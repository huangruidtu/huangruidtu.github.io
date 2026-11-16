---
title: An edge CI/CD retrospective
date: 2026-11-16
summary: My first attempt at treating delivery as one whole problem: layered DevSecOps checks, a self-hosted runner inside a private LAN, versioned artifacts in S3, and a manual rollback.
series: Project retrospectives
series_part: 1
---

> One post in a series of project retrospectives. Code: [huangruidtu/edge-ci-cd-demo](https://github.com/huangruidtu/edge-ci-cd-demo)

**TL;DR:** A GitHub Actions pipeline for a C++ app on an ARM board behind a private LAN. Layered checks (cppcheck, Trivy) run on every pull request and fail on high-severity findings. Release tags build a versioned binary on a self-hosted runner, publish it to S3 and deploy it over SSH. Rollback is a manual workflow that redeploys any earlier version from S3.

I started here because this was the first time I treated delivery as a whole problem, rather than as a workflow file that turns green.

## The setup

The application is deliberately trivial: `main.cpp` prints `CI/CD Demo Running!`. The less the app does, the more attention goes to the path it takes to production.

The constraints come from the target: an old ARMv7 board running **Ubuntu 14.04**. It runs a native binary, not containers, and it sits on a private LAN that GitHub's cloud runners can't reach. Almost every decision below follows from those two facts.

I built it in three stages, each answering a concrete problem, instead of writing one big workflow up front.

## Day 1: make CI able to fail

Day one was routine: a C++ skeleton, CMake, a multi-stage Dockerfile, GitHub Actions, a `dev` / `main` / PR branching model, and images pushed to ECR.

One small step is worth calling out. The history has these two commits:

```text
Test: break CI intentionally
Fix: restore CI
```

`main.cpp` still contains a block, switched off with `#if 1`, that dereferences a null pointer:

```cpp
int main() {
    int *p = nullptr;
    *p = 10;   // null pointer dereference
    return 0;
}
```

I flipped the switch to check that cppcheck actually fails the build. A CI pipeline that has never gone red tells you nothing. Prove it can fail before you trust it when it passes.

The other early decision was tagging. Images started out tagged with the commit SHA; on day two, releases moved to semantic versions such as `v1.2.4`. The SHA gives traceability; the version gives humans, and later the rollback, something to point at. `latest` was never used.

## Day 2: layer the security checks

Day two turned CI into a layered DevSecOps pipeline:

| Trigger | Goal | What runs |
|---|---|---|
| `dev` branch | Fast feedback | cppcheck (SAST) only |
| PR / `main` | Quality and security gate | cppcheck, Docker build, Trivy FS, Trivy image |
| Tag `vX.Y.Z` | Release and delivery | Build a versioned artifact, publish, deploy |

Both Trivy scans run with `severity: HIGH,CRITICAL` and `exit-code: 1`. They block; they don't just report. A scan that only reports quickly turns into noise nobody reads.

Why not run everything on every branch? On `dev` it would slow down day-to-day work until people start working around it. Why not only at release? Because problems surface too late. Layering means the checks get stricter the closer code gets to a release.

The same day I added Dependabot. Scanners find risk; Dependabot drives the fix. The policy is simple: merge patches, merge minors and let CI catch problems, test majors by hand. Docker layer caching keeps PR builds from starting from scratch.

## Day 3: the hard part of CD isn't in the YAML

Day three was about getting the binary onto the board. I cut nine tags that day (`v1.2.1` to `v1.3.1`), nearly every one a fix for the previous attempt. Four turning points stand out.

**1. Cross-compile first.** Install `gcc-arm-linux-gnueabihf` on a GitHub-hosted runner, build an ARMv7 binary, upload it to S3 by version.

**2. Deploy from the build job, then find out it can't reach the board.** The first CD step ran `scp` and `ssh` straight from the build job. But the board is on a private LAN, and GitHub's cloud runners can't see it. Deployment moved into its own job on a **self-hosted runner** inside the LAN.

**3. New toolchain, old OS.** The binary arrived, but binaries from a modern toolchain hit runtime compatibility problems on an OS as old as Ubuntu 14.04. I moved the ARM build to the self-hosted runner as well, and tried lowering the CMake minimum version from 3.10 to 2.8.12. The workflow step is literally named *legacy compatibility attempt*.

**4. Switch off ECR for now.** The board consumes a binary, not an image. On this path, pushing to ECR was just noise.

The final pipeline is really two paths:

```text
push / PR / tag --> GitHub-hosted runner
                    cppcheck -> Docker build -> Trivy FS -> Trivy image

tag --------------> self-hosted runner (inside the LAN)
                    build versioned binary -> upload to S3
                    -> download from S3 -> scp to board
                    -> stop.sh / start.sh
```

The S3 bucket in the middle matters. Every release lands at:

```text
s3://edge-cicd-demo-artifacts/edge-demo/releases/<version>/edge-app
```

The build only writes there and the deploy only reads from there. Neither side needs to know how the other works, and S3 becomes the source of truth for which versions exist. That is what makes rollback cheap.

## Rollback: a separate, manual workflow

Rollback isn't part of the main pipeline. It's its own `workflow_dispatch` that takes a version:

```yaml
on:
  workflow_dispatch:
    inputs:
      release_version:
        description: 'Release version to roll back to (e.g. v1.2.4)'
        required: true
```

It does exactly what a normal deploy does: fetch that version's binary from S3, copy it to the board, and call the board's existing `stop.sh` / `start.sh`. Every release is still in S3, so a rollback is just a deploy of an older version. No extra machinery.

Why manual? Rolling back is a sensitive operation. I want it to be explicit: a person decides when, and to which version.

## An idea I kept coming back to

The project never fully solved the board's runtime compatibility. In the docs I recorded it as a separate, platform-specific issue instead of calling the pipeline a failure:

> CI/CD orchestration success and target runtime compatibility are not the same problem.

At the time this felt a little like letting myself off the hook. I now think it's an important engineering habit: **be clear about what you proved and what you didn't.** The orchestration works. The artifact is built, published and delivered to the device. Whether a 2014-era OS can run it is a different question, and collapsing both into "done" or "not done" helps no one.

The habit gets more explicit in later projects. In the platform and data projects I wrote a separate document listing what was actually run and what was only designed or validated offline.

## If I did it again

From the project's own list of next steps:

- Image signing (Cosign) and an SBOM, so "what is this artifact and where did it come from" can be verified
- SARIF upload, so scan results land in GitHub Security instead of build logs
- Progressive delivery instead of an in-place swap

And, looking back:

- AWS access uses long-lived keys stored in GitHub Secrets. It should use short-lived credentials through GitHub OIDC and STS.
- Deployment ends as soon as `start.sh` runs. There's no post-deploy health check, and without one there's no safe automatic rollback.

## Next

Next is [the first version of CPEmon](/posts/cpemon-mvp/): a lab-scale monitoring platform for home routers (CPEs) on a Kubernetes cluster I ran myself. It was my first real look at what "you operate everything" means.
