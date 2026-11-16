---
title: About
summary: Rui Huang is a platform and data engineer in Copenhagen. Platforms, pipelines, and the alerts for when either breaks.
---

I'm Rui, a platform and data engineer in Copenhagen.

Most of what I do sits between “something happened” and “someone can act on it”. Devices, services and databases emit a constant stream of events. My job is getting that stream somewhere useful, keeping it correct on the way, and keeping the platform underneath it boring. Device telemetry, business analytics, CI/CD: it's the same shape of problem every time, just with different nouns.

I got here the long way round: Linux kernel drivers for smartphones, then an MSc in Computer Science and Engineering at DTU (with some Bluetooth firmware for hearing-aid accessories on the side), then infrastructure. From `segmentation fault` to `service not found`, with the occasional `consumer lag` these days.

Officially certified, too: CKA and AWS Certified Solutions Architect – Associate.

## What I reach for

- **Keeping platforms up:** Kubernetes, Terraform, Helm, Argo CD, and a lot of AWS
- **Moving data around:** Kafka, ClickHouse, Airflow, Spark, Flink, Debezium, dbt, Snowflake
- **Finding out why it broke:** Prometheus, Grafana, Loki, and the ELK stack
- **Writing the actual code:** Go, Python, Rust, C, and more Bash than I'd like to admit

## What's on this site

I build side projects to try ideas end to end, then write up how they went: what I built, why it ended up that way, and what I'd change. Roughly in the order my thinking evolved:

- **[edge-ci-cd-demo](https://github.com/huangruidtu/edge-ci-cd-demo)**: CI/CD for a C++ app on an ARM board in a private LAN. Layered DevSecOps checks, versioned binaries in S3, delivery through a self-hosted runner, manual rollback. [Write-up](/posts/edge-ci-cd/).
- **[cpemon-mvp](https://github.com/huangruidtu/cpemon-mvp)**: a telemetry platform for home routers (CPEs) on a Kubernetes cluster I ran myself. Go services, a MySQL-backed queue, Prometheus and Grafana, Elasticsearch and Kibana, Velero for backup and restore. [Write-up](/posts/cpemon-mvp/).
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
