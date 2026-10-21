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
_used = set()          # icons referenced by the document being built


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
    _used.add(name)
    return (f'<use href="#k8s-{name}" xlink:href="#k8s-{name}" x="{x}" y="{y}" '
            f'width="{size}" height="{size}"/>')


def symbols():
    """<symbol> for every Kubernetes icon used, so each is embedded once."""
    return "".join(f'<symbol id="k8s-{n}" viewBox="{vb}">{inner}</symbol>'
                   for n, (vb, inner) in sorted(_k8s_cache.items()) if n in _used)


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
        "env": '<path d="M6 3h9l4 4v14H6z"/><path d="M15 3v4h4"/><path d="M9 12h7M9 16h7"/>',
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
HOP = 0.8            # seconds a packet spends on one wire


def style(cycle):
    """cycle: seconds for one full pass of every packet in the document."""
    return f"""<style>
.flow {{ fill: none; stroke-width: 2.2; stroke-dasharray: 3 9; stroke-opacity: 0;
         animation: flow 1.1s linear infinite; }}
@keyframes flow {{ from {{ stroke-dashoffset: 12; stroke-opacity: .55; }}
                   to {{ stroke-dashoffset: 0; stroke-opacity: .55; }} }}
.pkt {{ opacity: 0; offset-rotate: 0deg; animation: pkt {cycle}s linear infinite; }}
@keyframes pkt {{ 0% {{ offset-distance: 0%; opacity: 1; }}
                  {HOP / cycle * 100:.2f}% {{ offset-distance: 100%; opacity: 1; }}
                  {HOP / cycle * 100 + 0.5:.2f}%, 100% {{ offset-distance: 100%; opacity: 0; }} }}
.move {{ animation: move {cycle}s ease-in-out infinite; }}
@keyframes move {{ 0%, 25% {{ transform: translateX(var(--from)); opacity: .35; }}
                   45%, 100% {{ transform: translateX(0); opacity: 1; }} }}
@media (prefers-reduced-motion: reduce) {{ .flow, .pkt, .move {{ animation: none; }} }}
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


def document(w, h, body, cycle=8.0):
    packets = "".join(PACKETS)
    PACKETS.clear()
    defs = symbols()
    _used.clear()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{defs}<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{TEXT2}"/></marker></defs>{style(cycle)}'
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


# ----------------------------------------------------------------- stack
def stack():
    W, H = 1440, 214
    tiles = [
        (B("vagrant", 34), "Vagrant", "builds the 2 VMs"), (B("virtualbox", 34), "VirtualBox", "hypervisor"),
        (B("ubuntu", 34), "Ubuntu 22.04", "VM OS"), (B("k3s", 34), "K3s", "K8s distribution"),
        (B("kubernetes", 34), "Kubernetes", "manifests · kubectl"), (B("docker", 34), "Docker", "builds the images"),
        (B("docker", 34), "Docker Hub", "alasmawi/* registry"), (B("gnubash", 34), "Bash", "orchestrator.sh"),
        (B("debian", 34), "Debian 12", "image base"), (B("python", 34), "Python", "the three apps"),
        (B("flask", 34), "Flask", "HTTP APIs"), (B("sqlalchemy", 34), "SQLAlchemy", "ORM"),
        (B("postgresql", 34), "PostgreSQL 15", "two databases"), (B("rabbitmq", 34), "RabbitMQ", "billing_queue"),
        (B("traefikproxy", 34), "Traefik", "Ingress controller"), (G("nfs", 34), "NFS", "shared volumes"),
    ]
    s = [text(24, 30, "Built with", 15, TEXT, 700)]
    for i, (icon, name, role) in enumerate(tiles):
        x, y = 24 + (i % 8) * 175, 46 + (i // 8) * 82
        s.append(f'<rect x="{x}" y="{y}" width="167" height="72" rx="8" fill="#FFFFFF" stroke="{LINE}"/>')
        s.append(icon(x + 12, y + 19) + text(x + 56, y + 32, name, 13.5, TEXT, 700) + text(x + 56, y + 50, role, 11, TEXT2))
    open(os.path.join(DOCS, "stack.svg"), "w").write(document(W, H, "".join(s)))


# --------------------------------------------------------- request flow
def request_flow():
    W, H = 1440, 640
    cols = [("Client", lambda x, y: brand("curl", x - 20, y, 34) + brand("postman", x + 20, y, 34), None, "curl · Postman"),
            ("api-gateway-app", B("flask", 34), "deploy", ":3000"),
            ("inventory-app", B("flask", 34), "deploy", ":8080"),
            ("inventory-db", B("postgresql", 34), "sts", ":5432"),
            ("rabbit-queue", B("rabbitmq", 34), "deploy", ":5672"),
            ("billing-app", B("python", 34), "sts", ":8080"),
            ("billing-db", B("postgresql", 34), "sts", ":5432")]
    xs = [110 + i * 203 for i in range(len(cols))]
    s = [text(24, 36, "Request flows", 20, TEXT, 700),
         text(24, 58, "Movies are synchronous. Billing goes through RabbitMQ, so it answers 200 even while billing-app "
                      "is stopped.", 13, TEXT2)]
    for x, (name, logo, kind, port) in zip(xs, cols):
        s.append(f'<line x1="{x}" y1="160" x2="{x}" y2="{H - 24}" stroke="{LINE}" stroke-width="1.4" stroke-dasharray="5 5"/>')
        s.append(f'<rect x="{x - 84}" y="76" width="168" height="84" rx="8" fill="#FFFFFF" stroke="{LINE}"/>')
        s.append(logo(x - 17, 84) + text(x, 134, name, 13, TEXT, 700, "middle"))
        if kind:
            s.append(k8s(kind, x - 40, 140, 15) + text(x - 21, 152, port, 11, TEXT2, 500, family=MONO))
        else:
            s.append(text(x, 152, port, 11, TEXT2, 500, "middle", MONO))

    def band(y, h, title, colour, fill):
        return (f'<rect x="16" y="{y}" width="{W - 32}" height="{h}" rx="10" fill="{fill}" stroke="{colour}" stroke-opacity=".35"/>' +
                text(30, y + 20, title, 12.5, colour, 700))

    s.append(band(176, 206, "Synchronous: movies CRUD", "#326CE5", "#326CE50A"))
    s.append(band(394, 230, "Asynchronous: billing", "#E65C00", "#FF66000A"))
    SYNC, ASYNC = "#326CE5", "#FF6600"
    steps = [  # (from col, to col, label, y, colour, reply)
        (0, 1, "POST /api/movies/", 222, SYNC, False), (1, 2, "HTTP inventory-app:8080", 256, SYNC, False),
        (2, 3, "INSERT INTO movies", 290, SYNC, False), (2, 1, "201 + movie JSON", 324, SYNC, True),
        (1, 0, "201 + movie JSON", 358, SYNC, True),
        (0, 1, "POST /api/billing/", 440, ASYNC, False), (1, 4, "publish to billing_queue (durable)", 474, ASYNC, False),
        (1, 0, "200 Message posted", 508, ASYNC, True), (4, 5, "deliver when billing-app runs", 542, ASYNC, False),
        (5, 6, "INSERT INTO orders", 576, ASYNC, False), (5, 4, "ack: message removed", 610, ASYNC, True)]
    for i, (a, b, label, y, colour, reply) in enumerate(steps):
        x1, x2 = xs[a], xs[b]
        d = 1 if x2 > x1 else -1
        s.append(arrow([(x1 + d * 4, y), (x2 - d * 6, y)], dash=reply, colour=colour if not reply else TEXT2,
                       packet=(i * 0.95, colour)))
        mid = (x1 + x2) / 2 + 9
        s.append(text(mid, y - 6, label, 11.5, TEXT, 500, "middle"))
        cx = mid - len(label) * 3.1 - 14
        s.append(f'<circle cx="{cx}" cy="{y - 10}" r="8" fill="{colour}"/>' +
                 text(cx, y - 6, str(i + 1), 10, "#FFFFFF", 700, "middle"))
    open(os.path.join(DOCS, "request-flow.svg"), "w").write(document(W, H, "".join(s), cycle=11.0))


# --------------------------------------------------------------- secrets
def secrets_flow():
    W, H = 1440, 250
    s = [text(24, 34, "Secrets: from .env to pods, never written to a file", 20, TEXT, 700)]
    boxes = [(G("env", 40), ".env", "gitignored, local only", 24),
             (B("gnubash", 40), "apply-secrets.sh", "create secret --dry-run", 268),
             (K("api", 40), "kube-apiserver", "stores 3 Secret objects", 512)]
    for icon, name, sub, x in boxes:
        s.append(f'<rect x="{x}" y="70" width="200" height="120" rx="8" fill="#FFFFFF" stroke="{LINE}"/>')
        s.append(icon(x + 80, 84) + text(x + 100, 148, name, 14, TEXT, 700, "middle") +
                 text(x + 100, 168, sub, 11, TEXT2, 400, "middle", MONO if "--" in sub else FONT))
    s.append(arrow([(224, 130), (268, 130)], packet=(0, "#4EAA25"), flow="#4EAA25"))
    s.append(arrow([(468, 130), (512, 130)], "piped", (490, 112), packet=(1, "#4EAA25"), flow="#4EAA25"))
    s.append(group(756, 60, 300, 150, "Secrets · crud-master", TEXT2, lambda x, y: k8s("secret", x, y, 24)))
    for i, (name, keys) in enumerate([("inventory-db-secret", "POSTGRES_USER · PASSWORD · DB"),
                                      ("billing-db-secret", "POSTGRES_USER · PASSWORD · DB"),
                                      ("rabbitmq-secret", "RABBITMQ_USER · PASSWORD")]):
        y = 98 + i * 36
        s.append(k8s("secret", 772, y, 26) + text(806, y + 12, name, 12, TEXT, 700, family=MONO) +
                 text(806, y + 26, keys, 10, TEXT2, 400, family=MONO))
    s.append(arrow([(712, 130), (756, 130)], packet=(2, "#4EAA25"), flow="#4EAA25"))
    s.append(group(1100, 60, 316, 150, "Pods read them via secretKeyRef", "#326CE5", lambda x, y: k8s("pod", x, y, 24)))
    pods = [("postgresql", "inventory-db"), ("flask", "inventory-app"), ("postgresql", "billing-db"),
            ("python", "billing-app"), ("rabbitmq", "rabbit-queue"), ("flask", "api-gateway-app")]
    for i, (logo, name) in enumerate(pods):
        x, y = 1116 + (i % 2) * 150, 100 + (i // 2) * 34
        s.append(brand(logo, x, y, 22) + text(x + 30, y + 16, name, 11.5, TEXT, 600))
    s.append(arrow([(1056, 130), (1100, 130)], "env", (1078, 112), packet=(3, "#4EAA25"), flow="#4EAA25"))
    s.append(text(24, 236, "No committed file contains a credential: the Secret manifests exist only in memory, "
                           "on their way to the API server.", 12, TEXT2))
    open(os.path.join(DOCS, "secrets-flow.svg"), "w").write(document(W, H, "".join(s), cycle=6.0))


# --------------------------------------------------------------- storage
def storage_flow():
    W, H = 1440, 360
    s = [text(24, 34, "A database pod moves between nodes and keeps its data", 20, TEXT, 700),
         text(24, 56, "cordon the node + delete inventory-db-0: the StatefulSet recreates it on the other node, "
                      "and the same PVC mounts the same NFS directory.", 13, TEXT2)]
    for x, name, ip in [(24, "VM agent", "192.168.56.22"), (520, "VM master", "192.168.56.21")]:
        s.append(group(x, 76, 470, 140, f"{name} · {ip}", "#E95420", lambda gx, gy: brand("ubuntu", gx, gy, 22), fill="#FFFFFF"))
    s.append(text(110, 194, "cordoned: no new pods", 11.5, MUTED, 400, "start"))
    # ghost on agent, live pod on master (animated move from agent to master)
    s.append(f'<rect x="150" y="112" width="220" height="66" rx="8" fill="none" stroke="{LINE}" stroke-dasharray="5 4"/>' +
             text(260, 150, "old pod deleted", 12, MUTED, 500, "middle"))
    pod = (f'<rect x="646" y="112" width="220" height="66" rx="8" fill="#FFFFFF" stroke="#4169E1" stroke-width="1.6"/>' +
           brand("postgresql", 660, 126, 36) + text(708, 140, "inventory-db-0", 14, TEXT, 700) +
           k8s("sts", 708, 150, 16) + text(728, 162, "StatefulSet · Running", 11, TEXT2))
    s.append(f'<g class="move" style="--from: -496px">{pod}</g>')
    s.append(arrow([(372, 145), (644, 145)], "rescheduled", (508, 132), dash=True))
    # storage chain under the live pod
    chain = [(K("pvc", 34), "PVC", "inventory-db-data-inventory-db-0", 520),
             (K("pv", 34), "PV", "inventory-db-pv · 1Gi · Retain", 820),
             (G("nfs", 34), "NFS export on master", "/srv/nfs/k3s/inventory-db", 1120)]
    for icon, name, sub, x in chain:
        s.append(f'<rect x="{x}" y="250" width="280" height="70" rx="8" fill="#FFFFFF" stroke="{LINE}"/>')
        s.append(icon(x + 14, 268) + text(x + 60, 280, name, 13.5, TEXT, 700) + text(x + 60, 298, sub, 10.5, TEXT2, 400, family=MONO))
    s.append(arrow([(756, 180), (756, 216), (660, 216), (660, 250)], "mounts", (708, 216), dash=True))
    s.append(arrow([(800, 285), (820, 285)]) + arrow([(1100, 285), (1120, 285)]))
    s.append(group(1000, 76, 416, 140, "Why it works", "#4169E1", lambda x, y: k8s("sc", x, y, 24), fill="#F7FAFF"))
    for i, line in enumerate(["local-path would pin the volume to one node's disk.",
                              "These PVs are NFS directories served by master,",
                              "so kubelet on either node can mount them.",
                              "The PVC belongs to the pod's name, not to a node."]):
        s.append(text(1016, 124 + i * 20, line, 12, TEXT2))
    open(os.path.join(DOCS, "storage-flow.svg"), "w").write(document(W, H, "".join(s), cycle=6.0))


if __name__ == "__main__":
    architecture()
    components()
    stack()
    request_flow()
    secrets_flow()
    storage_flow()
