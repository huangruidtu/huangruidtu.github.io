---
title: About
summary: Rui Huang — from C programmer to SRE. Projects on delivery pipelines, Kubernetes, cloud platforms and data engineering.
lang: en
---

I'm Rui. I started out writing C and moved into SRE work: from `segmentation fault` to `service not found`. `--progress?`

I learn by building things end to end and then writing down what happened: what the system does, why it ended up that way, and what I'd change. Most of what I build is about delivery pipelines, Kubernetes and cloud platforms, and data engineering.

## Projects

Roughly in the order my thinking evolved:

- **[edge-ci-cd-demo](https://github.com/huangruidtu/edge-ci-cd-demo)**: CI/CD for a C++ app on an ARM edge device in a private LAN. Layered DevSecOps checks, versioned binaries in S3, delivery through a self-hosted runner, manual rollback. [Write-up](/posts/edge-ci-cd/).
- **[cpemon-mvp](https://github.com/huangruidtu/cpemon-mvp)**: monitoring home-router (CPE) heartbeats on a self-managed Kubernetes cluster. Go services, MySQL-backed queues, Prometheus/Grafana, Elasticsearch/Kibana, Velero for backup and restore.
- **[aws-cpemon-lite](https://github.com/huangruidtu/aws-cpemon-lite)**: the same problem built only from AWS managed services. API Gateway, Lambda, DynamoDB, S3, CloudWatch alarms and SNS, with a small cost guardrail.
- **[cpemon cloud platform upgrade](https://github.com/huangruidtu/cpemon-mvp/tree/codex/cpemon-cloud-platform-upgrade)**: taking the MVP to EKS with Terraform, Helm, Kafka, Argo CD, External Secrets, Kyverno, OpenCost and Crossplane.
- **[Muztagh Developer Platform](https://github.com/huangruidtu/Muztagh-Developer-Platform)**: the platform pieces pulled out of that upgrade into a central internal developer platform. Terraform owns the foundation, Crossplane exposes `Workspace` / `Application` / `DataStore` contracts, and CPEmon is the first tenant.
- **[multi-source data engineering lab](https://github.com/huangruidtu/multi-source-data-engineering-pipeline-lab)**: batch and CDC pipelines (Airflow, Spark, Debezium/Kafka, Flink, Iceberg, Snowflake/dbt), plus an AWS-native version.

The later repositories say plainly what was actually run and what was only designed or validated offline.

## The duck

That's Psyduck: a bit slow, always slightly confused, gets there in the end. Felt right.

## Elsewhere

[GitHub](https://github.com/huangruidtu) · [LinkedIn](https://www.linkedin.com/in/rui-huang-314a50168/) · [RSS](/atom.xml)
