---
title: A telemetry platform on a cluster I ran myself
date: 2026-11-16
summary: A CPE monitoring platform built end to end on a self-managed Kubernetes lab, with every shortcut written down and failures rehearsed on purpose.
series: Project retrospectives
series_part: 2
---

> One post in a series of project retrospectives. Code: [huangruidtu/cpemon-mvp](https://github.com/huangruidtu/cpemon-mvp)

**TL;DR:** A lab-scale monitoring platform for home routers (CPEs), built end to end on a two-node kubeadm cluster. Simulated devices and a TR-069 server (GenieACS) feed three Go services; MySQL holds the state and doubles as a queue; Prometheus, Grafana, Elasticsearch and Kibana watch it; Velero backs it up. Six decision records explain every shortcut, and the demos break things on purpose and bring them back.

## Why build it

A telemetry platform looks simple from the outside: devices send data, a dashboard shows it. Everything interesting happens in between, and on a large system you usually see only a slice of it.

I wanted the whole loop in my hands, small enough to hold in my head: from a heartbeat leaving a device, through ingress, services, a queue and a database, to a dashboard, a log search, a backup, and a runbook for when it goes wrong. Almost nothing was managed for me. Apart from a container registry and an S3 bucket for backups, everything ran on machines I set up. If something broke, it was mine to find.

The rule I set for the documentation said the same thing from the reader's side: someone with basic Kubernetes knowledge should be able to go from zero to "I can deploy and run this" using only the README, and follow the data the whole way.

## The shape of it

```text
outside the cluster (vm3)      Kubernetes: 1 control plane + 1 worker
-------------------------      --------------------------------------
CPE simulators --heartbeat-->  cpemon-api     --> cpe_status, history
GenieACS ------webhook------>  acs-ingest     --> ingest_events (queue)
                               cpemon-writer  <-- polls the queue

Prometheus + Grafana     metrics from every service
Filebeat + ES + Kibana   logs
Velero + MinIO/S3        namespace backups, MySQL dumps
```

Three Go services do the work. `cpemon-api` takes heartbeats and serves the read APIs and a small admin UI. `acs-ingest` receives webhooks from the ACS. `cpemon-writer` drains the queue. Everything enters through ingress-nginx, and MetalLB gives the bare-metal cluster a real `LoadBalancer` IP for it.

## The world doesn't start at Kubernetes

The first real decision was where *not* to put things. GenieACS and the device simulators run on a separate VM, outside the cluster, and talk to it only through ingress, the way an existing system would.

Putting everything in the cluster would have been tidier. But in telecom, the ACS and the systems around it usually already exist, and a new monitoring layer has to plug into them rather than replace them. The decision record puts it in one line:

> I didn't pretend the world starts at Kubernetes.

## Six shortcuts, written down

The lab had two small nodes and one extra VM. That forced shortcuts everywhere, so I wrote each one down as an architecture decision record (ADR): what I chose, what I gave up, and what I'd do at real scale.

| Decision | What I gave up | At real scale |
|---|---|---|
| 1 control plane + 1 worker, 2 replicas per critical service | Surviving a control-plane failure | Multiple control-plane nodes, workers across zones |
| MySQL as the only primary store | Separate operational and analytical stores | Specialized stores per workload |
| A queue in MySQL instead of Kafka | Partitions, consumer groups, replay | Kafka between ingest and processing |
| Single-node Elasticsearch | Log availability | A multi-node cluster with lifecycle policies |
| Plain YAML instead of Helm | DRY manifests, multiple environments | Helm or Kustomize, plus GitOps |
| ACS and devices on an external VM | A one-command bring-up | Keep it: real networks look like this |

Every record ends with how the decision would evolve. That turned out to matter: in the later CPEmon upgrade, Kafka replaces the database queue and Helm replaces the plain YAML.

## A queue in a database

The most interesting shortcut is the queue. Kafka would have been the natural choice, but on a two-node lab it would have doubled the moving parts for demo-level traffic. So ACS events go into a MySQL table instead:

- **Idempotent enqueue.** A unique key on `(sn, event_ts)` plus `ON DUPLICATE KEY UPDATE` means a webhook delivered twice is stored once.
- **Claiming work.** The writer claims an event with a conditional update, `status = 'processing' WHERE id = ? AND status = 'queued'`. If no row changed, another writer got there first.
- **Retries and dead letters.** Each row has `attempts`, `next_at`, and a `dead` state, with exponential backoff from 5 seconds up to 5 minutes and five attempts before giving up.

Webhooks are signed with HMAC-SHA256 and compared in constant time. Every failure path increments a labeled Prometheus counter (`invalid_json`, `missing_sn`, `invalid_signature`), so the dashboard shows *why* requests fail, not just that they do.

Not all of it was finished. The retry and dead-letter path exists in the schema and code but isn't wired into the writer yet, and heartbeats skip the queue entirely, so the backlog demo (which sends heartbeats) never actually fills it. Signatures are also only checked when a webhook carries the header.

## Break it on purpose

The part I'm happiest with is that failure is part of the demo, not something I hope doesn't happen during it.

- **Drain a node.** `cpemon-api` and `acs-ingest` run two replicas, spread across both nodes with affinity, tolerations and a PodDisruptionBudget. Draining the worker while a loop polls `/healthz` shows the API keeps answering.
- **Delete the API.** A Velero script backs up the namespace, deletes the `cpemon-api` Deployment, Service and Ingress, restores them, and runs the smoke test again.
- **Write the runbooks.** Three incident runbooks cover a queue backlog, Elasticsearch running out of disk, and a MySQL connection spike, each with impact, likely causes, a diagnostics checklist and immediate actions.

Security got the same layered treatment: the admin UI sits behind Basic Auth *and* an ingress IP allowlist, and Calico network policies default-deny egress in the namespace, so only the core services can reach MySQL, Prometheus and Elasticsearch.

The admin UI ties it together for an operator: search a device by serial number, see its current state and history, then jump to its metrics in Grafana and its logs in Kibana. A device ID to the evidence in a few clicks.

## What it taught me

Running every layer myself was the fastest way to learn what each layer costs. Elasticsearch needs disk and attention. A database queue works until it doesn't. A single control plane is a single point of failure whatever the replica count says.

It also made the next question obvious: how much of this would I still want to run myself if I didn't have to?

## Next

Next is [the same problem with the opposite constraint](/posts/aws-cpemon-lite/): no servers at all, only AWS managed services.
