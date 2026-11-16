---
title: Migrating a lab Kubernetes platform to EKS
date: 2026-06-28
summary: The MVP's shortcuts, reversed one at a time: Terraform, Helm and Argo CD, Kafka instead of a database queue, externalized secrets, policies and cost visibility. Then it outgrew its repository.
series: Project retrospectives
series_part: 4
---

> One post in a series of project retrospectives. Code: [cpemon-mvp, `cpemon-cloud-platform-upgrade` branch](https://github.com/huangruidtu/cpemon-mvp/tree/codex/cpemon-cloud-platform-upgrade)

**TL;DR:** The self-managed MVP from two posts ago, moved toward a cloud platform: Terraform for an EKS foundation, Helm and Argo CD for delivery, Kafka in place of the database queue, secrets from AWS Secrets Manager, Kyverno policies, OpenCost, and later Crossplane and K8sGPT. It is validated offline, not run against a live cluster. Along the way it became too much for one repository, which is what the next post is about.

## Why

The MVP was deliberately plain: raw YAML, `kubectl apply`, a queue in MySQL. That was right for a first version, where the goal was to see every layer.

But most platform work isn't building something new on a lab cluster. It's moving an existing service onto managed Kubernetes, infrastructure as code and GitOps without breaking it. That's what I wanted to practice. The decision record that started the work says it plainly:

> The purpose of this upgrade is not to claim that CPEmon needs a full production cloud platform today. The purpose is to practice and document the migration thinking: what changes first, what stays stable, which risks appear during migration…

## Reversing the shortcuts

The MVP's decision records each ended with "at real scale, I would...". This branch is where several of those got cashed in.

| In the MVP | After the upgrade |
|---|---|
| kubeadm lab cluster | EKS, provisioned with Terraform |
| Plain YAML and `kubectl apply` | A Helm chart, reconciled from Git by Argo CD |
| A queue table in MySQL | Kafka between ingest and the writer |
| Secrets in manifests | External Secrets Operator and AWS Secrets Manager |
| Manual checks | PR gates for manifests, policies, images and Terraform plans |

Not everything moved. MySQL stayed inside the cluster for this step, with RDS written down as a later hardening decision. The database the services depended on stayed put while everything around it changed, which kept fewer things moving at once.

## Kafka, and a writer that does its job

Kafka went in the same way: first as a platform component with a namespace, a bootstrap address and a topic plan, and only then wired into the services.

`acs-ingest` now publishes versioned events (`cpemon.device.heartbeat.v1`, `cpemon.wan.status.v1`) keyed by device ID, so events for one device stay in order within a partition. The producer retries and exports metrics on failures.

On the other side, `cpemon-writer` now does real work. It consumes both topics, writes state to MySQL with idempotent upserts, and commits a Kafka offset only after the write succeeded. It also exports the last consumed and committed offset and the age of the last message, per partition, so Prometheus shows whether it is keeping up. That closes the gap the MVP left open, where the writer only claimed and acknowledged events.

## Where I held back

Some of the better decisions were about what not to do yet:

- **HPA before KEDA.** Scale `cpemon-api` on CPU first; event-driven autoscaling can wait until there is a reason.
- **K8sGPT as a detective, not a fixer.** Read-only access, no automatic remediation. Its findings are a hint, checked against `kubectl`, Argo CD, Prometheus and the runbooks.
- **A line between Terraform and Crossplane.** Terraform owns the foundation: VPC and subnets, the EKS cluster, baseline IAM. Crossplane only owns selected application-level resources that developers can request, and the two are not supposed to manage the same resource.

## Too much for one repository

Some numbers: 159 commits in ten days, 17 new decision records, 118 verification scripts, around 60 knowledge notes. Application code, cluster add-ons, Terraform, policies and a self-service API all lived in the same repository.

Each piece made sense. Together they blurred a question that matters more than any single tool: who owns what? Is Kafka part of CPEmon, or part of the platform CPEmon runs on? Is the Crossplane API for CPEmon, or for anyone? The roadmap had even said that step 2 should stay small, to avoid turning the upgrade into an internal developer platform. That is more or less what happened anyway.

## How far it was validated

The repository is explicit about this. Helm renders, Go tests, Kyverno fixture tests and Terraform validation run offline. Argo CD syncing, Crossplane provisioning real AWS resources and Kafka broker behavior need a live cluster and credentials, and the evidence matrix doesn't claim them.

## What changed in my thinking

Installing components turned out to be the easy part of a platform. Drawing ownership lines is the hard part. If I could keep only one decision record from this branch, it would be the one about where Terraform stops and Crossplane starts. That line became the starting point of the next project.

## Next

Next is [Muztagh](/posts/muztagh-platform/): taking the platform out of the application, and running it as a separate product for the teams that build on it.
