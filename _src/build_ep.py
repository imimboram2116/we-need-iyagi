#!/usr/bin/env python3
"""회차 대본 페이지(ep/<번호>.html)를 만든다.

입력: _src/episodes.json(회차 정보) + 각 회차의 풀대본 마크다운.
디자인 틀은 Stitch 시안(2026-10-02)의 색·글꼴·간격만 가져왔다. 내용은 전부 실제 파일에서 채운다.

사용: python3 _src/build_ep.py 18
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANNEL = "https://www.youtube.com/channel/UCRQXu1PqRn_JZzDO_Os9jNA"
SPEAKER_CHIP = {
    "세영": "diamond-chip bg-primary/10 text-primary",
    "혜진": "rounded-full bg-tertiary/15 text-tertiary",
    "보람": "rounded-sm bg-[#e8dec1] text-[#5b4910]",
}


def secs(t):
    parts = [int(p) for p in t.split(":")]
    s = 0
    for p in parts:
        s = s * 60 + p
    return s


def yt(vid, t):
    return f"https://youtu.be/{vid}?t={secs(t)}"


def inline(text):
    """발언 한 줄을 HTML로. 굵게·따옴표 처리와 받아쓰기 표시를 흐리게."""
    s = html.escape(text, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"「(.+?)」", r"<span class='font-semibold'>「\1」</span>", s)
    s = s.replace("(화자 확인 필요)", "<span class='mark-note' title='화자분리 라벨이 문맥과 안 맞아 보이는 곳'>(화자 확인 필요)</span>")
    s = s.replace("(?)", "<span class='mark-note' title='받아쓰기가 불확실한 곳'>(?)</span>")
    return s


def parse(md):
    """풀대본 → (구간 목록, 교정 노트 마크다운). 구간 = {time, title, lines:[(화자, 문장)]}"""
    body, _, notes = md.partition("\n## 교정 노트")
    sections = []
    for line in body.splitlines():
        m = re.match(r"^## \[(\d+:\d{2}(?::\d{2})?)\] (.+)$", line)
        if m:
            sections.append({"time": m.group(1), "title": m.group(2), "lines": []})
            continue
        m = re.match(r"^\*\*(세영|혜진|보람):\*\* (.+)$", line)
        if m and sections:
            sections[-1]["lines"].append((m.group(1), m.group(2)))
    return sections, ("## 교정 노트" + notes) if notes else ""


def md_to_html(md):
    r = subprocess.run(["npx", "-y", "marked", "--gfm"], input=md, capture_output=True, text=True, check=True)
    return r.stdout


def sidebar(eps, current):
    """왼쪽 회차 목록. 접힌 상태에선 회차 번호만, 마우스를 올리면 질문(없으면 제목)까지 펼친다."""
    items = []
    for e in sorted(eps, key=lambda x: -x["ep"]):
        text = html.escape(e.get("main_question") or e["title"])
        num = f"<span class='w-10 shrink-0 text-center font-timestamp-num text-timestamp-num'>{e['ep']}</span>"
        label = f"<span class='side-label line-clamp-2 leading-snug min-w-[13rem]'>{text}</span>"
        if e["ep"] == current:
            items.append(f"<li><span class='flex items-center gap-space-sm h-14 px-2 rounded-md bg-primary/10 text-primary font-semibold' aria-current='page'>{num}{label}</span></li>")
        elif e.get("transcript"):
            items.append(f"<li><a class='flex items-center gap-space-sm h-14 px-2 rounded-md hover:bg-surface-container' href='{e['ep']}.html'>{num}{label}</a></li>")
        else:
            items.append(f"<li><span class='flex items-center gap-space-sm h-14 px-2 text-outline' title='대본 준비 중'>{num}{label}</span></li>")
    return "\n".join(items)


def render(ep, sections, notes_html, prev_ep, next_ep, eps):
    vid = ep["youtube_id"]
    ep_label = f"Ep{ep['ep']}"
    toc = "\n".join(
        f"<li><a class='flex gap-space-sm hover:text-primary' href='#s{i}'>"
        f"<span class='font-timestamp-num text-timestamp-num text-secondary w-12 shrink-0'>{s['time']}</span>"
        f"<span>{html.escape(s['title'])}</span></a></li>"
        for i, s in enumerate(sections)
    )
    blocks = []
    for i, s in enumerate(sections):
        blocks.append(
            f"<section id='s{i}' class='scroll-mt-24 flex flex-col gap-space-lg'>"
            f"<div class='flex items-baseline justify-between gap-space-sm border-b border-outline-variant/40 pb-space-xs'>"
            f"<h2 class='font-headline-sm text-headline-sm font-bold text-on-surface'>{html.escape(s['title'])}</h2>"
            f"<a class='ts font-timestamp-num text-timestamp-num text-secondary hover:text-primary flex items-center gap-0.5 shrink-0' data-t='{secs(s['time'])}' "
            f"href='{yt(vid, s['time'])}' target='_blank' rel='noopener noreferrer' title='이 장면부터 재생'>"
            f"{s['time']}<span class='material-symbols-outlined text-[13px]'>arrow_outward</span></a></div>"
        )
        for who, text in s["lines"]:
            blocks.append(
                "<article class='flex flex-col gap-space-xs'>"
                "<div class='flex items-center gap-space-sm'>"
                f"<span class='w-6 h-6 {SPEAKER_CHIP[who]} text-xs flex items-center justify-center font-bold'><span>{who[0]}</span></span>"
                f"<span class='font-speaker-title text-speaker-title text-on-surface'>{who}</span></div>"
                f"<p class='pl-space-lg font-body-md text-body-md text-on-surface'>{inline(text)}</p></article>"
            )
        blocks.append("</section>")

    def nav(e, label, align):
        arrow_l = "<span class='material-symbols-outlined text-sm'>west</span>" if align == "left" else ""
        arrow_r = "<span class='material-symbols-outlined text-sm'>east</span>" if align == "right" else ""
        cls = "text-right items-end" if align == "right" else ""
        if not e or not e.get("transcript"):
            sub = f" (Ep{e['ep']})" if e else ""
            return f"<div class='flex-1 p-space-md bg-surface-container-low rounded-lg flex flex-col {cls} text-outline'><span class='font-label-sm text-label-sm'>{label}{sub}</span><span class='text-sm mt-2'>대본 준비 중</span></div>"
        return (
            f"<a class='flex-1 p-space-md bg-surface-container-low hover:bg-surface-container rounded-lg flex flex-col {cls}' href='{e['ep']}.html'>"
            f"<span class='flex items-center gap-1 font-label-sm text-label-sm text-secondary'>{arrow_l}{label} (Ep{e['ep']}){arrow_r}</span>"
            f"<span class='font-headline-sm text-sm text-on-surface font-semibold mt-2'>{html.escape(e.get('main_question') or e['title'])}</span></a>"
        )

    works = " · ".join(html.escape(w) for w in ep["works"])
    est = " <span class='text-outline'>(회차 번호 추정)</span>" if ep.get("ep_estimated") else ""
    return TEMPLATE.format(
        ep_label=ep_label,
        title=html.escape(ep["title"]),
        main_question=html.escape(ep["main_question"]),
        q_time=ep["question_time"],
        q_url=yt(vid, ep["question_time"]),
        q_secs=secs(ep["question_time"]),
        q_note=html.escape(ep["question_note"]),
        est=est,
        uploaded=ep["uploaded"].replace("-", "."),
        duration=ep["duration"],
        cast=" · ".join(ep["cast"]),
        works=works,
        video=f"https://youtu.be/{vid}",
        vid=vid,
        channel=CHANNEL,
        toc=toc,
        n_sections=len(sections),
        transcript="\n".join(blocks),
        notes=notes_html,
        prev=nav(prev_ep, "이전 회차", "left"),
        next=nav(next_ep, "다음 회차", "right"),
        sidebar=sidebar(eps, ep["ep"]),
    )


TEMPLATE = """<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ep_label} {title} — 이야기가 필요해 대본집</title>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Noto+Serif+KR:wght@400;600;700&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config={{theme:{{extend:{{
colors:{{"primary":"#973313","primary-container":"#b84a29","primary-fixed":"#ffdbd1","tertiary":"#005c76","surface":"#fcf9f3","surface-container-low":"#f6f3ed","surface-container":"#f0eee8","surface-container-high":"#ebe8e2","on-surface":"#1c1c18","on-surface-variant":"#57423c","secondary":"#615e5a","outline":"#8b716b","outline-variant":"#dec0b8"}},
spacing:{{"margin":"1.25rem","margin-tablet":"2.5rem","space-xs":"0.25rem","space-sm":"0.5rem","space-md":"1rem","space-lg":"1.75rem","space-xl":"3rem"}},
fontFamily:{{"headline-hero":["Noto Serif KR","serif"],"headline-sm":["Noto Serif KR","serif"],"speaker-title":["Noto Serif KR","serif"],"body-md":["Pretendard Variable","Pretendard","sans-serif"],"label-sm":["Manrope","sans-serif"],"label-md":["Manrope","sans-serif"],"timestamp-num":["Manrope","sans-serif"]}},
fontSize:{{"headline-hero":["2.5rem",{{lineHeight:"3.5rem",letterSpacing:"-0.02em",fontWeight:"700"}}],"headline-hero-mobile":["1.75rem",{{lineHeight:"2.625rem",fontWeight:"700"}}],"headline-sm":["1.25rem",{{lineHeight:"1.875rem",fontWeight:"600"}}],"speaker-title":["0.9375rem",{{lineHeight:"1.375rem",fontWeight:"700"}}],"body-md":["1.0625rem",{{lineHeight:"1.875rem"}}],"label-sm":["0.75rem",{{lineHeight:"1rem",letterSpacing:"0.05em",fontWeight:"500"}}],"label-md":["0.8125rem",{{lineHeight:"1.125rem",fontWeight:"500"}}],"timestamp-num":["0.8125rem",{{lineHeight:"1.125rem",letterSpacing:"0.06em",fontWeight:"600"}}]}}
}}}}}}</script>
<style>
#ep-side{{width:3.5rem}} #ep-side .side-label{{opacity:0;transition:opacity .15s}}
#ep-side:hover,#ep-side.open{{width:18rem;box-shadow:4px 0 16px rgba(0,0,0,.06)}} #ep-side:hover .side-label,#ep-side.open .side-label{{opacity:1}}
@media (max-width:767px){{#ep-side{{display:none}} #ep-side.open{{display:block}}}}
.diamond-chip{{border-radius:2px;transform:rotate(45deg) scale(.95)}} .diamond-chip>span{{transform:rotate(-45deg) scale(1.05)}}
::selection{{background:#e6dccb;color:inherit}}
.mark-note{{color:#8b716b;font-size:.8em}} .notes table{{display:block;overflow-x:auto;font-size:.85rem;margin:.75rem 0}} .notes td,.notes th{{border:1px solid #dec0b8;padding:4px 8px;vertical-align:top}} .notes h2,.notes h3{{font-weight:700;margin:1rem 0 .5rem}} .notes ul{{list-style:disc;padding-left:1.25rem}} .notes p{{margin:.5rem 0}}</style>
</head>
<body class="bg-surface text-on-surface antialiased font-body-md md:pl-14 xl:pr-[380px]">
<header class="sticky top-0 z-50 bg-surface/90 backdrop-blur-md shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
<div class="h-14 max-w-[45rem] mx-auto px-margin md:px-margin-tablet flex items-center justify-between">
<a class="font-headline-sm text-headline-sm hover:text-primary" href="../">&lt;이야기가 필요해&gt;</a>
<nav class="flex items-center gap-space-md font-label-md text-label-md text-on-surface-variant">
<button type="button" class="hover:text-on-surface md:hidden" onclick="document.getElementById('ep-side').classList.toggle('open')">회차 목록</button>
<a class="hover:text-on-surface hidden md:inline" href="../docs.html">전체 문서</a>
<a class="hover:text-on-surface" href="{channel}" target="_blank" rel="noopener noreferrer">유튜브</a></nav></div></header>

<aside id="ep-side" class="fixed left-0 top-14 bottom-0 z-40 bg-surface-container-low overflow-hidden transition-all duration-200">
<div class="px-2 pt-space-md pb-space-sm font-label-sm text-label-sm text-secondary flex items-center gap-space-sm"><span class="w-10 text-center material-symbols-outlined text-[18px]">menu_book</span><span class="side-label">회차 목록</span></div>
<ul class="px-1 flex flex-col gap-0.5 text-sm overflow-y-auto h-full pb-24">{sidebar}</ul></aside>
<main class="max-w-[45rem] mx-auto px-margin md:px-margin-tablet py-space-xl">
<div class="flex items-center justify-between flex-wrap gap-space-sm font-label-sm text-label-sm text-secondary">
<div class="flex items-center gap-space-xs tracking-wider"><span class="text-primary font-semibold">{ep_label}</span>{est}<span>·</span><span>{uploaded}</span><span>·</span><span class="font-timestamp-num">{duration}</span></div>
<a class="flex items-center gap-1 text-primary font-semibold" href="{video}" target="_blank" rel="noopener noreferrer"><span class="material-symbols-outlined text-[17px]">play_circle</span>전체 영상 보기</a></div>

<section class="my-space-xl flex flex-col items-center text-center">
<div class="w-8 h-0.5 bg-primary mb-space-md opacity-80"></div>
<span class="font-label-sm text-label-sm tracking-widest text-primary font-semibold mb-space-sm">오늘의 질문</span>
<h1 class="font-headline-hero text-headline-hero-mobile sm:text-headline-hero max-w-[42rem]"><span class="text-outline-variant mr-1">“</span>{main_question}<span class="text-outline-variant ml-1">”</span></h1>
<div class="w-8 h-0.5 bg-outline-variant mt-space-md"></div></section>

<div class="flex flex-col gap-space-sm">
<div class="bg-surface-container-low px-5 py-4 rounded-lg text-[15px] leading-6 text-on-surface-variant flex flex-col gap-1.5">
<div><span class="font-semibold text-on-surface">함께 나눈 콘텐츠</span> — {works}</div>
<div><span class="font-semibold text-on-surface">대화하는 사람들</span> — {cast}</div></div></div>

<details class="xl:hidden my-space-lg bg-surface-container-low rounded-lg px-space-md py-space-sm">
<summary class="cursor-pointer font-label-md text-label-md font-semibold">목차 · {n_sections}개 구간</summary>
<ol class="mt-space-sm flex flex-col gap-space-sm text-sm">{toc}</ol></details>

<div class="flex flex-col gap-space-xl my-space-xl">{transcript}</div>

<details class="notes my-space-xl bg-surface-container-low rounded-lg px-space-md py-space-sm text-on-surface-variant">
<summary class="cursor-pointer font-label-md text-label-md font-semibold">받아쓰기 교정 노트</summary>
<div class="mt-space-sm">{notes}</div></details>

<nav class="flex flex-col sm:flex-row gap-space-md my-space-lg">{prev}{next}</nav>
<div class="text-center my-space-lg"><a class="font-label-md text-label-md text-secondary hover:text-primary" href="../">← 회차 목록으로</a></div>
</main>
<footer class="bg-surface-container-low mt-space-xl"><div class="max-w-[45rem] mx-auto px-margin md:px-margin-tablet py-space-xl flex flex-col gap-space-xs">
<span class="font-headline-sm text-headline-sm">&lt;이야기가 필요해&gt;</span>
<p class="text-sm text-secondary">살다 보면 마음에 남는 질문이 있습니다. 그 질문에 콘텐츠로 답해보는 팟캐스트.</p>
<a class="font-label-md text-label-md text-on-surface-variant hover:text-primary" href="{channel}" target="_blank" rel="noopener noreferrer">YouTube</a></div></footer>
<div class="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 xl:top-20 z-50 w-[300px] sm:w-[340px] flex flex-col justify-end gap-3 pointer-events-none">
<nav aria-label="목차" class="hidden xl:flex flex-col min-h-0 pointer-events-auto">
<div class="px-1 pb-2 font-label-sm text-label-sm text-secondary font-semibold">목차 · {n_sections}개 구간</div>
<ol class="px-1 flex flex-col gap-2 text-sm text-on-surface-variant overflow-y-auto min-h-0">{toc}</ol></nav>
<aside id="pip" class="pointer-events-auto shrink-0 bg-white rounded-xl shadow-xl border border-outline-variant/40 overflow-hidden">
<div class="px-3 py-2 bg-surface-container flex items-center justify-between select-none">
<div class="flex items-center gap-1.5 min-w-0"><span class="w-2 h-2 rounded-full bg-primary shrink-0"></span><span class="font-label-sm text-[12px] font-semibold truncate">{ep_label} 전체 영상</span><span class="font-timestamp-num text-[11px] text-secondary shrink-0">{duration}</span></div>
<div class="flex items-center gap-1 shrink-0">
<a href="{video}" target="_blank" rel="noopener noreferrer" title="유튜브에서 열기" class="text-secondary hover:text-primary p-0.5"><span class="material-symbols-outlined text-[16px]">open_in_new</span></a>
<button type="button" id="pip-toggle" title="플레이어 접기/펼치기" class="text-secondary hover:text-on-surface p-0.5"><span class="material-symbols-outlined text-[16px]" id="pip-icon">expand_more</span></button>
<button type="button" onclick="document.getElementById('pip').style.display='none'" title="플레이어 닫기" class="text-secondary hover:text-primary p-0.5"><span class="material-symbols-outlined text-[16px]">close</span></button></div></div>
<div id="pip-body" class="relative w-full aspect-video bg-black"><iframe class="absolute inset-0 w-full h-full border-0" id="pip-frame" src="https://www.youtube.com/embed/{vid}?rel=0&enablejsapi=1" title="{ep_label} 영상" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe></div></aside></div>
<script>
(function(){{
  var body=document.getElementById('pip-body'), icon=document.getElementById('pip-icon');
  function set(open){{ body.style.display=open?'':'none'; icon.textContent=open?'expand_more':'expand_less'; }}
  // 휴대폰에선 본문을 가리지 않게 접힌 채로 시작
  set(window.innerWidth>=768);
  document.getElementById('pip-toggle').onclick=function(){{ set(body.style.display==='none'); }};
  // 시각을 누르면 새 창 대신 미니 플레이어를 그 장면으로 옮긴다. 플레이어가 준비 안 됐으면 원래 링크(유튜브)로 간다.
  var player=null;
  window.onYouTubeIframeAPIReady=function(){{ player=new YT.Player('pip-frame'); }};
  var tag=document.createElement('script'); tag.src='https://www.youtube.com/iframe_api'; document.head.appendChild(tag);
  document.addEventListener('click',function(e){{
    var a=e.target.closest('a.ts'); if(!a||!player||!player.seekTo) return;
    e.preventDefault();
    document.getElementById('pip').style.display=''; set(true);
    player.seekTo(Number(a.dataset.t),true); player.playVideo();
  }});
}})();
</script>
</body></html>
"""


def main():
    n = int(sys.argv[1])
    eps = sorted(json.loads((ROOT / "_src/episodes.json").read_text(encoding="utf-8")), key=lambda e: e["ep"])
    idx = next(i for i, e in enumerate(eps) if e["ep"] == n)
    ep = eps[idx]
    prev_ep = eps[idx - 1] if idx > 0 else None
    next_ep = eps[idx + 1] if idx + 1 < len(eps) else None
    sections, notes_md = parse((ROOT / ep["transcript"]).read_text(encoding="utf-8"))
    # 사이트에 보일 구간 제목만 바꿀 때 (원본 풀대본은 그대로 둔다)
    for sec in sections:
        sec["title"] = ep.get("section_titles", {}).get(sec["time"], sec["title"])
    out = ROOT / "ep" / f"{n}.html"
    out.write_text(render(ep, sections, md_to_html(notes_md), prev_ep, next_ep, eps), encoding="utf-8")
    print(f"{out} — 구간 {len(sections)}개, 발언 {sum(len(s['lines']) for s in sections)}개")


if __name__ == "__main__":
    main()
