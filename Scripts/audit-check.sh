#!/bin/bash
# Runs the hands-on part of the audit against a running cluster, using the
# same commands the auditor uses (plain `kubectl`, default namespace from the
# kubeconfig context), and prints PASS/FAIL per check.
#
#   ./Scripts/audit-check.sh            # rehearse the audit
#   CAPTURE_DIR=docs/screens/raw ./Scripts/audit-check.sh
#                                       # also save each step's output
#
# Side effects: adds 1 movie and 2 orders (user_id 20 and 22), and scales
# billing-app to 0 and back to 1, exactly like the audit does. Order checks
# compare counts before/after, so re-running it is fine.
set -uo pipefail
cd "$(dirname "$0")/.."

set -a
# shellcheck disable=SC1091
[ -f .env ] && source .env
set +a
[ -z "${KUBECONFIG:-}" ] && [ -f .kube/config ] && export KUBECONFIG="$(pwd)/.kube/config"

GATEWAY="${GATEWAY:-http://192.168.56.21:3000}"
CAPTURE_DIR="${CAPTURE_DIR:-}"
[ -n "$CAPTURE_DIR" ] && mkdir -p "$CAPTURE_DIR"
PASS=0; FAIL=0

green() { printf '\033[32m%s\033[0m' "$*"; }
red()   { printf '\033[31m%s\033[0m' "$*"; }
title() { printf '\n\033[1m%s\033[0m\n' "$*"; }
check() {   # check "<description>" <command...>
    local desc="$1"; shift
    if "$@" >/dev/null 2>&1; then echo "  $(green PASS) $desc"; PASS=$((PASS+1))
    else echo "  $(red FAIL) $desc"; FAIL=$((FAIL+1)); fi
}
# run <name> <command line>: shows the command and its output, saves both.
run() {
    local name="$1"; shift
    local out; out="$(eval "$*" 2>&1)"
    printf '$ %s\n%s\n' "$*" "$out"
    [ -n "$CAPTURE_DIR" ] && printf '$ %s\n%s\n' "$*" "$out" > "$CAPTURE_DIR/$name.txt"
    LAST="$out"
}
http() {    # http <method> <url> [json] -> sets CODE and BODY
    local resp
    resp="$(curl -s -m 10 -w '\n%{http_code}' -X "$1" "$2" -H 'Content-Type: application/json' ${3:+-d "$3"})"
    CODE="${resp##*$'\n'}"; BODY="${resp%$'\n'*}"
}
orders() {
    kubectl exec pods/billing-db-0 -- sudo -i -u postgres psql -d "${BILLING_DB_NAME:-billing_db}" -tAc "SELECT user_id FROM orders;"
}
# Counts, not presence, so the script can be re-run before every audit.
count()     { orders | grep -cx "$1"; }
is_count()  { [ "$(count "$1")" -eq "$2" ]; }
contains()  { grep -q -- "$2" <<<"$1"; }

title "Cluster"
run nodes "kubectl get nodes -A"
check "two nodes"                     test "$(kubectl get nodes --no-headers | wc -l | tr -d ' ')" -eq 2
check "both nodes Ready"              bash -c '! kubectl get nodes --no-headers | grep -v " Ready "'
check "names are master and agent"    bash -c 'kubectl get nodes --no-headers | grep -q "^master " && kubectl get nodes --no-headers | grep -q "^agent "'

title "Deployed resources"
run all "kubectl get all"
for d in api-gateway-app inventory-app rabbit-queue; do
    check "$d is a Deployment"        kubectl get deployment "$d"
done
for s in billing-app inventory-db billing-db; do
    check "$s is a StatefulSet"       kubectl get statefulset "$s"
done
run hpa "kubectl get hpa"
for h in api-gateway-app inventory-app; do
    check "$h HPA: min 1, max 3, 60% CPU" bash -c "[ \"\$(kubectl get hpa $h -o jsonpath='{.spec.minReplicas}/{.spec.maxReplicas}/{.spec.metrics[0].resource.target.averageUtilization}')\" = 1/3/60 ]"
done
run pvc "kubectl get pvc,pv"
check "database PVCs Bound"           bash -c '[ "$(kubectl get pvc --no-headers | grep -c Bound)" -eq 2 ]'
check "service ports 5432/5432/8080/8080/3000" bash -c '
    [ "$(kubectl get svc inventory-db -o jsonpath={.spec.ports[0].port})" = 5432 ] &&
    [ "$(kubectl get svc billing-db -o jsonpath={.spec.ports[0].port})" = 5432 ] &&
    [ "$(kubectl get svc inventory-app -o jsonpath={.spec.ports[0].port})" = 8080 ] &&
    [ "$(kubectl get svc billing-app -o jsonpath={.spec.ports[0].port})" = 8080 ] &&
    [ "$(kubectl get svc api-gateway-app -o jsonpath={.spec.ports[0].port})" = 3000 ]'

title "Images and secrets"
run images "kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.spec.containers[0].image}{\"\\n\"}{end}'"
check "every image is from Docker Hub user ${DOCKERHUB_USERNAME:-?}" bash -c "! kubectl get pods -o jsonpath='{range .items[*]}{.spec.containers[*].image}{\"\\n\"}{end}' | tr ' ' '\\n' | grep -v '^${DOCKERHUB_USERNAME:-x}/'"
run secrets "kubectl get secrets"
check "3 secrets exist"               bash -c '[ "$(kubectl get secrets --no-headers | grep -c Opaque)" -eq 3 ]'
check "no credentials in Manifests/"  bash -c '! grep -rniE "(password|passwd|pass)[[:space:]]*:[[:space:]]*[^ {]" Manifests/'

title "Inventory API"
http POST "$GATEWAY/api/movies/" '{"title": "A new movie", "description": "Very short description"}'
echo "  POST /api/movies/ -> $CODE $BODY"; [ -n "$CAPTURE_DIR" ] && printf '$ curl -X POST %s/api/movies/ -d %s\nHTTP %s\n%s\n' "$GATEWAY" "'{\"title\": \"A new movie\", \"description\": \"Very short description\"}'" "$CODE" "$BODY" > "$CAPTURE_DIR/movies-post.txt"
check "POST /api/movies/ returns 201" test "$CODE" = 201
http GET "$GATEWAY/api/movies/"
echo "  GET /api/movies/ -> $CODE $BODY"; [ -n "$CAPTURE_DIR" ] && printf '$ curl %s/api/movies/\nHTTP %s\n%s\n' "$GATEWAY" "$CODE" "$BODY" > "$CAPTURE_DIR/movies-get.txt"
check "GET /api/movies/ returns 200"  test "$CODE" = 200
check "GET returns the new movie as JSON" contains "$BODY" '"title":"A new movie"'

title "Billing API and queue resilience"
N20="$(count 20)"; N22="$(count 22)"
http POST "$GATEWAY/api/billing/" '{"user_id": "20", "number_of_items": "99", "total_amount": "250"}'
echo "  POST /api/billing/ (user 20) -> $CODE $BODY"
check "POST /api/billing/ returns 200" test "$CODE" = 200
# Let billing-app store order 20 before stopping it, as a human auditor would.
for i in $(seq 1 15); do is_count 20 $((N20 + 1)) && break; sleep 2; done
run stop-billing "kubectl scale statefulset billing-app --replicas=0 && kubectl wait --for=delete pod/billing-app-0 --timeout=60s; kubectl get statefulset billing-app"
check "billing-app stopped (0 pods)"  bash -c '! kubectl get pod billing-app-0'
http POST "$GATEWAY/api/billing/" '{"user_id": "22", "number_of_items": "10", "total_amount": "50"}'
echo "  POST /api/billing/ (user 22, billing-app down) -> $CODE $BODY"
[ -n "$CAPTURE_DIR" ] && printf '$ curl -X POST %s/api/billing/ -d %s\nHTTP %s\n%s\n' "$GATEWAY" "'{\"user_id\": \"22\", \"number_of_items\": \"10\", \"total_amount\": \"50\"}'" "$CODE" "$BODY" > "$CAPTURE_DIR/billing-post-down.txt"
check "POST returns 200 while billing-app is down" test "$CODE" = 200
run db-list "kubectl exec pods/billing-db-0 -- sudo -i -u postgres psql -c '\\l'"
check "billing database is listed"    contains "$LAST" "${BILLING_DB_NAME:-billing_db}"
run orders-before "kubectl exec pods/billing-db-0 -- sudo -i -u postgres psql -d ${BILLING_DB_NAME:-billing_db} -c 'TABLE orders;'"
check "order user_id=20 is listed"    is_count 20 $((N20 + 1))
check "order user_id=22 is NOT listed" is_count 22 "$N22"
run start-billing "kubectl scale statefulset billing-app --replicas=1 && kubectl wait --for=condition=Ready pod/billing-app-0 --timeout=120s; kubectl get statefulset billing-app"
check "billing-app started"           kubectl wait --for=condition=Ready pod/billing-app-0 --timeout=5s
for i in $(seq 1 15); do is_count 22 $((N22 + 1)) && break; sleep 2; done
run orders-after "kubectl exec pods/billing-db-0 -- sudo -i -u postgres psql -d ${BILLING_DB_NAME:-billing_db} -c 'TABLE orders;'"
check "order user_id=22 is now listed" is_count 22 $((N22 + 1))

title "Result"
echo "  $(green "$PASS passed"), $( [ "$FAIL" -eq 0 ] && echo 0 failed || red "$FAIL failed")"
[ "$FAIL" -eq 0 ]
