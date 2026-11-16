---
title: The same telemetry platform on AWS managed services
date: 2026-11-16
summary: The CPE monitoring problem again, with the opposite constraint: nothing to run myself. The services were the easy part; deciding which signals deserve an alarm was not.
series: Project retrospectives
series_part: 3
---

> One post in a series of project retrospectives. Code: [huangruidtu/aws-cpemon-lite](https://github.com/huangruidtu/aws-cpemon-lite)

**TL;DR:** The monitoring problem from the previous post, rebuilt in four days with nothing to operate. API Gateway and Lambda take telemetry in; DynamoDB keeps recent state, S3 keeps the raw payloads, CloudWatch holds metrics, dashboards and alarms, and SNS sends the email. The services were the easy part. Deciding which signals deserve an alarm was the real work.

## Why build it again

After running every layer myself, the obvious next question was how much of it I'd still want to run if I didn't have to. So I took the same problem and set the opposite constraint: managed services only. No servers, no cluster, as little to operate as possible.

I also changed the order of work. The first two days were documents (architecture, telemetry flow, security baseline, design decisions, cost) and the code came after.

## The shape of it

```text
device --HTTPS--> API Gateway --> ingestion Lambda
                                  |-- validate, derive health_state
                                  |-- CloudWatch metrics     (hot)
                                  |-- DynamoDB record        (warm)
                                  '-- S3 raw payload         (cold)

EventBridge (10 min) --> heartbeat-check Lambda
                         scan DynamoDB -> FleetMissingHeartbeatCount

CloudWatch alarms --> SNS --> email
```

One request, three destinations, each with a different job:

- **Hot:** the Lambda validates the payload, derives a simple health state and publishes metrics. This is where alarms come from.
- **Warm:** DynamoDB keeps structured records for the latest state and recent history of a device.
- **Cold:** S3 keeps the raw payload under `raw/<device_id>/<last_seen>.json` for traceability, debugging and replay.

The data overlaps; the jobs don't.

## Is the internet working?

The previous version tracked heartbeats: is the device alive? This time I asked what a broadband operator actually cares about, which is whether the household has internet. A router can be powered on and still leave a home offline.

So `wan_status` became the primary signal and `last_seen` a supporting one. CPU, memory and temperature are supporting health indicators. The Lambda folds them into a `health_state`: above 85 °C is `critical`; WAN down or CPU or memory above 90% is `warning`; anything else is `ok`. Short CPU and memory spikes are normal, so none of the alarms hang off them.

## Alert on the fleet, not the device

The first alarm I built was per device: `WanDown` with a `device_id` dimension. Its only purpose was to prove the path from metric to alarm to SNS to an email in my inbox. Once that worked, I deleted it.

The alarms that stayed answer the question someone on call actually needs answered: are many households affected right now?

- `FleetWanDownCount` is published without a device dimension, so every WAN-down report lands in one shared time series.
- `FleetMissingHeartbeatCount` comes from a scheduled Lambda that scans the telemetry table, finds each device's latest `last_seen`, and counts the devices that have gone quiet for more than ten minutes.

Single devices are for investigation, not alerting. For that, the CloudWatch dashboard has a `deviceId` variable. In the previous project I built a small admin UI for the same purpose; here a dashboard variable did the job.

The missing-heartbeat alarm exists but has its actions switched off, because the simulator doesn't run around the clock, and a noisy alarm teaches you to ignore it.

## The small things

None of these took long, and all of them are easy to skip:

- **Least privilege.** The ingestion function can put items into one table, write objects under one S3 prefix, and publish metrics. Nothing else.
- **Storage defaults.** S3 encryption and Block Public Access, DynamoDB encryption at rest.
- **Audit.** CloudTrail's default event history, without a dedicated trail, which is enough at this size.
- **Cost.** Cost Explorer grouped by service, and a small AWS Budget as a guardrail. With no servers to watch, the bill is one of the few signals left that tells you something changed.

## What I gave up

Observability got thinner. CloudWatch is no match for Prometheus, Grafana and a log search I control, and there's no buffering: every request is processed synchronously, with SQS left as the obvious next step.

Some shortcuts are fine for a lab and wrong for a fleet. The heartbeat check scans the whole table every ten minutes. Device authentication is still on the list. And `FleetWanDownCount` counts reports, not distinct devices, so one chatty router could look like an outage.

## What changed in my thinking

Running everything myself taught me what each layer costs to operate. Running nothing taught me something else: once the machinery is gone, the work that's left is deciding what to measure, and what is worth waking someone up for.

## Next

Next is [the CPEmon cloud platform upgrade](/posts/cpemon-eks-upgrade/): the original MVP taken to EKS with Terraform, GitOps and Kafka, and what happens when one repository tries to hold all of it.
