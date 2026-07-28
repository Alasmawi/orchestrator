# orchestrator

Deploys the `crud-master` microservices onto a 2-node K3s cluster (`master` + `agent`, provisioned by
Vagrant), managed end-to-end by [`orchestrator.sh`](orchestrator.sh).

## Architecture

```
                     ┌─────────────── K3s cluster ───────────────┐
                     │                                            │
  kubectl  ───────►  │  master node                agent node    │
  (from host,        │  (control plane)             (workloads    │
   via .kube/config) │                                schedule    │
                     │                                 here too)  │
                     └────────────────────────────────────────────┘

Namespace: crud-master
┌──────────────────────────────────────────────────────────────────┐
│  api-gateway-app   Deployment  (min 1 / max 3, HPA cpu 60%)       │
│    Service: NodePort 30000 → 3000   (only externally reachable)  │
│         │ HTTP              │ publish (AMQP)                     │
│         ▼                   ▼                                    │
│  inventory-app      rabbit-queue         billing-app             │
│  Deployment          Deployment          StatefulSet             │
│  (min1/max3,         (1 replica)         (1 replica, consumes    │
│   HPA cpu 60%)                            billing_queue)         │
│         │                                       │                │
│         ▼                                       ▼                │
│  inventory-db                            billing-db              │
│  StatefulSet + PVC (1Gi)                 StatefulSet + PVC (1Gi) │
└──────────────────────────────────────────────────────────────────┘
```

- **inventory-app**, **api-gateway-app**: `Deployment` + `HorizontalPodAutoscaler`
  (min 1, max 3, target 60% CPU).
- **billing-app**: `StatefulSet` (per spec) — same consumer logic as crud-master/play-with-containers,
  plus the small `/`-on-8080 health endpoint used for its readiness probe.
- **inventory-db**, **billing-db**: `StatefulSet` + `volumeClaimTemplates` (1Gi each), so a rescheduled
  pod reattaches to the same PVC instead of losing data.
- **rabbit-queue**: plain `Deployment` (not required to be a StatefulSet by the spec); uses the
  official `rabbitmq:3-management-alpine` image.
- Databases use the official `postgres:13-bullseye` image. App images (`inventory-app`, `billing-app`,
  `api-gateway-app`) are custom-built from [`Dockerfiles/`](Dockerfiles) — the same source as
  `play-with-containers` — and must be pushed to your own Docker Hub account before deploying.

## Secrets

All credentials (`INVENTORY_DB_*`, `BILLING_DB_*`, `RABBITMQ_*`) live only in a local `.env`
(gitignored — see [`.env.example`](.env.example)) and are turned into Kubernetes `Secret` objects at
deploy time by [`Scripts/apply-secrets.sh`](Scripts/apply-secrets.sh). No plaintext credential ever
appears in a committed manifest; every Deployment/StatefulSet references secrets via `secretKeyRef`.

## Building and pushing images

```bash
export DOCKERHUB_USERNAME=<your-dockerhub-username>
docker login

for app in inventory-app billing-app api-gateway-app; do
  docker build -t "$DOCKERHUB_USERNAME/$app:latest" "Dockerfiles/$app"
  docker push "$DOCKERHUB_USERNAME/$app:latest"
done
```

Set `DOCKERHUB_USERNAME` in `.env` too — `orchestrator.sh` substitutes it into the app manifests
(which reference the placeholder `__DOCKERHUB_USERNAME__`) before applying them.

## Running

```bash
cp .env.example .env   # fill in real values + DOCKERHUB_USERNAME

./orchestrator.sh create   # vagrant up (master + agent) + install K3s + deploy everything
./orchestrator.sh start    # resume a previously-created, halted cluster
./orchestrator.sh stop     # vagrant halt
./orchestrator.sh destroy  # vagrant destroy -f

export KUBECONFIG=$(pwd)/.kube/config
kubectl get nodes -A
```

`create` provisions both VMs, installs the K3s server on `master` and joins `agent` to it (join token
is exchanged via the Vagrant shared folder), writes a working `kubeconfig` to `.kube/config`, then
applies the namespace, secrets, databases, queue, and all three apps in order.

## Verified during development

Since actually booting the two Vagrant VMs needs VirtualBox (not installed in this environment — see
project-level notes), every manifest here was instead validated against a local **k3d** cluster
(K3s-in-Docker, same `master`+`agent` topology, same K3s version) built from the exact files in this
repo:

- All manifests applied cleanly: `Namespace`, 3 `Secret`s, 2 `StatefulSet`s with bound 1Gi PVCs, 1
  plain `Deployment` (RabbitMQ), 2 `Deployment`s with working `HorizontalPodAutoscaler`s.
- **Full request flow worked end to end** through the cluster: `POST/GET /api/movies` via the gateway
  correctly reached `inventory-app` → `inventory-db`; `POST /api/billing` correctly reached
  `rabbit-queue` → `billing-app` → `billing-db`.
- `kubectl top pods` / `kubectl get hpa` showed the HPAs reading real CPU metrics
  (`cpu: 1%/60%`), confirming the metrics pipeline the autoscaler depends on actually works, not just
  that the HPA object was accepted.
- PVCs (`inventory-db-data-inventory-db-0`, `billing-db-data-billing-db-0`) bound successfully with
  `local-path` storage class.

## Design notes

- App source under `Dockerfiles/*/` is the same code proven in `crud-master` and
  `play-with-containers` — no logic changes, only packaging.
- `rabbit-queue` and the two databases use official images rather than custom Debian builds (unlike
  `play-with-containers`, this project doesn't restrict base images to Alpine/Debian) — official
  images ship battle-tested entrypoints for graceful shutdown and signal handling, which matters more
  under a StatefulSet's pod lifecycle than it did under `docker-compose`.
- `api-gateway-app` is published via `NodePort` (30000→3000) rather than an `Ingress`, since the spec
  doesn't call for host-based routing here — keeps the manifest set minimal.
