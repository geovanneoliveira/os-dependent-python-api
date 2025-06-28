#!/bin/bash

set -e

# ----------- CONFIGURATION ----------
OUTPUT_DIR="outputs"
FINAL_CSV="final.csv"
KEEP_ZIPS=false
# ------------------------------------

# --- Input validation ---
if [ -z "$1" ]; then
    echo "Usage: $0 <GitHub release URL>"
    echo "Example: $0 https://github.com/mohasarc/os-dependent-python-api/releases/tag/output-2025-06-28-morning-2"
    exit 1
fi

RELEASE_URL="$1"

# Extract owner, repo and tag
if [[ "$RELEASE_URL" =~ github.com/([^/]+)/([^/]+)/releases/tag/(.+) ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    TAG="${BASH_REMATCH[3]}"
else
    echo "Invalid GitHub release URL format."
    exit 1
fi

echo "[INFO] Owner: $OWNER"
echo "[INFO] Repo: $REPO"
echo "[INFO] Tag: $TAG"

# Step 1: Download ZIP assets
echo "[INFO] Fetching release data from GitHub API..."
RELEASE_DATA=$(curl --silent "https://api.github.com/repos/$OWNER/$REPO/releases/tags/$TAG")

if echo "$RELEASE_DATA" | jq -e '.assets | length > 0' >/dev/null; then
    ZIP_URLS=$(echo "$RELEASE_DATA" | jq -r '.assets[].browser_download_url' | grep '\.zip$')

    for url in $ZIP_URLS; do
        FILENAME=$(basename "$url")
        echo "[INFO] Downloading: $FILENAME"
        curl -L -o "$FILENAME" "$url"
    done
else
    echo "[ERROR] No assets found for this release."
    exit 1
fi

# Step 2: Unzip to outputs/
mkdir -p "$OUTPUT_DIR"
for zipfile in *.zip; do
    BASENAME="${zipfile%.zip}"
    DEST="$OUTPUT_DIR/$BASENAME"
    mkdir -p "$DEST"
    echo "[INFO] Unzipping $zipfile into $DEST"
    unzip -q "$zipfile" -d "$DEST"
    $KEEP_ZIPS || rm "$zipfile"
done

# Step 3: Merge CSVs
rm -f "$FINAL_CSV"
first=1

echo "[INFO] Searching for CSVs and merging..."

find "$OUTPUT_DIR" -type f \( -name "macos-latest.csv" -o -name "ubuntu-latest.csv" -o -name "windows-latest.csv" \) | while read -r filepath; do
    if [ "$first" -eq 1 ]; then
        head -n 1 "$filepath" > "$FINAL_CSV"
        first=0
    fi
    tail -n +2 "$filepath" >> "$FINAL_CSV"
done

echo "[INFO] Final CSV generated: $FINAL_CSV"
