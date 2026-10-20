#!/bin/bash
# Turns the raw captures in docs/screens/raw/ (from
# `CAPTURE_DIR=docs/screens/raw ./Scripts/audit-check.sh` plus create/stop/start
# output) into the terminal screenshots the README shows.
set -euo pipefail
cd "$(dirname "$0")/../screens"
R=raw
render() { python3 ../tools/render_terminal.py "$@"; }

render 01-orchestrator.svg "orchestrator.sh · create · stop · start" $R/create.txt $R/stop.txt $R/start.txt $R/vagrant.txt
render 02-nodes.svg        "kubectl get nodes -A"                     $R/nodes.txt
render 03-all.svg          "kubectl get all"                          $R/all.txt
render 04-hpa-storage.svg  "autoscaling and storage"                  $R/hpa.txt $R/pvc.txt
render 05-images-secrets.svg "images from docker hub · secrets"       $R/images.txt $R/secrets.txt
render 06-inventory-api.svg "inventory api through the gateway"       $R/movies-post.txt $R/movies-get.txt
render 07-queue-resilience.svg "billing queue resilience"             $R/stop-billing.txt $R/billing-post-down.txt $R/db-list.txt $R/orders-before.txt $R/start-billing.txt $R/orders-after.txt
render 08-audit-check.svg  "scripts/audit-check.sh"                   $R/audit-check.txt
echo "rendered $(ls ./*.svg | wc -l | tr -d ' ') screenshots"
