#!/bin/bash

set -e

# ----------- CONFIGURATION ----------
OUTPUT_DIR="outputs"
FINAL_CSV="final_all.csv"
KEEP_ZIPS=false
PYTHON_SCRIPT="coleta_dados.py"
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
        curl -s -L -o "$FILENAME" "$url"
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
    if unzip -q "$zipfile" -d "$DEST"; then
        echo "[INFO] Successfully unzipped $zipfile"
        $KEEP_ZIPS || rm "$zipfile"
    else
        echo "[WARN] Failed to unzip $zipfile — skipping"
    fi
    $KEEP_ZIPS || rm -f "$zipfile" 
done

# Step 3: Process folders with Python
echo "[INFO] Executando script Python para processar resultados..."

if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 não encontrado no sistema."
    exit 1
fi

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "[ERROR] Script Python '$PYTHON_SCRIPT' não encontrado no diretório atual."
    exit 1
fi

python3 "$PYTHON_SCRIPT" "$OUTPUT_DIR"

echo "[INFO] CSV final gerado: $OUTPUT_DIR/$FINAL_CSV"
