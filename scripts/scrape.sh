#!/bin/bash
# Usage: scrape.sh <outdir> <results_per_term> <max_usd> "term 1" "term 2" ...
# Runs the Apify actor clockworks~tiktok-scraper on TikTok search (US proxy, no media downloads),
# waits for it to finish and saves the posts to <outdir>/main.json.
# Token: $APIFY_TOKEN, or the first key in $APIFY_TOKENS_FILE (default ~/.apify_tokens.txt)
# that still has at least <max_usd> of monthly credit left.
set -e
PY=${PYTHON:-python3}
OUT=$1; PER=$2; USD=$3; shift 3
mkdir -p "$OUT"
TOKENS_FILE=${APIFY_TOKENS_FILE:-$HOME/.apify_tokens.txt}
pick() {
  local list=$APIFY_TOKEN
  [ -z "$list" ] && [ -f "$TOKENS_FILE" ] && list=$(grep -oE 'apify_api_[A-Za-z0-9]+' "$TOKENS_FILE")
  for T in $list; do
    left=$(curl -s "https://api.apify.com/v2/users/me/limits?token=$T" | $PY -c "import json,sys
d=json.load(sys.stdin).get('data') or {}
print(round((d.get('limits',{}).get('maxMonthlyUsageUsd') or 0)-(d.get('current',{}).get('monthlyUsageUsd') or 0),2))" 2>/dev/null || echo 0)
    if $PY -c "import sys; sys.exit(0 if float('$left')>=float('$USD') else 1)"; then echo "$T"; return; fi
  done
}
T=$(pick); [ -z "$T" ] && { echo "No Apify token with \$$USD of credit left. Set APIFY_TOKEN or APIFY_TOKENS_FILE."; exit 1; }
echo "token ...${T: -4}"
Q=$($PY -c "import json,sys; print(json.dumps(sys.argv[1:]))" "$@")
BODY="{\"searchQueries\":$Q,\"searchSection\":\"\",\"resultsPerPage\":$PER,\"shouldDownloadVideos\":false,\"shouldDownloadCovers\":false,\"shouldDownloadSlideshowImages\":false,\"proxyCountryCode\":\"US\"}"
read RUN DS < <(curl -s -X POST "https://api.apify.com/v2/acts/clockworks~tiktok-scraper/runs?token=$T&maxTotalChargeUsd=$USD" -H 'Content-Type: application/json' -d "$BODY" | $PY -c "import json,sys; d=json.load(sys.stdin)['data']; print(d['id'], d['defaultDatasetId'])")
echo "run $RUN"
while :; do
  s=$(curl -s "https://api.apify.com/v2/actor-runs/$RUN?token=$T" | $PY -c "import json,sys; print(json.load(sys.stdin)['data']['status'])")
  [ "$s" != RUNNING ] && [ "$s" != READY ] && break; sleep 20
done
curl -s "https://api.apify.com/v2/datasets/$DS/items?token=$T&clean=1" > "$OUT/main.json"
echo "$s, $($PY -c "import json; print(len(json.load(open('$OUT/main.json'))))") posts saved to $OUT/main.json"
