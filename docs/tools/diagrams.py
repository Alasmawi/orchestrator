#!/usr/bin/env python3
"""Generate the README diagrams (flat SVG, no external assets).

    python3 docs/tools/diagrams.py      # writes docs/architecture.svg, docs/k8s-components.svg

Everything drawn here mirrors the manifests: kinds, ports, replica bounds,
Service types and storage. Change the manifests, then change this.
"""
import html
import os

INK, PANEL, PANEL2, BONE = "#0E0F12", "#15171C", "#1B1D23", "#EFE9DD"
CARMINE, ROSE, AMBER = "#B0122B", "#EA5F70", "#F2A93B"
SOFT, MUTED, DIM = "#A3A4AB", "#8D8F98", "#5C5E66"
HAIR = "rgba(239,233,221,.14)"
HAIR2 = "rgba(239,233,221,.28)"
MONO = "'JetBrains Mono','SFMono-Regular',Menlo,Consolas,monospace"
COND = "'Archivo Narrow','Arial Narrow','Roboto Condensed','Helvetica Neue',Arial,sans-serif"
BODY = "Archivo,'Helvetica Neue',Arial,sans-serif"

OUT = os.path.join(os.path.dirname(__file__), "..")
e = html.escape


def label(x, y, text, fill=MUTED, size=10.5, anchor="start", spacing=1.3):
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{fill}" '
            f'letter-spacing="{spacing}" text-anchor="{anchor}">{e(text)}</text>')


def title(x, y, text, size=20, fill=BONE, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-family="{COND}" font-weight="800" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}">{e(text.upper())}</text>')


def body(x, y, text, size=13, fill=SOFT):
    return f'<text x="{x}" y="{y}" font-family="{BODY}" font-size="{size}" fill="{fill}">{e(text)}</text>'


def frame(x, y, w, h, fill="none", stroke=HAIR, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x}.5" y="{y}.5" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}"{d}/>'


def card(x, y, w, h, bar):
    return frame(x, y, w, h, PANEL) + f'<rect x="{x}" y="{y}" width="4" height="{h + 1}" fill="{bar}"/>'


def chip(x, y, text, fill=SOFT, stroke=HAIR2):
    w = int(len(text) * 6.6 + 16)
    return (frame(x, y, w, 20, PANEL2, stroke) +
            f'<text x="{x + 8}" y="{y + 14}" font-family="{MONO}" font-size="11" fill="{fill}">{e(text)}</text>', w)


def chips(x, y, items, gap=6):
    out = []
    for item in items:
        text, fill = item if isinstance(item, tuple) else (item, SOFT)
        svg, w = chip(x, y, text, fill)
        out.append(svg)
        x += w + gap
    return "".join(out)


def wire(points, text=None, tx=None, ty=None, dash=False, anchor="middle"):
    d = " ".join(f"{'M' if i == 0 else 'L'}{px},{py}" for i, (px, py) in enumerate(points))
    dd = ' stroke-dasharray="4 4"' if dash else ""
    out = f'<path d="{d}" fill="none" stroke="{SOFT}" stroke-width="1.2"{dd} marker-end="url(#arrow)"/>'
    if text:
        out += label(tx, ty, text, MUTED, 10, anchor, 0.6)
    return out


def component(x, y, kind, name, detail, bar, w=170, h=74):
    return (card(x, y, w, h, bar) + label(x + 14, y + 19, kind, MUTED, 9.5, spacing=1.2) +
            title(x + 14, y + 44, name, 19) + label(x + 14, y + 62, detail, ROSE, 10.5, spacing=0.4))


def svg(w, h, content):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{SOFT}"/></marker></defs>'
            f'<rect width="{w}" height="{h}" fill="{INK}"/>{content}</svg>\n')


def architecture():
    W, H = 1200, 850
    s = []
    # header + legend
    s.append(label(30, 34, "ORCHESTRATOR · DEPLOYED ARCHITECTURE", ROSE, 11))
    s.append(title(30, 66, "Six components on a two-node K3s cluster", 30))
    lx = 716
    s.append(f'<rect x="{lx}" y="26" width="4" height="12" fill="{CARMINE}"/>' + label(lx + 12, 36, "STATEFULSET", SOFT, 10))
    s.append(f'<rect x="{lx + 110}" y="26" width="4" height="12" fill="{DIM}"/>' + label(lx + 122, 36, "DEPLOYMENT", SOFT, 10))
    s.append(f'<path d="M{lx + 222},32 h26" stroke="{SOFT}" marker-end="url(#arrow)"/>' + label(lx + 256, 36, "TRAFFIC", SOFT, 10))
    s.append(f'<path d="M{lx + 318},32 h26" stroke="{SOFT}" stroke-dasharray="4 4" marker-end="url(#arrow)"/>' +
             label(lx + 352, 36, "VOLUME · PULL", SOFT, 10))
    s.append(f'<line x1="30" y1="86" x2="{W - 30}" y2="86" stroke="{HAIR}"/>')

    # host column
    s.append(frame(30, 104, 200, 716) + label(44, 124, "HOST · MACOS", MUTED, 10))
    s.append(card(44, 140, 172, 70, DIM) + label(58, 160, "CLIENT", MUTED, 9.5) + title(58, 184, "curl · Postman", 18) +
             label(58, 200, "audit requests", ROSE, 10.5, spacing=0.4))
    s.append(card(44, 250, 172, 70, DIM) + label(58, 270, "CLI", MUTED, 9.5) + title(58, 294, "kubectl", 18) +
             label(58, 310, "~/.kube/config", ROSE, 10.5, spacing=0.4))
    s.append(card(44, 380, 172, 88, DIM) + label(58, 400, "IAC", MUTED, 9.5) + title(58, 424, "orchestrator.sh", 18) +
             label(58, 440, "vagrant · kubectl", ROSE, 10.5, spacing=0.4) + label(58, 456, "create start stop", MUTED, 10, spacing=0.4))
    s.append(card(44, 680, 172, 88, DIM) + label(58, 700, "REGISTRY", MUTED, 9.5) + title(58, 724, "Docker Hub", 18) +
             label(58, 740, "alasmawi/*:latest", ROSE, 10.5, spacing=0.4) + label(58, 756, "6 images", MUTED, 10, spacing=0.4))

    # cluster frame
    s.append(frame(256, 104, 914, 716) + label(270, 124, "K3S CLUSTER · VIRTUALBOX HOST-ONLY NETWORK 192.168.56.0/24", MUTED, 10))

    # nodes
    s.append(card(270, 138, 440, 124, CARMINE) + label(286, 158, "VM MASTER · 192.168.56.21 · K3S SERVER", BONE, 10.5))
    s.append(chips(286, 168, [("kube-apiserver :6443", BONE), "scheduler", "controller-manager"]))
    s.append(chips(286, 194, ["sqlite (kine)", "coredns", "metrics-server", ("traefik :80", BONE)]))
    s.append(chips(286, 220, [("servicelb :3000", BONE), ("nfs-server /srv/nfs/k3s", ROSE)]))
    s.append(label(286, 254, "+ node agents: kubelet · kube-proxy · containerd · flannel", MUTED, 10, spacing=0.3))
    s.append(card(726, 138, 430, 124, DIM) + label(742, 158, "VM AGENT · 192.168.56.22 · K3S AGENT", BONE, 10.5))
    s.append(chips(742, 168, ["kubelet", "kube-proxy", "containerd"]))
    s.append(chips(742, 194, ["flannel vxlan (host-only nic)", "nfs-client"]))
    s.append(label(742, 254, "joins with the token shared through /vagrant", MUTED, 10, spacing=0.3))

    # namespace
    s.append(frame(270, 282, 886, 410, "none", HAIR2, "2 4") +
             label(284, 302, "NAMESPACE CRUD-MASTER · PODS ARE SCHEDULED ON EITHER NODE", MUTED, 10))
    c1, c2, c3, c4 = 296, 526, 756, 970
    ya, yb = 344, 564
    s.append(component(c1, 454, "DEPLOYMENT + HPA", "api-gateway-app", ":3000 · 1-3 @ 60% cpu", DIM))
    s.append(component(c2, ya, "DEPLOYMENT + HPA", "inventory-app", ":8080 · 1-3 @ 60% cpu", DIM))
    s.append(component(c4, ya, "STATEFULSET", "inventory-db", ":5432 · postgres 15", CARMINE))
    s.append(component(c2, yb, "DEPLOYMENT", "rabbit-queue", ":5672 · billing_queue", DIM))
    s.append(component(c3, yb, "STATEFULSET", "billing-app", ":8080 · consumer", CARMINE))
    s.append(component(c4, yb, "STATEFULSET", "billing-db", ":5432 · postgres 15", CARMINE))
    s.append(label(c1, 424, "SERVICE LOADBALANCER :3000", BONE, 9.5, spacing=0.8))
    s.append(label(c1, 440, "NODEPORT :30000 · INGRESS /api", MUTED, 9.5, spacing=0.8))

    # traffic
    s.append(wire([(216, 175), (240, 175), (240, 491), (c1, 491)], "HTTP", 262, 484, anchor="start"))
    s.append(wire([(216, 285), (236, 285), (236, 200), (270, 200)], "HTTPS", 242, 226, anchor="start"))
    s.append(wire([(c1 + 170, 480), (498, 480), (498, ya + 37), (c2, ya + 37)], "HTTP", 492, ya + 60, anchor="end"))
    s.append(wire([(c1 + 170, 502), (498, 502), (498, yb + 37), (c2, yb + 37)], "AMQP", 492, yb + 20, anchor="end"))
    s.append(wire([(c2 + 170, ya + 37), (c4, ya + 37)], "SQL · inventory-db:5432", (c2 + 170 + c4) / 2, ya + 30))
    s.append(wire([(c2 + 170, yb + 37), (c3, yb + 37)], "consume", (c2 + 170 + c3) / 2, yb + 30))
    s.append(wire([(c3 + 170, yb + 37), (c4, yb + 37)], "SQL", (c3 + 170 + c4) / 2, yb + 30))
    s.append(label(c2, yb + 96, "messages wait here while billing-app is stopped", MUTED, 10, spacing=0.3))

    # storage + secrets
    s.append(card(756, 712, 400, 92, CARMINE) + label(772, 732, "STORAGE · NFS-STATIC · RECLAIM RETAIN", BONE, 10.5))
    s.append(chips(772, 742, [("inventory-db-pv 1Gi", BONE), ("billing-db-pv 1Gi", BONE)]))
    s.append(label(772, 790, "nfs 192.168.56.21:/srv/nfs/k3s — mountable from both nodes", MUTED, 10, spacing=0.2))
    s.append(wire([(c4 + 170, ya + 37), (1146, ya + 37), (1146, 700), (1100, 700), (1100, 712)], dash=True))
    s.append(wire([(c4 + 60, yb + 74), (c4 + 60, 712)], dash=True))
    s.append(card(270, 712, 470, 92, DIM) + label(286, 732, "SECRETS · RENDERED FROM .ENV, NEVER WRITTEN TO A FILE", BONE, 10.5))
    s.append(chips(286, 742, ["inventory-db-secret", "billing-db-secret", "rabbitmq-secret"]))
    s.append(label(286, 790, "injected into pods with env.valueFrom.secretKeyRef", MUTED, 10, spacing=0.2))

    # image pull
    s.append(wire([(216, 724), (256, 724)], dash=True))
    s.append(label(222, 716, "PULL", MUTED, 9, spacing=0.8))

    s.append(label(30, 842, "Kinds, ports, replica bounds and storage are taken from Manifests/.", DIM, 10, spacing=0.2))
    open(os.path.join(OUT, "architecture.svg"), "w").write(svg(W, H, "".join(s)))


def components():
    W, H = 1200, 680
    s = [label(30, 34, "KUBERNETES COMPONENTS · AS THEY RUN IN THIS CLUSTER", ROSE, 11),
         title(30, 66, "Control plane, node agents and the K3s add-ons", 30),
         f'<line x1="30" y1="86" x2="{W - 30}" y2="86" stroke="{HAIR}"/>']

    def column(x, y, w, head, where, rows, bar):
        out = [card(x, y, w, 58 + len(rows) * 62, bar), label(x + 18, y + 24, head, BONE, 11),
               label(x + w - 18, y + 24, where, MUTED, 10, "end")]
        ry = y + 50
        for name, role in rows:
            out.append(f'<line x1="{x + 18}" y1="{ry - 8}" x2="{x + w - 18}" y2="{ry - 8}" stroke="{HAIR}"/>')
            out.append(title(x + 18, ry + 16, name, 18))
            out.append(body(x + 18, ry + 38, role))
            ry += 62
        return "".join(out)

    s.append(column(30, 104, 560, "CONTROL PLANE", "master · k3s server", [
        ("kube-apiserver", "The front door. kubectl, kubelets and controllers all talk to it."),
        ("datastore (etcd · sqlite in K3s)", "Holds every object: the cluster's desired and current state."),
        ("kube-scheduler", "Chooses a node for each new pod from requests, affinity and taints."),
        ("kube-controller-manager", "Control loops: ReplicaSet, StatefulSet, HPA, node, endpoints."),
        ("cloud-controller-manager", "Cloud API glue. K3s ships its own; ServiceLB provides load balancers."),
    ], CARMINE))
    s.append(column(610, 104, 560, "NODE COMPONENTS", "master + agent", [
        ("kubelet", "Starts the pods assigned to its node, runs probes, reports status."),
        ("kube-proxy", "Programs iptables so a Service IP reaches the pods behind it."),
        ("container runtime · containerd", "Pulls images from Docker Hub and runs the containers."),
        ("cni · flannel", "Pod network: every pod gets an IP reachable from both nodes."),
    ], DIM))

    s.append(label(610, 444, "K3S ADD-ONS · KUBE-SYSTEM", BONE, 11))
    addons = [("coredns", "Service names to IPs:", "inventory-db.crud-master.svc"),
              ("traefik", "Ingress controller:", "/api to api-gateway-app"),
              ("servicelb", "type: LoadBalancer:", "gateway on node-ip:3000"),
              ("metrics-server", "Pod CPU and memory", "that the HPAs read")]
    for i, (name, l1, l2) in enumerate(addons):
        x, y = 610 + (i % 2) * 284, 454 + (i // 2) * 84
        s.append(card(x, y, 276, 74, DIM) + title(x + 16, y + 26, name, 17) +
                 body(x + 16, y + 46, l1, 12) + label(x + 16, y + 63, l2, ROSE, 10.5, spacing=0.2))
    s.append(label(30, 508, "WHAT THEY DO FOR THIS PROJECT", BONE, 11))
    notes = ["kubectl apply sends each manifest to the apiserver,",
             "which stores it in the datastore.",
             "Controllers create pods from Deployments and StatefulSets;",
             "the scheduler places them on master or agent.",
             "The kubelet starts them with containerd; flannel wires",
             "them together; kube-proxy and CoreDNS make Services work.",
             "metrics-server feeds the HPA, which resizes the Deployments."]
    for i, n in enumerate(notes):
        s.append(body(30, 534 + i * 20, n, 13))
    open(os.path.join(OUT, "k8s-components.svg"), "w").write(svg(W, H, "".join(s)))


if __name__ == "__main__":
    architecture()
    components()
