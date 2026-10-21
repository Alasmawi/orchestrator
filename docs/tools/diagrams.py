#!/usr/bin/env python3
"""Generate the README diagrams as self-contained SVGs (icons are inlined, so
nothing is fetched when the image is viewed).

    python3 docs/tools/diagrams.py   # writes docs/architecture.svg, docs/k8s-components.svg

Everything drawn here mirrors the manifests: kinds, ports, replica bounds,
Service types and storage. Change the manifests, then change this.

Icons: docs/icons/brands (Simple Icons, CC0) and docs/icons/k8s (Kubernetes
community icons, Apache-2.0). See docs/icons/README.md.
"""
import html
import os
import re
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..")
ICONS = os.path.join(DOCS, "icons")
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

FONT = "'Inter','Segoe UI','Helvetica Neue',Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono','SFMono-Regular',Menlo,Consolas,monospace"
TEXT, TEXT2, MUTED, LINE = "#232F3E", "#545B64", "#7D8998", "#D5DBDB"

# Official brand colours (Simple Icons data).
BRAND = {
    "apple": "000000", "containerd": "575757", "curl": "073551", "debian": "A81D33",
    "docker": "2496ED", "etcd": "419EDA", "flask": "000000", "gnubash": "4EAA25",
    "k3s": "FFC61C", "kubernetes": "326CE5", "linux": "FCC624", "postgresql": "4169E1",
    "postman": "FF6C37", "python": "3776AB", "rabbitmq": "FF6600", "sqlalchemy": "D71F00",
    "sqlite": "003B57", "traefikproxy": "24A1C1", "ubuntu": "E95420", "vagrant": "1868F2",
    "virtualbox": "2F61B4",
}
e = html.escape


# --------------------------------------------------------------------- icons
def brand(name, x, y, size, colour=None):
    """A Simple Icons logo: one 24x24 path, filled with its brand colour."""
    src = open(os.path.join(ICONS, "brands", f"{name}.svg")).read()
    d = re.search(r'<path d="([^"]+)"', src).group(1)
    fill = colour or f"#{BRAND[name]}"
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 24 24">'
            f'<path d="{d}" fill="{fill}"/></svg>')


_k8s_cache = {}


def k8s(name, x, y, size):
    """An official Kubernetes icon, cleaned of editor metadata, ids namespaced."""
    if name not in _k8s_cache:
        root = ET.parse(os.path.join(ICONS, "k8s", f"{name}.svg")).getroot()
        view_box = root.get("viewBox")
        parts = []
        for child in root:
            tag = child.tag.split("}")[-1]
            if tag in ("metadata", "namedview") or not child.tag.startswith("{" + SVG_NS):
                continue
            for el in child.iter():
                for attr in list(el.attrib):
                    if attr.startswith("{") and not attr.startswith("{" + SVG_NS):
                        del el.attrib[attr]
                if "id" in el.attrib:
                    el.attrib["id"] = f"k8s-{name}-{el.attrib['id']}"
            parts.append(ET.tostring(child, encoding="unicode"))
        _k8s_cache[name] = (view_box, "".join(parts))
    return (f'<use href="#k8s-{name}" xlink:href="#k8s-{name}" x="{x}" y="{y}" '
            f'width="{size}" height="{size}"/>')


def symbols():
    """<symbol> for every Kubernetes icon used, so each is embedded once."""
    return "".join(f'<symbol id="k8s-{n}" viewBox="{vb}">{inner}</symbol>'
                   for n, (vb, inner) in sorted(_k8s_cache.items()))


def glyph(kind, x, y, size, colour=TEXT2):
    """Small drawn icons for things without an official logo."""
    s = size / 24
    paths = {
        "nfs": '<rect x="3" y="4" width="18" height="6" rx="1.5"/><rect x="3" y="14" width="18" height="6" rx="1.5"/>'
               '<circle cx="7" cy="7" r="1" fill="C"/><circle cx="7" cy="17" r="1" fill="C"/>'
               '<path d="M12 10v4"/>',
        "flannel": '<circle cx="5" cy="12" r="2.5"/><circle cx="19" cy="5" r="2.5"/><circle cx="19" cy="19" r="2.5"/>'
                   '<path d="M7.3 11 16.7 6M7.3 13l9.4 5M19 7.5v9"/>',
        "dns": '<rect x="2.5" y="5" width="19" height="14" rx="2"/>'
               '<text x="12" y="15.2" font-size="7" font-weight="700" text-anchor="middle" fill="C" stroke="none" '
               f'font-family="{FONT}">DNS</text>',
        "metrics": '<path d="M3 21h18"/><rect x="5" y="12" width="3" height="7"/><rect x="10.5" y="7" width="3" height="12"/>'
                   '<rect x="16" y="3" width="3" height="16"/>',
    }[kind].replace('"C"', f'"{colour}"')
    return (f'<g transform="translate({x},{y}) scale({s})" fill="none" stroke="{colour}" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round">{paths}</g>')


# ------------------------------------------------------------------ drawing
def text(x, y, s, size=13, fill=TEXT, weight=400, anchor="start", family=FONT):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{e(s)}</text>')


def group(x, y, w, h, title, colour, icon=None, dash=False, fill=None, sub=None):
    fill = fill or "none"
    d = ' stroke-dasharray="6 5"' if dash else ""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{colour}" stroke-width="1.6"{d}/>']
    tx = x + 14
    if icon:
        out.append(icon(x + 12, y + 9))
        tx = x + 44
    out.append(text(tx, y + 26, title, 14, colour, 700))
    if sub:
        out.append(text(x + w - 14, y + 26, sub, 12, TEXT2, 400, "end"))
    return "".join(out)


def tile(x, y, icon, name, detail=None, w=76):
    """Small icon + caption, used for components inside a node."""
    out = [icon(x + (w - 36) / 2, y), text(x + w / 2, y + 52, name, 11.5, TEXT, 600, "middle")]
    if detail:
        out.append(text(x + w / 2, y + 66, detail, 10.5, TEXT2, 400, "middle"))
    return "".join(out)


def node(x, y, logo, name, kind_icon, kind, detail, colour, badge=None, w=170, h=128):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#FFFFFF" stroke="{LINE}" stroke-width="1.2"/>',
           f'<rect x="{x}" y="{y}" width="{w}" height="4" rx="2" fill="{colour}"/>',
           logo(x + w / 2 - 20, y + 14),
           text(x + w / 2, y + 76, name, 14.5, TEXT, 700, "middle"),
           k8s(kind_icon, x + 14, y + 85, 18),
           text(x + 36, y + 98, kind, 11.5, TEXT2, 500),
           text(x + w / 2, y + 117, detail, 11.5, colour, 600, "middle", MONO)]
    if badge:
        out.append(k8s(badge, x + w - 34, y + 10, 24))
    return "".join(out)


# Animation: packets travel along request wires (CSS motion path). They are
# invisible unless animating, so a still render or prefers-reduced-motion
# shows the finished static diagram.
PACKETS = []
CYCLE = 8.0          # seconds for one full pass of both flows
HOP = 0.8            # seconds a packet spends on one wire
STYLE = f"""<style>
.flow {{ fill: none; stroke-width: 2.2; stroke-dasharray: 3 9; stroke-opacity: 0;
         animation: flow 1.1s linear infinite; }}
@keyframes flow {{ from {{ stroke-dashoffset: 12; stroke-opacity: .55; }}
                   to {{ stroke-dashoffset: 0; stroke-opacity: .55; }} }}
.pkt {{ opacity: 0; offset-rotate: 0deg; animation: pkt {CYCLE}s linear infinite; }}
@keyframes pkt {{ 0% {{ offset-distance: 0%; opacity: 1; }}
                  {HOP / CYCLE * 100:.2f}% {{ offset-distance: 100%; opacity: 1; }}
                  {HOP / CYCLE * 100 + 0.5:.2f}%, 100% {{ offset-distance: 100%; opacity: 0; }} }}
@media (prefers-reduced-motion: reduce) {{ .flow, .pkt {{ animation: none; }} }}
</style>"""


def arrow(points, label=None, at=None, dash=False, colour=TEXT2, flow=None, packet=None):
    """flow: colour of animated dashes on the wire; packet: (hop index, colour)."""
    d = " ".join(f"{'M' if i == 0 else 'L'}{px},{py}" for i, (px, py) in enumerate(points))
    dd = ' stroke-dasharray="5 4"' if dash else ""
    out = [f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="1.6"{dd} marker-end="url(#arrow)"/>']
    if flow:
        out.append(f'<path class="flow" d="{d}" stroke="{flow}"/>')
    if packet:
        hop, pcolour = packet
        PACKETS.append(f'<circle class="pkt" r="5" fill="{pcolour}" stroke="#FFFFFF" stroke-width="1.6" '
                       f'style="offset-path: path(\'{d}\'); animation-delay: {hop * HOP:.1f}s"/>')
    if label:
        lx, ly = at
        w = len(label) * 6.6 + 12
        out.append(f'<rect x="{lx - w / 2}" y="{ly - 11}" width="{w}" height="17" rx="8.5" fill="#FFFFFF" stroke="{LINE}"/>')
        out.append(text(lx, ly + 2, label, 10.5, TEXT2, 500, "middle", MONO))
    return "".join(out)


def document(w, h, body):
    packets = "".join(PACKETS)
    PACKETS.clear()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{symbols()}<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{TEXT2}"/></marker></defs>{STYLE}'
            f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>{body}{packets}</svg>\n')


def B(name, size=40, colour=None):
    return lambda x, y: brand(name, x, y, size, colour)


def K(name, size=40):
    return lambda x, y: k8s(name, x, y, size)


def G(kind, size=40):
    return lambda x, y: glyph(kind, x, y, size)


# ------------------------------------------------------------- architecture
def architecture():
    W, H = 1440, 950
    s = [text(24, 40, "orchestrator · deployed architecture", 22, TEXT, 700),
         text(24, 63, "Six microservices on a two-node K3s cluster, provisioned by Vagrant on VirtualBox, "
                      "images pulled from Docker Hub.", 13.5, TEXT2)]

    # legend
    lx = 980
    s.append(arrow([(lx, 36), (lx + 34, 36)]) + text(lx + 42, 40, "request", 12, TEXT2))
    s.append(arrow([(lx + 104, 36), (lx + 138, 36)], dash=True) + text(lx + 146, 40, "volume · image pull", 12, TEXT2))
    s.append(k8s("deploy", lx, 50, 20) + text(lx + 26, 64, "Deployment", 12, TEXT2))
    s.append(k8s("sts", lx + 104, 50, 20) + text(lx + 130, 64, "StatefulSet", 12, TEXT2))
    s.append(k8s("hpa", lx + 222, 50, 20) + text(lx + 248, 64, "HPA", 12, TEXT2))
    s.append(k8s("svc", lx + 290, 50, 20) + text(lx + 316, 64, "Service", 12, TEXT2))

    # ---- host
    s.append(group(24, 92, 232, 600, "Host · macOS", TEXT2, lambda x, y: brand("apple", x, y, 22), fill="#F8F9F9"))
    hosts = [
        (lambda x, y: brand("curl", x - 22, y, 40) + brand("postman", x + 22, y, 40), "Client", "curl · Postman"),
        (B("kubernetes"), "kubectl", "~/.kube/config"),
        (B("gnubash"), "orchestrator.sh", "create · start · stop"),
        (B("vagrant"), "Vagrant", "2 VMs from Vagrantfile"),
        (B("docker"), "Docker", "Scripts/build-push.sh"),
    ]
    for i, (logo, name, detail) in enumerate(hosts):
        y = 134 + i * 110
        s.append(f'<rect x="44" y="{y}" width="192" height="96" rx="8" fill="#FFFFFF" stroke="{LINE}"/>')
        s.append(logo(120, y + 10))
        s.append(text(140, y + 70, name, 14, TEXT, 700, "middle"))
        s.append(text(140, y + 87, detail, 11, TEXT2, 400, "middle", MONO))
    s.append(arrow([(140, 574), (140, 584)]))           # orchestrator -> vagrant (stacked)

    # ---- docker hub
    s.append(group(24, 712, 232, 216, "Docker Hub", "#2496ED", lambda x, y: brand("docker", x, y, 22), fill="#F2F8FE"))
    for i, img in enumerate(["inventory-db", "billing-db", "rabbit-queue", "inventory-app", "billing-app", "api-gateway-app"]):
        s.append(text(44, 766 + i * 25, f"alasmawi/{img}", 12, TEXT, 500, family=MONO))
    s.append(arrow([(140, 664), (140, 712)], "push", (172, 690)))

    # ---- virtualbox network / k3s cluster / VMs
    s.append(group(280, 92, 1136, 836, "VirtualBox · host-only network 192.168.56.0/24", "#2F61B4",
                   lambda x, y: brand("virtualbox", x, y, 22), fill="#F5F8FD"))
    s.append(group(298, 134, 1100, 778, "K3s cluster", "#B8860B", lambda x, y: brand("k3s", x, y, 22),
                   fill="#FFFDF5", sub="v1.36 · flannel VXLAN over the host-only NIC"))

    s.append(group(316, 176, 656, 196, "VM master · 192.168.56.21 · K3s server", "#E95420",
                   lambda x, y: brand("ubuntu", x, y, 22), fill="#FFFFFF"))
    master = [(K("api", 36), "apiserver", ":6443"), (K("sched", 36), "scheduler", None),
              (K("c-m", 36), "controller", "manager"), (B("sqlite", 36), "SQLite", "datastore"),
              (B("traefikproxy", 36), "Traefik", "ingress :80"), (K("svc", 36), "ServiceLB", "LB :3000"),
              (G("dns", 36), "CoreDNS", None), (G("metrics", 36), "metrics", "server"),
              (G("nfs", 36), "NFS server", "/srv/nfs/k3s")]
    for i, (icon, name, detail) in enumerate(master):
        s.append(tile(338 + i * 70, 220, icon, name, detail, 70))
    s.append(text(332, 356, "also runs the node agents: kubelet · kube-proxy · containerd · flannel", 11.5, TEXT2))

    s.append(group(990, 176, 390, 196, "VM agent · 192.168.56.22 · K3s agent", "#E95420",
                   lambda x, y: brand("ubuntu", x, y, 22), fill="#FFFFFF"))
    agent = [(K("kubelet", 36), "kubelet", None), (K("k-proxy", 36), "kube-proxy", None),
             (B("containerd", 36), "containerd", "runtime"), (G("flannel", 36), "flannel", "pod network"),
             (G("nfs", 36), "NFS client", None)]
    for i, (icon, name, detail) in enumerate(agent):
        s.append(tile(1000 + i * 74, 220, icon, name, detail, 74))
    s.append(text(1004, 356, "joins with the token shared through /vagrant", 11.5, TEXT2))

    # ---- namespace
    s.append(group(316, 392, 1064, 384, "Namespace crud-master", "#326CE5", lambda x, y: k8s("ns", x, y, 24),
                   dash=True, fill="#F7FAFF", sub="pods are scheduled on either node"))
    ya, yb, yg = 438, 622, 530
    s.append(f'<rect x="336" y="470" width="124" height="96" rx="8" fill="#FFFFFF" stroke="{LINE}"/>' +
             k8s("ing", 348, 482, 30) + brand("traefikproxy", 384, 484, 26) +
             text(398, 536, "Ingress", 12.5, TEXT, 700, "middle") + text(398, 553, ":80 /api", 11, TEXT2, 400, "middle", MONO))
    s.append(f'<rect x="336" y="590" width="124" height="96" rx="8" fill="#FFFFFF" stroke="{LINE}"/>' +
             k8s("svc", 382, 600, 34) +
             text(398, 653, "LoadBalancer", 12.5, TEXT, 700, "middle") +
             text(398, 670, ":3000 · NodePort :30000", 9.5, TEXT2, 400, "middle", MONO))
    s.append(node(490, yg, B("flask"), "api-gateway-app", "deploy", "Deployment", ":3000 · 1-3 @ 60%", "#326CE5", "hpa"))
    s.append(node(730, ya, B("flask"), "inventory-app", "deploy", "Deployment", ":8080 · 1-3 @ 60%", "#326CE5", "hpa"))
    s.append(node(730, yb, B("rabbitmq"), "rabbit-queue", "deploy", "Deployment", ":5672 · billing_queue", "#FF6600"))
    s.append(node(950, yb, B("python"), "billing-app", "sts", "StatefulSet", ":8080 · consumer", "#3776AB"))
    s.append(node(1186, ya, B("postgresql"), "inventory-db", "sts", "StatefulSet", ":5432 · movies_db", "#4169E1"))
    s.append(node(1186, yb, B("postgresql"), "billing-db", "sts", "StatefulSet", ":5432 · billing_db", "#4169E1"))

    # ---- secrets + storage
    s.append(group(316, 792, 540, 110, "Secrets · from .env, never written to a file", TEXT2,
                   lambda x, y: k8s("secret", x, y, 24), fill="#FFFFFF"))
    for i, name in enumerate(["inventory-db-secret", "billing-db-secret", "rabbitmq-secret"]):
        x = 330 + i * 176
        s.append(k8s("secret", x, 832, 30) + text(x + 35, 845, name, 10.5, TEXT, 600, family=MONO) +
                 text(x + 35, 861, "secretKeyRef", 10, TEXT2, 400, family=MONO))
    s.append(group(870, 792, 510, 110, "Storage · cluster-scoped", "#4169E1",
                   lambda x, y: k8s("sc", x, y, 24), fill="#FFFFFF"))
    store = [(K("pvc", 32), "2 PVCs", "one per DB pod"), (K("pv", 32), "2 PVs · 1Gi", "Retain"),
             (K("sc", 32), "nfs-static", "StorageClass"), (G("nfs", 32), "NFS export", "on master")]
    for i, (icon, name, detail) in enumerate(store):
        x = 882 + i * 124
        s.append(icon(x, 832) + text(x + 37, 845, name, 11.5, TEXT, 700) + text(x + 37, 861, detail, 10, TEXT2))
        if i < 3:
            s.append(arrow([(x + 106, 848), (x + 120, 848)]))

    # ---- traffic
    SYNC, ASYNC, OPS = "#326CE5", "#FF6600", "#4EAA25"
    s.append(arrow([(236, 182), (268, 182), (268, 638), (336, 638)], "HTTP :3000", (302, 610),
                   flow=SYNC, packet=(0, SYNC)))
    s.append(arrow([(236, 182), (268, 182), (268, 518), (336, 518)], flow=ASYNC, packet=(5, ASYNC)))
    s.append(arrow([(268, 518), (336, 518)], ":80", (302, 506)))
    s.append(arrow([(236, 292), (258, 292), (258, 238), (343, 238)], "HTTPS :6443", (300, 278),
                   flow=OPS, packet=(3, OPS)))
    s.append(arrow([(460, 518), (475, 518), (475, 575), (490, 575)], packet=(6, ASYNC)))
    s.append(arrow([(460, 638), (475, 638), (475, 615), (490, 615)], packet=(1, SYNC)))
    s.append(arrow([(660, 575), (695, 575), (695, ya + 64), (730, ya + 64)], "HTTP :8080", (695, 532),
                   flow=SYNC, packet=(2, SYNC)))
    s.append(arrow([(660, 615), (695, 615), (695, yb + 64), (730, yb + 64)], "AMQP :5672", (695, 660),
                   flow=ASYNC, packet=(7, ASYNC)))
    s.append(arrow([(900, ya + 64), (1186, ya + 64)], "SQL :5432", (1043, ya + 64), flow=SYNC, packet=(3, SYNC)))
    s.append(arrow([(900, yb + 64), (950, yb + 64)], "consume", (925, yb + 46), flow=ASYNC, packet=(8, ASYNC)))
    s.append(arrow([(1120, yb + 64), (1186, yb + 64)], "SQL", (1153, yb + 46), flow=ASYNC, packet=(9, ASYNC)))
    s.append(text(815, yb + 144, "messages wait in billing_queue while billing-app is stopped", 11.5, TEXT2, 400, "middle"))
    s.append(arrow([(1356, ya + 64), (1370, ya + 64), (1370, 800)], dash=True))
    s.append(arrow([(1271, yb + 128), (1271, 800)], dash=True))
    s.append(arrow([(256, 846), (298, 846)], dash=True))
    s.append(text(262, 838, "pull", 10.5, TEXT2, 500, family=MONO))

    s.append(text(24, 942, "Kinds, ports, replica bounds and storage mirror Manifests/. "
                           "Logos: Simple Icons (CC0) · Kubernetes icons (Apache-2.0).", 11, MUTED))
    open(os.path.join(DOCS, "architecture.svg"), "w").write(document(W, H, "".join(s)))


# ---------------------------------------------------------- k8s components
def components():
    W, H = 1440, 878
    s = [text(24, 40, "Kubernetes components · as they run in this cluster", 22, TEXT, 700),
         text(24, 63, "The K3s server on master is the control plane; both VMs run the node agents; "
                      "K3s bundles the add-ons in kube-system.", 13.5, TEXT2)]

    def rows(gx, gy, items):
        out = []
        for i, (icon, name, role) in enumerate(items):
            y = gy + 50 + i * 80
            if i:
                out.append(f'<line x1="{gx + 16}" y1="{y - 12}" x2="{gx + 660}" y2="{y - 12}" stroke="{LINE}"/>')
            out.append(icon(gx + 18, y))
            out.append(text(gx + 82, y + 20, name, 15, TEXT, 700))
            out.append(text(gx + 82, y + 41, role, 13, TEXT2))
        return "".join(out)

    s.append(group(24, 88, 680, 470, "Control plane · master (K3s server)", "#326CE5",
                   lambda x, y: k8s("control-plane", x, y, 24), fill="#F7FAFF"))
    s.append(rows(24, 88, [
        (K("api", 48), "kube-apiserver", "The front door: kubectl, kubelets and controllers all talk to it."),
        (K("etcd", 48), "Datastore · SQLite via kine (etcd in full K8s)", "Stores every object: the desired and current state of the cluster."),
        (K("sched", 48), "kube-scheduler", "Picks a node for each new pod from requests, affinity and taints."),
        (K("c-m", 48), "kube-controller-manager", "Control loops: ReplicaSet, StatefulSet, HPA, nodes, endpoints."),
        (K("c-c-m", 48), "cloud-controller-manager", "Cloud API glue. K3s ships its own; ServiceLB provides load balancers."),
    ]))
    s.append(group(736, 88, 680, 390, "Node components · master and agent", "#E95420",
                   lambda x, y: k8s("node", x, y, 24), fill="#FFF8F5"))
    s.append(rows(736, 88, [
        (K("kubelet", 48), "kubelet", "Starts the pods assigned to its node, runs probes, reports status."),
        (K("k-proxy", 48), "kube-proxy", "Programs iptables so a Service IP reaches the pods behind it."),
        (B("containerd", 48), "containerd", "Container runtime: pulls images from Docker Hub and runs them."),
        (G("flannel", 48), "flannel (CNI)", "Pod network: every pod gets an IP reachable from both nodes."),
    ]))
    s.append(group(736, 494, 680, 196, "K3s add-ons · kube-system", "#B8860B",
                   lambda x, y: brand("k3s", x, y, 22), fill="#FFFDF5"))
    addons = [(G("dns", 40), "CoreDNS", "Service names to IPs"), (B("traefikproxy", 40), "Traefik", "Ingress /api"),
              (K("svc", 40), "ServiceLB", "LoadBalancer :3000"), (G("metrics", 40), "metrics-server", "CPU for the HPAs"),
              (K("sc", 40), "local-path", "default StorageClass")]
    for i, (icon, name, role) in enumerate(addons):
        x, y = 752 + (i % 3) * 220, 536 + (i // 3) * 74
        s.append(f'<rect x="{x}" y="{y}" width="208" height="64" rx="8" fill="#FFFFFF" stroke="{LINE}"/>')
        s.append(icon(x + 12, y + 12) + text(x + 62, y + 28, name, 13.5, TEXT, 700) + text(x + 62, y + 46, role, 11.5, TEXT2))

    s.append(group(24, 574, 680, 116, "Resources this project creates", "#4169E1",
                   lambda x, y: k8s("ns", x, y, 24), fill="#FFFFFF"))
    kinds = [("ns", "Namespace"), ("deploy", "Deployment"), ("sts", "StatefulSet"), ("svc", "Service"),
             ("ing", "Ingress"), ("hpa", "HPA"), ("secret", "Secret"), ("pvc", "PVC"), ("pv", "PV")]
    for i, (icon, name) in enumerate(kinds):
        x = 44 + i * 73
        s.append(k8s(icon, x + 14, 612, 36) + text(x + 32, 664, name, 11, TEXT, 600, "middle"))

    # how a manifest becomes a running pod
    s.append(group(24, 706, 1392, 138, "From kubectl apply to a running pod", TEXT2, fill="#F8F9F9"))
    flow = [(B("kubernetes", 36), "kubectl apply", "sends the manifest"),
            (K("api", 36), "apiserver", "validates, stores"),
            (K("etcd", 36), "datastore", "desired state"),
            (K("c-m", 36), "controllers", "create pods"),
            (K("sched", 36), "scheduler", "binds to a node"),
            (K("kubelet", 36), "kubelet", "starts the pod"),
            (B("containerd", 36), "containerd", "pulls alasmawi/*"),
            (K("pod", 36), "pod", "Running, Ready")]
    for i, (icon, name, role) in enumerate(flow):
        x = 48 + i * 172
        s.append(icon(x + 50, 742) + text(x + 68, 796, name, 13, TEXT, 700, "middle") +
                 text(x + 68, 813, role, 11.5, TEXT2, 400, "middle"))
        if i < len(flow) - 1:
            s.append(arrow([(x + 104, 760), (x + 204, 760)], flow="#326CE5", packet=(i, "#326CE5")))

    s.append(text(24, 868, "Logos: Simple Icons (CC0) · Kubernetes icons (Apache-2.0).", 11, MUTED))
    open(os.path.join(DOCS, "k8s-components.svg"), "w").write(document(W, H, "".join(s)))


if __name__ == "__main__":
    architecture()
    components()
