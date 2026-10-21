#!/usr/bin/env bash
# Re-fetch compaction prompts and serialization code from upstream into evidence/.
#
# These files change fast. Run this before trusting any file:line reference in the analysis,
# then diff against the committed snapshots to see what moved.
#
# Requires: gh (authenticated).
#
# Usage:  ./refresh.sh            # fetch from default branch, update PROVENANCE.md
#         ./refresh.sh --check    # fetch to temp and diff only, do not overwrite

set -euo pipefail
cd "$(dirname "$0")"

CHECK=0
[[ "${1:-}" == "--check" ]] && CHECK=1

OUT="."
[[ $CHECK -eq 1 ]] && OUT="$(mktemp -d)"

# repo|path|outfile|sed-range (empty = whole file)
TARGETS=(
  "openai/codex|codex-rs/prompts/templates/compact/prompt.md|codex-compact-prompt.md|"
  "aaif-goose/goose|crates/goose-context-management/src/prompts/compaction.md|goose-compaction.md|"
  "aaif-goose/goose|crates/goose-context-management/src/prompts/compaction_summary.md|goose-compaction-summary.md|"
  "aaif-goose/goose|crates/goose-context-management/src/format.rs|goose-format.rs|"
  "google-gemini/gemini-cli|packages/core/src/prompts/snippets.ts|gemini-cli-compression-prompt.ts|885,1010"
  "earendil-works/pi|packages/coding-agent/src/core/compaction/compaction.ts|pi-summarization-prompts.ts|467,537"
  "earendil-works/pi|packages/coding-agent/src/core/compaction/utils.ts|pi-serialize-conversation.ts|101,158"
)

fetch() {
  gh api "repos/$1/contents/$2" --jq '.content' | base64 -d
}

pin() {
  gh api "repos/$1/commits?path=$2&per_page=1" \
    --jq '"\(.[0].sha[0:12]) \(.[0].commit.committer.date)"'
}

{
  echo "# Provenance"
  echo
  echo "Upstream sources for everything in \`evidence/\`, pinned to the commit that last touched each"
  echo "file. Regenerate with \`./refresh.sh\`."
  echo
  echo "Snapshot taken: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "| Repo | Path | Commit | Last modified | Evidence file |"
  echo "| --- | --- | --- | --- | --- |"
} >"$OUT/PROVENANCE.md.tmp"

for t in "${TARGETS[@]}"; do
  IFS='|' read -r repo path out range <<<"$t"
  echo "fetching $repo :: $path" >&2

  if [[ -n "$range" ]]; then
    fetch "$repo" "$path" | sed -n "${range}p" >"$OUT/$out"
  else
    fetch "$repo" "$path" >"$OUT/$out"
  fi

  read -r sha date <<<"$(pin "$repo" "$path")"
  echo "| $repo | \`$path\` | \`$sha\` | $date | [\`$out\`]($out) |" >>"$OUT/PROVENANCE.md.tmp"
done

{
  echo
  echo "Ranged extracts (\`gemini-cli-*\`, \`pi-*\`) are line slices of a larger file — line numbers"
  echo "drift on every upstream edit. Re-run this script rather than trusting a stale range."
} >>"$OUT/PROVENANCE.md.tmp"

mv "$OUT/PROVENANCE.md.tmp" "$OUT/PROVENANCE.md"

if [[ $CHECK -eq 1 ]]; then
  echo "--- diff vs committed snapshots ---" >&2
  diff -ru --exclude=PROVENANCE.md --exclude=refresh.sh . "$OUT" || true
  echo "(temp: $OUT)" >&2
else
  echo "done — evidence/ and PROVENANCE.md updated" >&2
fi
