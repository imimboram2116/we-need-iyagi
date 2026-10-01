#!/bin/bash
# 워크스페이스의 팟캐스트 폴더를 이 사이트 저장소로 복사하고 푸시한다.
# 새 회차 대본을 만든 뒤 `~/Documents/we-need-iyagi/sync.sh` 한 번 실행하면 사이트에 반영된다.
#
# YouTube Studio 전용 지표가 든 문서(PRIVATE)는 원문을 올리지 않고 비밀번호로 암호화한 HTML만 올린다.
# 비밀번호는 맥 키체인에서 읽는다. 처음 한 번 직접 저장:
#   security add-generic-password -s we-need-iyagi-admin -a admin -w
set -e
shopt -s nullglob
SRC="$HOME/Documents/do-better-workspace-v2/20-operations/24-이야기가-필요해-팟캐스트"
DST="$(cd "$(dirname "$0")" && pwd)"
# 확장자 없이, 팟캐스트 폴더 기준 경로
PRIVATE=("릴리즈-분석" "지표-로그" "에피소드-아이디어" "Ep13-15-분석" "scripts/Ep17-코스피특집")

PW=$(security find-generic-password -s we-need-iyagi-admin -w 2>/dev/null) || {
  echo "키체인에 비밀번호가 없다. 먼저 실행: security add-generic-password -s we-need-iyagi-admin -a admin -w"
  exit 1
}

EXCLUDES=(--exclude '.git' --exclude 'sync.sh' --exclude '_config.yml' --exclude 'index.md' --exclude '.staticrypt.json')
for n in "${PRIVATE[@]}"; do EXCLUDES+=(--exclude "/$n.md" --exclude "/$n.html"); done
rsync -a --delete "${EXCLUDES[@]}" "$SRC/" "$DST/"

# 비공개 문서: 마크다운 → HTML → 암호화. 채널 로그인 이메일 줄은 원본에만 남긴다.
TMP=$(mktemp -d)
for n in "${PRIVATE[@]}"; do
  b=$(basename "$n")
  sed '/유튜브 계정:/d' "$SRC/$n.md" > "$TMP/$b.md"
  {
    echo "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>$b</title>"
    echo "<style>body{font-family:-apple-system,sans-serif;max-width:860px;margin:2em auto;padding:0 16px;line-height:1.6}table{border-collapse:collapse;display:block;overflow-x:auto}td,th{border:1px solid #ccc;padding:4px 8px}</style></head><body>"
    npx -y marked --gfm -i "$TMP/$b.md"
    echo "</body></html>"
  } > "$TMP/$b.html"
  (cd "$DST" && npx -y staticrypt "$TMP/$b.html" -p "$PW" --short -d "$TMP/enc" >/dev/null)
  cp "$TMP/enc/$b.html" "$DST/$n.html"
  # 공개 문서 안의 링크가 잠긴 페이지를 가리키게
  find "$DST" -name "*.md" -not -path "*/.git/*" -exec sed -i '' "s|($b.md)|($b.html)|g" {} +
done
rm -rf "$TMP"

# 첫 화면: 폴더별 파일 목록
{
  echo "# 이야기가 필요해"
  echo
  echo "팟캐스트 <이야기가 필요해> 회차별 대본·질문 흐름·운영 기록."
  echo "대본은 자동 받아쓰기를 정리한 것이라 고유명사 오류가 있을 수 있습니다."
  echo
  echo "## 분석·운영"
  echo
  for f in "$DST"/*.md; do n=$(basename "$f"); [ "$n" = index.md ] || echo "- [${n%.md}]($n)"; done
  for n in "${PRIVATE[@]}"; do echo "- [$n]($n.html) (비밀번호 필요)"; done
  for d in scripts transcripts; do
    files=("$DST/$d"/*.md)
    [ ${#files[@]} -gt 0 ] || continue
    echo; echo "## $d"; echo
    for f in "${files[@]}"; do n=$(basename "$f"); echo "- [${n%.md}]($d/$n)"; done
  done
} > "$DST/index.md"

cd "$DST"
git add -A
if git diff --cached --quiet; then echo "바뀐 것 없음"; exit 0; fi
git commit -q -m "Sync podcast folder ($(date +%Y-%m-%d))"
git push -q 2>/dev/null && echo "푸시 완료 — 1~2분 뒤 https://imimboram2116.github.io/we-need-iyagi/ 에 반영" || echo "커밋만 함 — 원격 저장소가 아직 없거나 푸시 실패"
