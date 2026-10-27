"""Web del Libro de Naranjas de Hiroshima (GitHub Pages) + tomos por año.
Uso: python3 sitio.py <carpeta_feeds> <pdf_completo> <portada.jpg> <intro.md> <salida>
"""
import json, glob, os, re, sys, hashlib, html as H, shutil
import markdown
from pypdf import PdfReader, PdfWriter

FEEDS, PDF, PORTADA, INTRO, OUT = sys.argv[1:6]
os.makedirs(os.path.join(OUT, 'tomos'), exist_ok=True)
NOMBRE_PDF = os.path.basename(PDF)
r = PdfReader(PDF)
total_pags = len(r.pages)
dest = {k.lstrip('/'): r.get_destination_page_number(v) + 1 for k, v in r.named_destinations.items()}

entries = []
for f in sorted(glob.glob(os.path.join(FEEDS, 'feed_*.json'))):
    entries += json.load(open(f))['feed'].get('entry', [])
seen, datos = set(), []
for e in entries:
    link = next((l['href'] for l in e['link'] if l['rel'] == 'alternate'), '')
    if link in seen: continue
    seen.add(link)
    pid = 'e' + hashlib.md5(link.encode()).hexdigest()[:8]
    datos.append({'t': e['title']['$t'].strip(), 'd': e['published']['$t'][:10], 'u': link,
                  'l': [c['term'] for c in e.get('category', [])], 'p': dest.get(pid)})
datos.sort(key=lambda x: x['d'])
anios = sorted({x['d'][:4] for x in datos})

# tomos por año: portada + páginas del año
tomos = []
for i, y in enumerate(anios):
    ini = dest.get('a' + y)
    if not ini: continue
    fin = (dest.get('a' + anios[i + 1]) - 1) if i + 1 < len(anios) and dest.get('a' + anios[i + 1]) else total_pags
    w = PdfWriter()
    w.add_page(r.pages[0])
    for p in range(ini - 1, fin): w.add_page(r.pages[p])
    w.add_metadata({'/Title': f'Libro de Naranjas de Hiroshima · {y}'})
    nombre = f'Libro-Naranjas-de-Hiroshima-{y}.pdf'
    with open(os.path.join(OUT, 'tomos', nombre), 'wb') as fh: w.write(fh)
    tomos.append({'y': y, 'n': sum(1 for x in datos if x['d'][:4] == y), 'pags': fin - ini + 1, 'ini': ini,
                  'mb': round(os.path.getsize(os.path.join(OUT, 'tomos', nombre)) / 1e6, 1), 'f': 'tomos/' + nombre})

shutil.copy(PORTADA, os.path.join(OUT, 'portada.jpg'))
pdf_mb = round(os.path.getsize(PDF) / 1e6)
en_repo = pdf_mb < 24   # el navegador de GitHub solo acepta archivos de hasta 25 MB
if en_repo: shutil.copy(PDF, os.path.join(OUT, NOMBRE_PDF))

intro = open(INTRO, encoding='utf-8').read()
intro = re.sub(r'^# .*\n', '', intro, count=1)
intro_html = markdown.markdown(intro)
intro_html = re.sub(r'\[([^\]]+)\]', r'<mark>[\1]</mark>', intro_html)

n = len(datos)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import portada_web
PT_CSS, PT_HTML, PT_JS = portada_web.construir(os.path.dirname(os.path.abspath(__file__)), OUT)
PT_HTML = PT_HTML.replace('{N}', str(len(datos)))
pdf_href = NOMBRE_PDF if en_repo else 'https://github.com/naranjasdehiroshima/libro-20-aniversario/releases/latest/download/' + NOMBRE_PDF
tomos_html = ''.join(
    f"<div class='tomo'><a class='tomo-leer' href='lector.html?t={t['y']}'><b>{t['y']}</b><span>{t['n']} {'entrada' if t['n'] == 1 else 'entradas'} · {t['pags']} págs.</span><i>Leer en línea →</i></a><a class='tomo-pdf' href='{t['f']}' download>PDF · {t['mb']} MB</a></div>"
    for t in tomos)

page = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Libro de Naranjas de Hiroshima · 20 aniversario</title>
<meta name="description" content="Veinte años de cine documental: las {n} entradas de Naranjas de Hiroshima (2007–2026) en un libro de {total_pags:,} páginas para leer, descargar y guardar.">
<meta property="og:title" content="Libro de Naranjas de Hiroshima · 20 aniversario">
<meta property="og:description" content="{n} entradas · {total_pags:,} páginas · 2007–2027">
<meta property="og:image" content="portada.jpg">
<meta name="theme-color" content="#1A1410">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+JP:wght@900&family=DM+Mono:wght@400;500&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
<style>
:root{{--naranja:#D4521A;--naranja-osc:#B2410F;--naranja-luz:#F08A4B;--negro:#1A1410;--negro-2:#2A221C;--gris:#3D342C;--gris-m:#5E5044;--linea:#D8CCBB;--crema:#F5F0E8;--crema-o:#EDE5D8;--blanco:#FDFAF5;--claro:#E8E0D5;--tenue:#C9BBA8}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--crema);color:var(--negro);font-family:'Libre Baskerville',Georgia,serif;font-size:17px;line-height:1.7}}
a{{color:var(--naranja-osc)}}a:hover{{color:var(--negro)}}
.wrap{{max-width:1200px;margin:0 auto;padding:0 40px}}@media(max-width:700px){{.wrap{{padding:0 16px}}}}
.bebas{{font-family:'Bebas Neue',Impact,sans-serif;font-weight:400;text-transform:uppercase;letter-spacing:.02em}}
.mono{{font-family:'DM Mono',monospace}}
.hero{{background:var(--negro);color:var(--blanco)}}
.hero .wrap{{display:flex;flex-wrap:wrap;gap:48px;align-items:center;padding-top:56px;padding-bottom:56px}}
.portada-col{{flex:0 1 380px;min-width:240px;width:100%}}
.hero-txt{{flex:999 1 420px;min-width:0;display:flex;flex-direction:column;gap:18px}}
.kicker{{font-family:'DM Mono',monospace;font-size:12px;letter-spacing:.18em;text-transform:uppercase;color:var(--tenue)}}
.hero h1{{margin:0;font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:clamp(48px,7vw,92px);line-height:.92;color:var(--naranja-luz);text-transform:uppercase}}
.hero p{{margin:0;color:var(--claro);font-size:18px;max-width:58ch}}
.cifras{{display:flex;flex-wrap:wrap;border-top:1px solid #4a3f36;border-bottom:1px solid #4a3f36}}
.cifra{{padding:12px 22px 12px 0;margin-right:22px;border-right:1px solid #4a3f36}}.cifra:last-child{{border-right:0}}
.cifra b{{display:block;font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:40px;line-height:1;color:var(--blanco)}}
.cifra span{{font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--tenue)}}
.btns{{display:flex;flex-wrap:wrap;gap:10px}}
.btn{{display:inline-flex;align-items:center;min-height:48px;padding:0 22px;border-radius:2px;font-family:'DM Mono',monospace;font-size:13px;letter-spacing:.12em;text-transform:uppercase;text-decoration:none;background:var(--naranja-osc);color:var(--blanco)}}
.btn:hover{{background:var(--naranja-luz);color:var(--negro)}}
.btn.sec{{background:transparent;border:1px solid var(--naranja-luz);color:var(--naranja-luz)}}.btn.sec:hover{{background:var(--naranja-luz);color:var(--negro)}}
.perfs{{height:14px;background-color:#0E0B09;background-image:repeating-linear-gradient(90deg,transparent 0,transparent 10px,var(--crema) 10px,var(--crema) 20px,transparent 20px,transparent 30px);background-size:30px 6px;background-repeat:repeat-x;background-position:0 4px;opacity:.85}}
section{{padding:64px 0}}
h2.sec{{margin:0 0 24px;font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:46px;line-height:1;text-transform:uppercase;border-bottom:1px solid var(--linea);padding-bottom:10px}}
.intro{{max-width:760px}}
.intro h2{{font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:30px;text-transform:uppercase;color:var(--naranja-osc);margin:32px 0 8px}}
.intro blockquote{{margin:0 0 24px;padding:4px 0 4px 18px;border-left:4px solid var(--naranja);font-style:italic;color:var(--gris)}}
.intro mark{{background:#FFE7A8;padding:0 3px}}
.tomos{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px}}
.tomo-leer{{display:flex;flex-direction:column;gap:4px;text-decoration:none;color:var(--negro)}}.tomo-leer:hover b{{color:var(--naranja-osc)}}
.tomo-pdf{{margin-top:8px;padding-top:8px;border-top:1px dotted var(--linea);font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--gris);text-decoration:none}}.tomo-pdf:hover{{color:var(--naranja-osc)}}
.tomo{{display:flex;flex-direction:column;gap:4px;padding:16px;background:var(--blanco);border:1px solid var(--linea);border-top:4px solid var(--negro);border-radius:2px;text-decoration:none;color:var(--negro)}}
.tomo:hover{{border-top-color:var(--naranja);color:var(--negro)}}
.tomo b{{font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:40px;line-height:1}}
.tomo span{{font-size:14px;color:var(--gris)}}.tomo i{{font-style:normal;font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.08em;color:var(--naranja-osc);text-transform:uppercase}}
.buscar{{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-bottom:16px}}
.buscar label{{font-family:'DM Mono',monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--gris-m)}}
.buscar input{{flex:1;min-width:220px;font-family:'DM Mono',monospace;font-size:15px;padding:12px 14px;min-height:48px;border:1px solid var(--linea);background:var(--blanco);border-radius:2px;color:var(--negro)}}
.anios{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:20px}}
.anios button{{min-height:40px;padding:0 12px;border:1px solid var(--linea);background:var(--blanco);border-radius:2px;font-family:'DM Mono',monospace;font-size:13px;cursor:pointer;color:var(--gris)}}
.anios button[aria-pressed=true]{{background:var(--negro);color:var(--blanco);border-color:var(--negro)}}
#cuenta{{font-family:'DM Mono',monospace;font-size:12px;color:var(--gris-m);margin-bottom:8px}}
.lista{{list-style:none;margin:0;padding:0}}
.lista li{{display:grid;grid-template-columns:110px minmax(0,1fr) auto;gap:4px 18px;align-items:baseline;padding:12px 0;border-bottom:1px dotted var(--linea)}}
.lista .f{{font-family:'DM Mono',monospace;font-size:12px;color:var(--gris-m)}}
.lista .t a{{color:var(--negro);text-decoration:none;font-weight:700}}.lista .t a:hover{{color:var(--naranja-osc)}}
.lista .et{{display:block;font-family:'DM Mono',monospace;font-size:11px;color:var(--gris-m);margin-top:2px}}
.lista .pg{{font-family:'DM Mono',monospace;font-size:12px;white-space:nowrap}}
@media(max-width:620px){{.lista li{{grid-template-columns:1fr auto}}.lista .f{{grid-column:1/-1}}}}
footer{{background:var(--negro);color:var(--claro);padding:40px 0;font-family:'DM Mono',monospace;font-size:12px;letter-spacing:.06em}}
footer a{{color:var(--naranja-luz)}}
{PT_CSS}</style></head><body>
<header class="hero"><div class="wrap">
  <div class="portada-col">{PT_HTML}</div>
  <div class="hero-txt">
    <div class="kicker">Naranjas de Hiroshima · 2007 — 2027</div>
    <h1>Libro de Naranjas de Hiroshima<br>Edición 20 aniversario</h1>
    <p>Veinte años de cine documental: todas las entradas del blog, de 2007 a hoy, en un solo libro para leer sin conexión, descargar y guardar.</p>
    <div class="cifras">
      <div class="cifra"><b>{n}</b><span>entradas</span></div>
      <div class="cifra"><b>{total_pags:,}</b><span>páginas</span></div>
      <div class="cifra"><b>{len(anios)}</b><span>años con publicaciones</span></div>
      <div class="cifra"><b>20</b><span>años</span></div>
    </div>
    <div class="btns">
      <a class="btn" href="lector.html?t={anios[0]}">Leer en línea</a>
      <a class="btn sec" href="{pdf_href}">Descargar el libro · PDF {pdf_mb} MB</a>
      <a class="btn sec" href="#tomos">Por años</a>
      <a class="btn sec" href="https://www.naranjasdehiroshima.com/">Ir al blog</a>
    </div>
  </div>
</div></header>
<div class="perfs" aria-hidden="true"></div>
<main>
<section><div class="wrap"><h2 class="sec">Veinte años de Naranjas de Hiroshima</h2><div class="intro">{intro_html}</div></div></section>
<section id="tomos" style="background:var(--crema-o)"><div class="wrap"><h2 class="sec">El libro por años</h2>
<p style="margin-top:0;color:var(--gris)">Cada tomo incluye la portada y las entradas de ese año. Pesan poco y se abren en el navegador.</p>
<div class="tomos">{tomos_html}</div></div></section>
<section id="indice"><div class="wrap"><h2 class="sec">Índice</h2>
<div class="buscar"><label for="q">Buscar</label><input id="q" type="search" placeholder="título, director, país, tema…" autocomplete="off"></div>
<div class="anios" role="group" aria-label="Filtrar por año"></div>
<div id="cuenta" aria-live="polite"></div>
<ol class="lista" id="lista"></ol></div></section>
</main>
<footer><div class="wrap">Naranjas de Hiroshima · Ciudad de México · desde 2007 · Textos bajo licencia Creative Commons BY-NC-SA · <a href="https://www.naranjasdehiroshima.com/">naranjasdehiroshima.com</a></div></footer>
<script>
const DATOS = {json.dumps(datos, ensure_ascii=False)};
const TOMOS = {json.dumps({t['y']: t for t in tomos}, ensure_ascii=False)};
const PDF = {json.dumps(pdf_href)}, PDF_LOCAL = {json.dumps(en_repo)};
const MESES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
const norm = s => s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
const esc = s => s.replace(/[&<>"]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
DATOS.forEach(x => x.k = norm(x.t + ' ' + x.l.join(' ')));
let anio = null;
const cont = document.querySelector('.anios');
['Todos', ...Object.keys(TOMOS)].forEach(y => {{
  const b = document.createElement('button'); b.type = 'button'; b.textContent = y;
  b.setAttribute('aria-pressed', y === 'Todos' ? 'true' : 'false');
  b.onclick = () => {{ anio = y === 'Todos' ? null : y; cont.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b ? 'true' : 'false')); pintar(); }};
  cont.appendChild(b);
}});
function enlacePagina(x) {{
  if (!x.p) return '';
  const y = x.d.slice(0,4), t = TOMOS[y];
  if (PDF_LOCAL) return `<a class="pg" href="${{PDF}}#page=${{x.p}}">pág. ${{x.p}}</a>`;
  if (t) return `<a class="pg" href="lector.html?t=${{y}}#p${{x.p - t.ini + 2}}">pág. ${{x.p}}</a>`;
  return `<span class="pg">pág. ${{x.p}}</span>`;
}}
function pintar() {{
  const q = norm(document.getElementById('q').value.trim());
  const res = DATOS.filter(x => (!anio || x.d.startsWith(anio)) && (!q || q.split(/\\s+/).every(w => x.k.includes(w))));
  document.getElementById('cuenta').textContent = res.length + (res.length === 1 ? ' entrada' : ' entradas');
  document.getElementById('lista').innerHTML = res.map(x => {{
    const [y,m,d] = x.d.split('-');
    return `<li><span class="f">${{+d}} ${{MESES[+m-1]}} ${{y}}</span><span class="t"><a href="${{x.u}}">${{esc(x.t)}}</a><span class="et">${{esc(x.l.slice(0,6).join(' · '))}}</span></span>${{enlacePagina(x)}}</li>`;
  }}).join('');
}}
document.getElementById('q').addEventListener('input', pintar);
pintar();
{PT_JS}
</script>
</body></html>"""
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(page)
HERE = os.path.dirname(os.path.abspath(__file__))
lector = open(os.path.join(HERE, 'lector.html'), encoding='utf-8').read()
lector = lector.replace('__TOMOS__', json.dumps({t['y']: {'f': t['f'], 'n': t['n']} for t in tomos}, ensure_ascii=False)).replace('__PDF__', json.dumps(pdf_href))
open(os.path.join(OUT, 'lector.html'), 'w', encoding='utf-8').write(lector)
shutil.copytree(os.path.join(HERE, 'vendor'), os.path.join(OUT, 'vendor'), dirs_exist_ok=True)
open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8').write(f"""# Libro de Naranjas de Hiroshima · Edición 20 aniversario

Todas las entradas de [Naranjas de Hiroshima](https://www.naranjasdehiroshima.com/) (2007–2026) en un libro PDF de {total_pags:,} páginas, más un tomo por año.

Web: https://naranjasdehiroshima.github.io/libro-20-aniversario/

Textos bajo licencia Creative Commons BY-NC-SA. Las imágenes y películas citadas pertenecen a sus autores.
""")
print('ok', n, 'entradas,', len(tomos), 'tomos, PDF', pdf_mb, 'MB', 'en el repo' if en_repo else 'para Release')
