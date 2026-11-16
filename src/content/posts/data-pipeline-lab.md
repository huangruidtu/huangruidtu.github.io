---
title: A multi-source data pipeline, hybrid and AWS-native
date: 2026-11-07
summary: Batch and CDC pipelines for commerce and operations data, built first on open-source engines with a SaaS warehouse, then again on AWS. Most of the work went into one question: when two records disagree, which one is true?
series: Project retrospectives
series_part: 6
---

> One post in a series of project retrospectives. Code: [huangruidtu/multi-source-data-engineering-pipeline-lab](https://github.com/huangruidtu/multi-source-data-engineering-pipeline-lab)

**TL;DR:** A data engineering lab with two ingestion paths. Batch: PostgreSQL, a REST API and CSV/JSON files through Airflow into Bronze Parquet, then Spark into Silver Iceberg tables. CDC: the PostgreSQL WAL through Debezium and Kafka into Flink. Snowflake reads Silver and dbt builds Gold. Then the same contracts again on AWS: S3, Glue, Iceberg and Redshift Serverless. Most of the effort went into correctness rules, not tools.

## Why a data project

The telemetry and platform projects were about moving data and running the systems that move it. They kept touching the same question from the other side: once the data has arrived, what makes it correct? A duplicate webhook, a replayed batch, a message that arrives out of order. This project is about that question.

## The first version: hybrid

```text
batch   PostgreSQL / REST / CSV / JSON
          --Airflow--> Bronze (Parquet)
          --Spark----> Silver (Iceberg)

CDC     PostgreSQL WAL
          --Debezium--> Kafka
          --Flink-----> CDC Bronze archive + Silver (Iceberg)

Gold    Silver
          --Snowflake (external)--> dbt
          --> dimensions, facts, marts
```

Open-source engines for ingestion and processing, a SaaS warehouse for analytics. Each layer has a narrow job:

- **Bronze** keeps what arrived, unchanged, plus a quarantine for invalid records with the reason they were rejected.
- **Silver** keeps the current state that consumers can trust.
- **Gold** is dimensional models and marts, built by dbt.

Airflow schedules the batch functions but contains no transformation logic. The decision record puts it as "Airflow controls execution, not truth."

## One writer per table

The first rule: every Silver table has exactly one writer. Spark owns the reference tables (exchange rates, locations). Flink owns the commerce state from CDC (customers, products, orders, payments). dbt owns Gold and nothing else. If code tries to write a table it doesn't own, it fails early.

> A table has one writer because correctness is clearer than shared convenience.

It's the same idea as the platform project, where ownership followed the reconciler. Here it follows the writer.

## Freshness is evidence

The most useful bug in the project was in the Spark `MERGE`. It updated a Silver row if the incoming extract was at least as new, *or* if the record hash differed. The second half sounds reasonable until you replay an old batch: the old record is different, so it wins, and newer state is silently overwritten.

The fix compares a version tuple instead: business time first, then source extraction time, then ingestion time, and the hash only as a final tie-breaker. Six tests pin it down, including one where an older version with a different hash must lose, and one where an exact replay must change nothing.

> Hash proves difference, never freshness.

The CDC path has its own version of the rule. Kafka offsets say where a message sits in a partition, not when the change happened in the database. So Flink orders changes by PostgreSQL LSN first and transaction order second. If two events claim the same position and the code can't prove one is an exact replay of the other, it reports a conflict instead of letting the last arrival win:

> When evidence is insufficient, correctness wins over availability.

Debezium is configured explicitly for this: `pgoutput`, a named publication and replication slot, an initial snapshot, delete tombstones, and transaction metadata.

## The second version: AWS-native

The AWS version keeps the same source contracts, layers and ownership rules, and swaps the runtime:

```text
PostgreSQL / REST / CSV / JSON
  --> S3 Bronze: data.parquet, then _COMMITTED.json
  --> Glue Spark --> Iceberg + Glue Data Catalog (Silver)
  --> Redshift Serverless (opt-in) --> dbt (Gold)
```

A few details worth pointing out:

- **Manifest last.** A batch writes its Parquet first and its commit manifest last. Readers only consume batches with a verified manifest, so a half-written batch is invisible.
- **Ownership in code.** The Glue job owns only the two reference tables and rejects commerce snapshots, which stay with the CDC path.
- **No partial publishes.** Ingestion buffers a whole source operation, so nothing is published after a REST traversal fails halfway. The limits are explicit (record counts, page counts, object size) instead of hoped for.
- **Guardrails in Terraform.** The configuration only works against one explicitly allowed account ID, enforced twice. GitHub OIDC trusts a single environment-scoped subject. S3 uses a customer-managed KMS key, blocks public access, requires TLS and keeps versions.

## How far it was validated

The first version is honest about its limits: offline unit tests cover ingestion, Spark contracts, the Debezium configuration, the Flink model, the warehouse contracts and the validation framework, but the repository does not claim that Airflow, Spark, Flink, Kafka, S3, Snowflake and dbt ever ran together. Its validation runner is built so it cannot report success when a native command failed.

The AWS version went further locally. A real Spark 3.5 and Iceberg 1.10 `MERGE` runs on Linux in CI, and a source-to-Gold demo runs end to end on a local machine. No AWS resources were deployed.

## What changed in my thinking

The platform projects taught me that ownership should follow whatever reconciles a resource. This one taught the same lesson again with rows instead of resources. And the habit from the first post, saying clearly what was proven and what wasn't, turned out to apply to data as much as to pipelines: a record needs evidence before it's allowed to replace another.

This is the last post in the series for now.
