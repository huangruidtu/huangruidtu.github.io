---
title: Pulling the platform out of the application
date: 2026-10-20
summary: After the EKS upgrade outgrew its repository, I split the platform into its own: decide who owns what first, then pick the tools. The interface a team sees is three small resources.
series: Project retrospectives
series_part: 5
---

> One post in a series of project retrospectives. Code: [huangruidtu/Muztagh-Developer-Platform](https://github.com/huangruidtu/Muztagh-Developer-Platform)

**TL;DR:** A small internal developer platform, split out of the CPEmon upgrade. Terraform owns the AWS and EKS foundation, Argo CD reconciles from Git, Crossplane exposes three contracts (`Workspace`, `Application`, `DataStore`), and Kyverno enforces a few guardrails. CPEmon is the first tenant: onboarding is three short YAML files in a pull request. It is validated offline in CI, not run on a live AWS account.

## Why a separate repository

The previous project ended with a question it couldn't answer: who owns what? Kafka, Crossplane, policies and the application all lived in one repository, and every boundary was a matter of opinion.

So this time I started from ownership and picked the tools afterwards. The work went in as nine pull requests, each one a single step: foundation, Terraform, GitOps, platform APIs, tenancy, the first consumer, observability, CI, documentation. Eleven commits in total, after 159 in the previous branch. That felt like a different kind of project.

## Who owns what

One sentence from the ownership document did most of the work:

> Ownership follows the reconciler and resource boundary, not repository write access.

```text
platform team --> Terraform --> network, EKS, baseline IAM

domain team --> YAML in a PR --> CI --> Argo CD
                                          |
                                          v
                            Workspace / Application / DataStore
                                          |
                                          v
                              Crossplane Compositions
                              --> namespaces, workloads, S3
```

Terraform owns the shared foundation. Crossplane owns only the developer-facing resources its Compositions create. The two never manage the same resource. Argo CD submits what was approved in Git, but doesn't replace either of them.

The same idea applies when something breaks. An invalid image or an unhealthy application is normally the domain team's problem; a broken Composition or a provider failure is the platform's. In the document's words, "diagnosis can cross that boundary without transferring permanent ownership."

## The interface a team sees

This is everything CPEmon declares to get a workspace, a running service and a bucket (`apiVersion` and annotations trimmed):

```yaml
kind: Workspace
metadata:
  name: cpemon-dev
spec:
  owner: cpemon
  environment: dev
  costCenter: connectivity
  developerGroup: muztagh:cpemon-developers
---
kind: Application
metadata:
  name: cpemon-api
  namespace: cpemon-dev
spec:
  image: registry.example.com/cpemon/cpemon-api
  tag: v0.1.0
  replicas: 2
  port: 8080
---
kind: DataStore
metadata:
  name: cpemon-backup
  namespace: cpemon-dev
spec:
  region: eu-west-1
  deletionPolicy: Orphan
```

Behind those few fields, a `Workspace` becomes a namespace with a resource quota, a bounded role binding and network-policy intent. An `Application` becomes a workload with secure defaults behind a ClusterIP Service. A `DataStore` becomes an S3 bucket with public access blocked and encryption on. Three Kyverno policies sit underneath: the restricted Pod Security profile, ClusterIP-only Services, and required ownership labels.

## The first consumer is not the design

The tempting move is to shape the platform around the first application that uses it. One decision record exists to prevent exactly that:

> The contract test is whether a second unrelated domain could use the APIs without inheriting CPEmon concepts.

So Kafka, ClickHouse and CPEmon-specific labels are not in the contracts. They stay visibly missing instead of being bent into a shared API for one tenant. That was also my answer to the previous post's question: for now, Kafka stays outside the platform's contracts, as an open gap rather than a quiet special case.

## Git is the front door

There's no portal. Teams submit YAML through a pull request, CI validates it, and Argo CD applies it after merge. The reasoning in the decision record: a portal is only useful once the API, authorization and ownership model underneath are stable. The API is the durable part; a portal or CLI can generate the same declarations later.

## How far it was validated

Every pull request runs Terraform format, validate and lint for both environments, Kubeconform, Kyverno policy tests, `promtool` on the alert rules, actionlint, yamllint, Trivy and Gitleaks, all behind one required check. One fixture is deliberately invalid and must fail validation, so the checks are known to catch something. The full set ran green on a real pull request.

What it doesn't prove is just as explicit: no `terraform apply`, no EKS cluster, no live Argo CD or Crossplane reconciliation, no bucket created from a claim. The repository calls itself offline-validated and stops there.

## What changed in my thinking

In the upgrade I added tools and then discovered the ownership problem. Here I settled ownership first, and the tools became easier to choose and easier to leave out. The interface also got smaller as it got clearer. Four fields describe an application, and the most useful part of the design is what it refuses to include.

## Next

Next is a different domain: [a data engineering lab](/posts/data-pipeline-lab/) with batch and CDC pipelines, built first as a hybrid stack and then again on AWS.
