---
title: About
summary: Rui Huang is a platform engineer in Copenhagen working on Kubernetes and AWS. Before that, Linux kernel drivers and embedded firmware.
---

I'm Rui, a platform engineer in Copenhagen.

At Nuuday I work on CPEmon, the platform YouSee uses to monitor and manage more than a million broadband devices. That means services on Kubernetes and AWS, a telemetry path built on Kafka and ClickHouse (I also contribute to the Rust-based Linux agents that collect the data), and the Prometheus, Grafana and Loki setup that tells us when something is off. Plus the on-call that comes with it.

I got here the long way round: nearly three years of Linux kernel drivers for Xiaomi phones in Beijing, then an MSc in Computer Science and Engineering at DTU, with a stint on Bluetooth LE firmware at Oticon along the way. From `segmentation fault` to `service not found`.

I hold the CKA and the AWS Certified Solutions Architect – Associate.

## What's on this site

I build side projects to try ideas end to end, then write up how they went: what I built, why it ended up that way, and what I'd change. Roughly in the order my thinking evolved:

- **[edge-ci-cd-demo](https://github.com/huangruidtu/edge-ci-cd-demo)**: CI/CD for a C++ app on an ARM board in a private LAN. Layered DevSecOps checks, versioned binaries in S3, delivery through a self-hosted runner, manual rollback. [Write-up](/posts/edge-ci-cd/).
- **[cpemon-mvp](https://github.com/huangruidtu/cpemon-mvp)**: a lab-scale version of a CPE monitoring platform on a self-managed Kubernetes cluster. Go services, MySQL-backed queues, Prometheus and Grafana, Elasticsearch and Kibana, Velero for backup and restore.
- **[aws-cpemon-lite](https://github.com/huangruidtu/aws-cpemon-lite)**: the same problem built only from AWS managed services: API Gateway, Lambda, DynamoDB, S3, CloudWatch alarms and SNS, with a small cost guardrail.
- **[CPEmon cloud platform upgrade](https://github.com/huangruidtu/cpemon-mvp/tree/codex/cpemon-cloud-platform-upgrade)**: the MVP moved to EKS with Terraform, Helm, Kafka, Argo CD, External Secrets, Kyverno, OpenCost and Crossplane.
- **[Muztagh Developer Platform](https://github.com/huangruidtu/Muztagh-Developer-Platform)**: the platform pieces pulled out of that upgrade into a central internal developer platform. Terraform owns the foundation, Crossplane exposes `Workspace`, `Application` and `DataStore` contracts, and CPEmon is the first tenant.
- **[Multi-source data engineering lab](https://github.com/huangruidtu/multi-source-data-engineering-pipeline-lab)**: batch and CDC pipelines with Airflow, Spark, Debezium, Kafka, Flink, Iceberg, Snowflake and dbt, plus an AWS-native version.

The later repositories state plainly what was actually run and what was only designed or validated offline.

## Outside work

Basketball, hiking, football, and Liverpool FC.

## The duck

That's Psyduck: a bit slow, always slightly confused, gets there in the end. Felt right.

## Elsewhere

[GitHub](https://github.com/huangruidtu) · [LinkedIn](https://www.linkedin.com/in/rui-huang-314a50168/) · [RSS](/atom.xml)
