#!/usr/bin/env python3
"""첫 화면(질문 아카이브, index.html)을 만든다. 회차별 메인 질문이 주인공.

입력: _src/episodes.json. 디자인은 회차 대본 페이지(build_ep.py)와 같은 머리(head)를 쓴다.
사용: python3 _src/build_home.py
"""
import html
import json
from pathlib import Path

from build_ep import CHANNEL, ROOT, TEMPLATE

HEAD = TEMPLATE.split("<body")[0]


def item(e):
    q = e.get("main_question")
    meta = [f"Ep{e['ep']}"]
    if e.get("uploaded"):
        meta.append(e["uploaded"].replace("-", "."))
    meta_html = " · ".join(meta)
    big = html.escape(q) if q else html.escape(e["title"])
    sub = html.escape(e["title"]) if q else "질문 정리 중"
    extra = " · ".join(html.escape(w) for w in e.get("works", []))
    extra_html = f"<p class='text-sm text-on-surface-variant mt-1'>{extra}</p>" if extra else ""
    if e.get("transcript"):
        return (
            f"<li><a class='group block py-space-lg border-b border-outline-variant/40' href='ep/{e['ep']}.html'>"
            f"<span class='font-label-sm text-label-sm text-primary font-semibold tracking-wider'>{meta_html}</span>"
            f"<h2 class='font-headline-sm text-[1.5rem] leading-9 font-bold mt-2 group-hover:text-primary'>{big}</h2>"
            f"<p class='text-sm text-secondary mt-1'>{sub}</p>{extra_html}"
            f"<span class='inline-flex items-center gap-1 mt-space-sm font-label-md text-label-md text-primary'>대본 읽기"
            f"<span class='material-symbols-outlined text-[16px]'>east</span></span></a></li>"
        )
    return (
        f"<li class='py-space-lg border-b border-outline-variant/40'>"
        f"<span class='font-label-sm text-label-sm text-secondary font-semibold tracking-wider'>{meta_html}</span>"
        f"<h2 class='font-headline-sm text-[1.5rem] leading-9 font-bold mt-2 text-on-surface-variant'>{big}</h2>"
        f"<p class='text-sm text-secondary mt-1'>{sub}</p>"
        f"<span class='inline-flex items-center gap-space-sm mt-space-sm font-label-md text-label-md text-outline'>대본 준비 중 ·"
        f"<a class='inline-flex items-center gap-1 text-on-surface-variant hover:text-primary' href='https://youtu.be/{e['youtube_id']}' target='_blank' rel='noopener noreferrer'>유튜브에서 보기"
        f"<span class='material-symbols-outlined text-[14px]'>arrow_outward</span></a></span></li>"
    )


def main():
    eps = sorted(json.loads((ROOT / "_src/episodes.json").read_text(encoding="utf-8")), key=lambda e: -e["ep"])
    head = HEAD.format(ep_label="", title="질문 아카이브").replace("<title> ", "<title>")
    body = f"""<style>/* 첫 화면은 전부 프리텐다드 (아이콘 글꼴은 제외) */ body *:not(.material-symbols-outlined){{font-family:"Pretendard Variable",Pretendard,sans-serif}}</style>
<body class="bg-surface text-on-surface antialiased font-body-md">
<header class="sticky top-0 z-50 bg-surface/90 backdrop-blur-md shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
<div class="h-14 max-w-[45rem] mx-auto px-margin md:px-margin-tablet flex items-center justify-between">
<a class="font-headline-sm text-headline-sm hover:text-primary" href="./">&lt;이야기가 필요해&gt;</a>
<nav class="flex items-center gap-space-md font-label-md text-label-md text-on-surface-variant">
<a class="hover:text-on-surface" href="docs.html">전체 문서</a>
<a class="hover:text-on-surface" href="{CHANNEL}" target="_blank" rel="noopener noreferrer">유튜브</a></nav></div></header>
<main class="max-w-[45rem] mx-auto px-margin md:px-margin-tablet py-space-xl">
<section class="text-center my-space-lg">
<div class="w-8 h-0.5 bg-primary mx-auto mb-space-md opacity-80"></div>
<p class="font-headline-sm text-headline-sm leading-9">살다 보면 마음에 남는 질문이 있습니다.<br>그 질문에 콘텐츠로 답해보는 팟캐스트,</p>
<h1 class="font-headline-hero text-headline-hero-mobile sm:text-headline-hero mt-space-sm">&lt;이야기가 필요해&gt;</h1>
<p class="font-label-sm text-label-sm text-secondary tracking-widest mt-space-md">우리가 나눈 질문들</p></section>
<ol class="mt-space-lg">{"".join(item(e) for e in eps)}</ol>
</main>
<footer class="bg-surface-container-low mt-space-xl"><div class="max-w-[45rem] mx-auto px-margin md:px-margin-tablet py-space-xl flex flex-col gap-space-xs">
<span class="font-headline-sm text-headline-sm">&lt;이야기가 필요해&gt;</span>
<p class="text-sm text-secondary">살다 보면 마음에 남는 질문이 있습니다. 그 질문에 콘텐츠로 답해보는 팟캐스트.</p>
<a class="font-label-md text-label-md text-on-surface-variant hover:text-primary" href="{CHANNEL}" target="_blank" rel="noopener noreferrer">YouTube</a></div></footer>
</body></html>
"""
    out = ROOT / "index.html"
    out.write_text(head + body, encoding="utf-8")
    print(f"{out} — 회차 {len(eps)}개")


if __name__ == "__main__":
    main()
