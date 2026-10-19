"""Собирает все сайты в папку sites/ и галерею sites/index.html.

    python3 tools/build_sites.py              — сайты для GitHub / Vercel
    python3 tools/build_sites.py --artifacts DIR — версии для артефактов claude.ai
"""
import os
import sys
from html import escape as e

sys.path.insert(0, os.path.dirname(__file__))
from site_engine import render, icon  # noqa: E402

SITES = []
for mod in ('sites_a', 'sites_b', 'sites_c'):
    try:
        SITES += __import__(mod).SITES
    except ModuleNotFoundError:
        pass

ROOT = os.path.join(os.path.dirname(__file__), '..', 'sites')


def gallery(links):
    cards = ''
    for i, s in enumerate(SITES):
        bg, fg, accent, accent2 = s['pal']
        href = links(s)
        target = ' target="_blank" rel="noopener"' if href.startswith('http') else ''
        cards += (f'<a class="t" href="{e(href)}"{target} style="--i:{i % 12};--b:{bg};--f:{fg};--a:{accent};--a2:{accent2}">'
                  f'<span class="t__ico">{icon(s["icon"])}</span><small>{e(s["niche"])}</small><b>{e(s["name"])}</b></a>')
    return f'''<title>50 сайтов</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@600&family=Manrope:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{--bg:#F3F2EF;--fg:#161616;--muted:#6E6B66;--ease:cubic-bezier(.22,1,.36,1)}}
*,*::before,*::after{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 "Manrope",system-ui,sans-serif}}
a{{color:inherit;text-decoration:none}}
main{{max-width:1240px;margin:0 auto;padding:60px max(16px,4vw) 80px}}
h1{{font:600 clamp(34px,6vw,72px)/1 "Unbounded",system-ui,sans-serif;margin:0 0 14px;text-wrap:balance}}
.lead{{color:var(--muted);max-width:620px;margin:0 0 40px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}}
.t{{position:relative;display:flex;flex-direction:column;justify-content:flex-end;min-height:190px;padding:20px;border-radius:20px;overflow:hidden;background:var(--b);color:var(--f);transition:transform .5s var(--ease),box-shadow .5s var(--ease);animation:in .7s var(--ease) both;animation-delay:calc(var(--i)*40ms)}}
.t:hover{{transform:translateY(-6px);box-shadow:0 30px 50px -30px rgba(0,0,0,.5)}}
.t::before{{content:"";position:absolute;right:-50px;top:-50px;width:170px;height:170px;border-radius:50%;background:radial-gradient(circle at 30% 30%,var(--a2),var(--a));transition:transform .8s var(--ease)}}
.t:hover::before{{transform:scale(1.4)}}
.t__ico{{position:absolute;top:22px;left:20px;width:44px;height:44px;border-radius:12px;display:grid;place-items:center;background:var(--a);color:#fff}}
.t__ico svg{{width:22px;height:22px}}
.t small{{position:relative;opacity:.7;font-size:13px}}
.t b{{position:relative;font:600 21px/1.15 "Unbounded",system-ui,sans-serif}}
@keyframes in{{from{{opacity:0;transform:translateY(16px)}}}}
@media (prefers-reduced-motion:reduce){{.t{{animation:none}}}}
</style>
<main>
  <h1>{len(SITES)} сайтов для бизнеса</h1>
  <p class="lead">Шаблоны с плавной анимацией и записью через WhatsApp: форма собирает сообщение и открывает личный чат. Названия и данные вымышленные — под реальную компанию меняем тексты, цены, контакты и номер WhatsApp.</p>
  <div class="grid">{cards}</div>
</main>
'''


def main():
    if '--artifacts' in sys.argv:
        out = sys.argv[sys.argv.index('--artifacts') + 1]
        os.makedirs(out, exist_ok=True)
        for s in SITES:
            with open(os.path.join(out, s['slug'] + '.html'), 'w') as f:
                f.write(render(s, artifact=True))
        print(f'{len(SITES)} artifact pages → {out}')
        return
    os.makedirs(ROOT, exist_ok=True)
    for s in SITES:
        d = os.path.join(ROOT, s['slug'])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'index.html'), 'w') as f:
            f.write(render(s))
    page = gallery(lambda s: s['slug'] + '/')
    with open(os.path.join(ROOT, 'index.html'), 'w') as f:
        f.write('<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1">\n' + page.replace('<main>', '</head>\n<body>\n<main>', 1) + '</body>\n</html>\n')
    print(f'{len(SITES)} sites → {os.path.normpath(ROOT)}')


if __name__ == '__main__':
    main()
