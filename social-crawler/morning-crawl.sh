#!/bin/bash
# Morning crawl script - runs at 10:40 via system crontab
# Starts Chrome CDP, crawls 19 brands, saves raw data

LOGFILE=/tmp/tea-morning-crawl.log
exec >> "$LOGFILE" 2>&1
echo "=== Morning crawl starting at $(date) ==="

# Step 1: Start Chrome CDP if not already running
if ! curl -sf http://localhost:9333/json/version > /dev/null 2>&1; then
  echo "Starting Chrome CDP on port 9333..."
  /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=9333 \
    --no-first-run \
    --no-default-browser-check \
    --user-data-dir=/tmp/chrome-debug-profile \
    &>/tmp/chrome-startup.log &
  
  # Wait for CDP to be ready (up to 60s)
  for i in {1..30}; do
    if curl -sf http://localhost:9333/json/version > /dev/null 2>&1; then
      echo "Chrome CDP ready after ${i}s"
      break
    fi
    sleep 2
  done
else
  echo "Chrome CDP already running"
fi

# Verify CDP
if ! curl -sf http://localhost:9333/json/version > /dev/null 2>&1; then
  echo "ERROR: Chrome CDP not available after 60s"
  exit 1
fi

# Step 2: Run crawl
cd /Users/yifansmacmini/.openclaw/workspace/social-crawler
echo "Starting crawl..."
/opt/homebrew/bin/node crawl-today-and-save.mjs
EXIT_CODE=$?
echo "Crawl completed with exit code $EXIT_CODE"

# Check that JSON was saved
if [ -f /tmp/tea-raw-2026-06-14.json ]; then
  echo "Raw data saved to /tmp/tea-raw-2026-06-14.json"
fi

echo "=== Morning crawl finished at $(date) ==="
exit $EXIT_CODE
