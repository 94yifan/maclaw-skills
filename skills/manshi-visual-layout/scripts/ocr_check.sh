#!/usr/bin/env bash
# 用 macOS Vision（swift）做 OCR，带坐标，用来校验渲染图文字是否漏字/串行/被裁
# 依赖同目录 ocr.swift；用法: ./ocr_check.sh /abs/path/image.png
set -euo pipefail
IMG="${1:?usage: ocr_check.sh <image>}"
SWIFT="$(cd "$(dirname "$0")" && pwd)/ocr.swift"
swift "$SWIFT" "$IMG" 2>/dev/null
