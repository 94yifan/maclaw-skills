#!/bin/bash
# feishu-doc-write-fix.patch.sh
# 修复 feishu_doc 工具两个导致空白文档的 bug（2026-08-01 逸凡反馈）
# Bug 1: create action 不接受 content，模型把正文塞进 create 会被静默忽略，只建空壳
# Bug 2: writeDoc 先 clearDocumentContent 再 convert markdown，转换失败(400)时文档已被清空 → 空白文档
# 修复: create 支持 content（创建后自动 write）；writeDoc 先 convert 成功再 clear
#
# 用法: bash feishu-doc-write-fix.patch.sh [apply|check|revert]
# OpenClaw 更新后如果插件被重置，重新运行 apply 即可。

API_JS="$HOME/.openclaw/npm/projects/openclaw-feishu-dc69f44688/node_modules/@openclaw/feishu/dist/api.js"
BACKUP="${API_JS}.bak-fix"

apply() {
  [ -f "$API_JS" ] || { echo "ERROR: $API_JS not found"; exit 1; }
  # 已应用则跳过
  if grep -q 'content_written: true' "$API_JS"; then
    echo "Already applied. Nothing to do."
    return 0
  fi
  [ -f "$BACKUP" ] || cp "$API_JS" "$BACKUP"
  echo "Backup saved to $BACKUP"

  python3 - "$API_JS" <<'PYEOF'
import sys

path = sys.argv[1]
with open(path) as f:
    src = f.read()

# --- Fix 1: create schema accepts content ---
old_schema = '''\tType.Object({
\t\taction: Type.Literal("create"),
\t\ttitle: Type.String({ description: "Document title" }),
\t\tfolder_token: Type.Optional(Type.String({ description: "Target folder token (optional)" })),
\t\tgrant_to_requester: Type.Optional(Type.Boolean({ description: "Grant edit permission to the trusted requesting Feishu user from runtime context (default: true)." }))
\t}),'''
new_schema = '''\tType.Object({
\t\taction: Type.Literal("create"),
\t\ttitle: Type.String({ description: "Document title" }),
\t\tfolder_token: Type.Optional(Type.String({ description: "Target folder token (optional)" })),
\t\tgrant_to_requester: Type.Optional(Type.Boolean({ description: "Grant edit permission to the trusted requesting Feishu user from runtime context (default: true)." })),
\t\tcontent: Type.Optional(Type.String({ description: "Markdown content to write immediately after creation (optional). Use this instead of a separate write call. If conversion fails, the document is left empty and an error is returned." }))
\t}),'''
if old_schema in src:
    src = src.replace(old_schema, new_schema)
    print("Fix 1a (schema content) applied")
else:
    print("Fix 1a: pattern not found, skipping (may already be applied)")

# --- Fix 1b: create case passes content ---
old_case = '''case "create": return json$1(await createDoc(client, p.title, p.folder_token, {
\t\t\t\t\t\t\t\tgrantToRequester: p.grant_to_requester,
\t\t\t\t\t\t\t\trequesterOpenId: trustedRequesterOpenId
\t\t\t\t\t\t\t}));'''
new_case = '''case "create": return json$1(await createDoc(client, p.title, p.folder_token, {
\t\t\t\t\t\t\t\tgrantToRequester: p.grant_to_requester,
\t\t\t\t\t\t\t\trequesterOpenId: trustedRequesterOpenId,
\t\t\t\t\t\t\t\tcontent: p.content,
\t\t\t\t\t\t\t\tmaxBytes: getMediaMaxBytes(p, defaultAccountId),
\t\t\t\t\t\t\t\tlogger: api.logger
\t\t\t\t\t\t\t}));'''
if old_case in src:
    src = src.replace(old_case, new_case)
    print("Fix 1b (create case) applied")
else:
    print("Fix 1b: pattern not found, skipping")

# --- Fix 1c: createDoc writes content after creation ---
old_create_doc = '''\treturn {
\t\tdocument_id: docToken,
\t\ttitle: doc?.title,
\t\turl: `https://feishu.cn/docx/${docToken}`,
\t\t...shouldGrantToRequester && {
\t\t\trequester_permission_added: requesterPermissionAdded,
\t\t\t...requesterOpenId && { requester_open_id: requesterOpenId },
\t\t\trequester_perm_type: requesterPermType,
\t\t\t...requesterPermissionSkippedReason && { requester_permission_skipped_reason: requesterPermissionSkippedReason },
\t\t\t...requesterPermissionError && { requester_permission_error: requesterPermissionError }
\t\t}
\t};
}'''
new_create_doc = '''\tconst base = {
\t\tdocument_id: docToken,
\t\ttitle: doc?.title,
\t\turl: `https://feishu.cn/docx/${docToken}`,
\t\t...shouldGrantToRequester && {
\t\t\trequester_permission_added: requesterPermissionAdded,
\t\t\t...requesterOpenId && { requester_open_id: requesterOpenId },
\t\t\trequester_perm_type: requesterPermType,
\t\t\t...requesterPermissionSkippedReason && { requester_permission_skipped_reason: requesterPermissionSkippedReason },
\t\t\t...requesterPermissionError && { requester_permission_error: requesterPermissionError }
\t\t}
\t};
\tif (options?.content) {
\t\ttry {
\t\t\tconst writeResult = await writeDoc(client, docToken, options.content, options.maxBytes, options.logger);
\t\t\treturn {
\t\t\t\t...base,
\t\t\t\tcontent_written: true,
\t\t\t\tblocks_added: writeResult.blocks_added,
\t\t\t\timages_processed: writeResult.images_processed
\t\t\t};
\t\t} catch (err) {
\t\t\treturn {
\t\t\t\t...base,
\t\t\t\tcontent_written: false,
\t\t\t\tcontent_error: formatErrorMessage(err)
\t\t\t};
\t\t}
\t}
\treturn base;
}'''
if old_create_doc in src:
    src = src.replace(old_create_doc, new_create_doc)
    print("Fix 1c (createDoc content) applied")
else:
    print("Fix 1c: pattern not found, skipping")

# --- Fix 2: writeDoc converts first, clears only after success ---
old_write = '''async function writeDoc(client, docToken, markdown, maxBytes, logger) {
\tconst deleted = await clearDocumentContent(client, docToken);
\tlogger?.info?.("feishu_doc: Converting markdown...");
\tconst { blocks, firstLevelBlockIds } = await chunkedConvertMarkdown(client, markdown);
\tif (blocks.length === 0) return {
\t\tsuccess: true,
\t\tblocks_deleted: deleted,
\t\tblocks_added: 0,
\t\timages_processed: 0
\t};
\tlogger?.info?.(`feishu_doc: Converted to ${blocks.length} blocks, inserting...`);'''
new_write = '''async function writeDoc(client, docToken, markdown, maxBytes, logger) {
\tlogger?.info?.("feishu_doc: Converting markdown...");
\tconst { blocks, firstLevelBlockIds } = await chunkedConvertMarkdown(client, markdown);
\tif (blocks.length === 0) return {
\t\tsuccess: true,
\t\tblocks_deleted: 0,
\t\tblocks_added: 0,
\t\timages_processed: 0
\t};
\tconst deleted = await clearDocumentContent(client, docToken);
\tlogger?.info?.(`feishu_doc: Converted to ${blocks.length} blocks, inserting...`);'''
if old_write in src:
    src = src.replace(old_write, new_write)
    print("Fix 2 (writeDoc order) applied")
else:
    print("Fix 2: pattern not found, skipping")

with open(path, 'w') as f:
    f.write(src)
print("Done. Verify with: node --check " + path)
PYEOF
}

check() {
  echo "=== Fix status ==="
  grep -c 'content_written: true' "$API_JS" 2>/dev/null | xargs echo "create-content fix:"
  grep -c 'const deleted = await clearDocumentContent' "$API_JS" 2>/dev/null | xargs echo "writeDoc clear count:"
  node --check "$API_JS" 2>&1 && echo "Syntax: OK"
}

revert() {
  [ -f "$BACKUP" ] && cp "$BACKUP" "$API_JS" && echo "Reverted to backup"
}

case "${1:-check}" in
  apply) apply ;;
  check) check ;;
  revert) revert ;;
  *) echo "Usage: $0 [apply|check|revert]" ;;
esac
