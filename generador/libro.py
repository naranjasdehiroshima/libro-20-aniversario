"""Libro de Naranjas de Hiroshima: convierte las entradas del blog en un libro PDF.
Uso: python3 libro.py <carpeta_feeds> <año_desde> <año_hasta> <numero_libro> <salida_dir>
"""
import json, glob, os, re, sys, hashlib, html as H, io, base64, asyncio, urllib.request
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from PIL import Image
import qrcode

FEEDS, Y0, Y1, NUM, OUT = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
NUMTXT = f' · Nº {NUM}' if NUM else ''
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)
_cache = os.path.join(FEEDS, 'img_cache'); os.makedirs(_cache, exist_ok=True)
if not os.path.exists(os.path.join(OUT, 'img')):
    os.symlink(_cache, os.path.join(OUT, 'img'))
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

entries = []
for f in sorted(glob.glob(os.path.join(FEEDS, 'feed_*.json'))):
    entries += json.load(open(f))['feed'].get('entry', [])
seen = set(); posts = []
for e in entries:
    y = int(e['published']['$t'][:4])
    link = next((l['href'] for l in e['link'] if l['rel'] == 'alternate'), '')
    if Y0 <= y <= Y1 and link not in seen:
        seen.add(link)
        posts.append(dict(t=e['title']['$t'].strip(), d=e['published']['$t'], u=link,
                          labels=[c['term'] for c in e.get('category', [])], html=e.get('content', {}).get('$t', '')))
posts.sort(key=lambda p: p['d'])
CACHE = os.path.join(FEEDS, 'paginas'); os.makedirs(CACHE, exist_ok=True)
def cuerpo_vivo(p):
    k = os.path.join(CACHE, hashlib.md5(p['u'].encode()).hexdigest() + '.html')
    if not os.path.exists(k):
        try:
            req = urllib.request.Request(p['u'], headers={'User-Agent': 'Mozilla/5.0'})
            open(k, 'wb').write(urllib.request.urlopen(req, timeout=40).read())
        except Exception:
            return
    pb = BeautifulSoup(open(k, encoding='utf-8', errors='ignore').read(), 'lxml').select_one('.post-body')
    if pb and len(pb.get_text(strip=True)) >= 0.6 * len(BeautifulSoup(p['html'], 'lxml').get_text(strip=True)):
        p['html'] = pb.decode_contents()
with ThreadPoolExecutor(12) as ex: list(ex.map(cuerpo_vivo, posts))

# ---------- imágenes: descarga, reduce y guarda en local ----------
def norm(url):
    url = url.strip()
    if url.startswith('//'): url = 'https:' + url
    url = re.sub(r'/s\d+(-[a-z0-9-]+)?/', '/w1200/', url)
    url = re.sub(r'=s\d+(-[a-z0-9-]+)?$', '=w1200', url)
    return url
jobs = {}
def local(url):
    url = norm(url); k = hashlib.md5(url.encode()).hexdigest()[:16]
    jobs[url] = k
    return f'img/{k}.jpg'
def fetch(item):
    url, k = item; dst = os.path.join(OUT, 'img', k + '.jpg')
    if os.path.exists(dst): return True
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = urllib.request.urlopen(req, timeout=40).read()
        im = Image.open(io.BytesIO(data))
        if im.mode in ('RGBA', 'LA', 'P'):
            im = im.convert('RGBA'); bg = Image.new('RGB', im.size, (255, 255, 255)); bg.paste(im, mask=im.split()[-1]); im = bg
        else: im = im.convert('RGB')
        im.thumbnail((900, 1200)); im.save(dst, 'JPEG', quality=76, optimize=True, progressive=True)
        return True
    except Exception:
        return False

def qr(url):
    q = qrcode.QRCode(border=1, box_size=4); q.add_data(url); q.make(fit=True)
    b = io.BytesIO(); q.make_image(fill_color='#1A1410', back_color='#FDFAF5').save(b, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

def limpiar(html):
    s = BeautifulSoup(html, 'lxml')
    for t in s(['script', 'style', 'noscript', 'form', 'input', 'button']): t.decompose()
    for f in s.find_all(['iframe', 'embed', 'object', 'video']):
        src = f.get('src') or f.get('data') or ''
        yt = re.search(r'(?:youtube(?:-nocookie)?\.com/(?:embed|v)/|youtu\.be/)([\w-]{11})', src)
        box = s.new_tag('div', **{'class': 'video'})
        if src.startswith('//'): src = 'https:' + src
        if yt:
            img = s.new_tag('img', src=local(f'https://img.youtube.com/vi/{yt.group(1)}/hqdefault.jpg')); box.append(img)
            src = f'https://www.youtube.com/watch?v={yt.group(1)}'
        cap = s.new_tag('p', **{'class': 'video-cap'})
        cap.string = 'Película en línea · ' + (src if src else 'ver en el blog')
        box.append(cap); f.replace_with(box)
    for img in s.find_all('img'):
        src = img.get('src') or ''
        if not src or src.startswith('data:') or 'feeds.feedburner' in src or 'blogger.com/img/icon' in src: img.decompose(); continue
        img['src'] = local(src)
        for a in ('width', 'height', 'style', 'border', 'srcset', 'data-original-height', 'data-original-width'): img.attrs.pop(a, None)
    for t in s.find_all(True):
        for a in ('style', 'width', 'height', 'align', 'face', 'size', 'color', 'class' if t.name not in ('div', 'p') else '__'):
            t.attrs.pop(a, None)
    for a in s.find_all('a'):
        if a.find('img'): a.unwrap()
    for t in s.find_all(['p', 'div', 'span']):
        if not t.get_text(strip=True).replace('\xa0', '') and not t.find(['img', 'div']):
            t.decompose()
    body = s.body.decode_contents() if s.body else str(s)
    return re.sub(r'(<br\s*/?>\s*){3,}', '<br/><br/>', body)

def fecha(iso):
    y, m, d = iso[:4], int(iso[5:7]), int(iso[8:10])
    return f'{d} de {MESES[m - 1]} de {y}'

years = sorted({p['d'][:4] for p in posts})
toc, body = [], []
for y in years:
    ps = [p for p in posts if p['d'][:4] == y]
    body.append(f"<section class='anio' id='a{y}'><div class='anio-num'>{y}</div><div class='anio-sub'>{len(ps)} {'entrada' if len(ps) == 1 else 'entradas'}</div></section>")
    toc.append(f"<li class='toc-anio'><a data-pag='000' href='#a{y}'>{y}</a></li>")
    for i, p in enumerate(ps):
        pid = 'e' + hashlib.md5(p['u'].encode()).hexdigest()[:8]
        toc.append(f"<li><a data-pag='000' href='#{pid}'><span>{H.escape(p['t'])}</span></a></li>")
        chips = ''.join(f"<span class='chip'>{H.escape(l)}</span>" for l in p['labels'][:12])
        body.append(f"""<article class='entrada' id='{pid}'>
<header><div class='fecha'>{fecha(p['d'])}</div><h2>{H.escape(p['t'])}</h2><div class='chips'>{chips}</div></header>
<div class='cuerpo'>{limpiar(p['html'])}</div>
<footer class='fuente'><img class='qr' src='{qr(p['u'])}' alt=''/><div><b>Entrada original</b><br/>{H.escape(p['u'])}</div></footer>
</article>""")

with ThreadPoolExecutor(16) as ex:
    res = list(ex.map(fetch, jobs.items()))
print('imágenes', sum(res), 'de', len(res))
# imágenes fallidas: quitarlas
falladas = {k for (u, k), ok in zip(jobs.items(), res) if not ok}
html_body = '\n'.join(body)
for k in falladas:
    html_body = re.sub(rf"<img[^>]*src=\"img/{k}\.jpg\"[^>]*/?>", '', html_body)

css = open(os.path.join(HERE, 'libro.css'), encoding='utf-8').read()
css = css.replace('__FONDO__', base64.b64encode(open(os.path.join(HERE, 'fondo_portada.jpg'), 'rb').read()).decode())
samurai_l = base64.b64encode(open(os.path.join(HERE, 'boom.webp'), 'rb').read()).decode()
samurai_r = base64.b64encode(open(os.path.join(HERE, 'cam.webp'), 'rb').read()).decode()
n = len(posts)
import markdown
intro_path = os.path.join(HERE, 'intro.md')
intro_html = markdown.markdown(open(intro_path, encoding='utf-8').read()) if os.path.exists(intro_path) else ''
intro_html = re.sub(r'\[([^\]]+)\]', r"<mark>[\1]</mark>", intro_html)
doc = f"""<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Libro de Naranjas de Hiroshima · 20 aniversario</title>
<link href='https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+JP:wght@700;900&family=DM+Mono:wght@400;500&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap' rel='stylesheet'>
<style>{css}</style></head><body>
<section class='portada'>
  <div class='pt-grano'></div>
  <div class='pt-top'>
    <div class='pt-libro'>Libro de</div>
    <div class='pt-nombre'>Naranjas de Hiroshima</div>
    <div class='pt-etiqueta'>Edición 20 aniversario{NUMTXT}</div>
  </div>
  <div class='pt-claqueta'></div>
  <div class='pt-escena'>
    <div class='pt-rayos'></div>
    <div class='pt-lata'>
      <div class='pt-lata-cara'></div>
      <div class='pt-etq'>
        <div class='pt-etq-top'><span>Naranjas de Hiroshima</span><span>NdH</span></div>
        <div class='pt-etq-num'><b>20</b><i>años</i></div>
        <div class='pt-etq-bot'><span>2007 — 2027</span><span>Lata 020</span></div>
      </div>
    </div>
    <img class='pt-sam pt-sam-l' src='data:image/webp;base64,{samurai_l}' alt=''/>
    <img class='pt-sam pt-sam-r' src='data:image/webp;base64,{samurai_r}' alt=''/>
    <div class='pt-jp pt-jp-l'>ドキュメンタリー映画</div>
    <div class='pt-jp pt-jp-r'>広島オレンジ</div>
    <div class='pt-anios'><b>años</b>difundiendo cine documental</div>
  </div>
  <div class='pt-fechas'>2007 <i></i> 2027</div>
  <div class='pt-pie'>{n} entradas · Cine documental · Creative Commons</div>
</section>
<section class='creditos'>
  <p><b>Libro de Naranjas de Hiroshima{NUMTXT} · Edición 20 aniversario</b><br/>Entradas publicadas entre {Y0} y {Y1} en naranjasdehiroshima.com</p>
  <p>Edición de aniversario. Archivo en PDF del blog, para leer sin conexión y para que el trabajo sobreviva a la web.</p>
  <p>Textos bajo licencia Creative Commons BY-NC-SA. Las imágenes y películas citadas pertenecen a sus autores.</p>
  <p>Ciudad de México</p>
</section>
<section class='intro'>{intro_html}</section>
<nav class='indice'><h2>Índice</h2><ol>{''.join(toc)}</ol></nav>
{html_body}
</body></html>"""
open(os.path.join(OUT, 'libro.html'), 'w', encoding='utf-8').write(doc)

OPTS = dict(width='170mm', height='240mm', print_background=True, display_header_footer=True, header_template='<span></span>',
            footer_template="<div style='width:100%;font-family:monospace;font-size:7px;color:#5E5044;text-align:center;letter-spacing:.1em'>NARANJAS DE HIROSHIMA · <span class='pageNumber'></span></div>",
            margin={'top': '18mm', 'bottom': '18mm', 'left': '16mm', 'right': '16mm'})
async def pdf():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto('file://' + os.path.abspath(os.path.join(OUT, 'libro.html')), wait_until='networkidle', timeout=600000)
        await pg.add_style_tag(content='.portada{height:200mm!important;margin:0!important;visibility:hidden;background:none!important}')
        await pg.evaluate("document.querySelector('.portada').innerHTML = ''")
        final = os.path.join(OUT, f'Libro-Naranjas-de-Hiroshima-20-aniversario-{Y0}-{Y1}.pdf')
        for paso in (1, 2):
            await pg.pdf(path=final, **OPTS)
            if paso == 1:
                from pypdf import PdfReader
                r = PdfReader(final); pags = {}
                # cada enlace del índice apunta a la página de destino
                for i, page in enumerate(r.pages[:80]):
                    for an in (page.get('/Annots') or []):
                        a = an.get_object()
                        dest = a.get('/Dest') or (a.get('/A') or {}).get('/D')
                        if dest is None: continue
                        if isinstance(dest, str) or hasattr(dest, 'decode'):
                            d = r.named_destinations.get(str(dest))
                            if d is None: continue
                            num = r.get_destination_page_number(d)
                            pags[str(dest).lstrip('/')] = num + 1
                await pg.evaluate('''(p) => document.querySelectorAll('.indice a').forEach(a => { const k = decodeURIComponent(a.getAttribute('href').slice(1)); if (p[k]) a.setAttribute('data-pag', p[k]); })''', pags)
                print('índice', len(pags), 'destinos')
        # portada sin márgenes ni pie, unida delante
        cap = await b.new_page(viewport={'width': 643, 'height': 907}, device_scale_factor=3.125)
        await cap.goto('file://' + os.path.abspath(os.path.join(OUT, 'libro.html')), wait_until='networkidle', timeout=600000)
        await cap.evaluate("document.querySelectorAll('body > :not(.portada)').forEach(e => e.remove()); document.querySelector('.portada').style.margin = '0'")
        await cap.wait_for_timeout(800)
        png = os.path.join(OUT, 'portada.png')
        await cap.locator('.portada').screenshot(path=png)
        Image.open(png).convert('RGB').save(os.path.join(OUT, 'portada.jpg'), 'JPEG', quality=90)
        jpg64 = base64.b64encode(open(os.path.join(OUT, 'portada.jpg'), 'rb').read()).decode()
        await cap.set_content("<html><body style='margin:0'><img style='display:block;width:170mm;height:240mm' src='data:image/jpeg;base64," + jpg64 + "'></body></html>")
        tapa = os.path.join(OUT, '_portada.pdf')
        await cap.pdf(path=tapa, width='170mm', height='240mm', print_background=True, margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'}, page_ranges='1')
        from pypdf import PdfReader, PdfWriter
        w = PdfWriter(); w.append(tapa); w.append(final, pages=(1, len(PdfReader(final).pages)))
        w.write(final); os.remove(tapa)
        await b.close()
        return
        await pg.pdf(path=os.path.join(OUT, f'Libro-Naranjas-de-Hiroshima-20-aniversario-{Y0}-{Y1}.pdf'), width='170mm', height='240mm',
                     print_background=True, display_header_footer=True, header_template='<span></span>',
                     footer_template="<div style='width:100%;font-family:monospace;font-size:7px;color:#5E5044;text-align:center;letter-spacing:.1em'>NARANJAS DE HIROSHIMA · <span class='pageNumber'></span></div>",
                     margin={'top': '18mm', 'bottom': '18mm', 'left': '16mm', 'right': '16mm'})
        await b.close()
asyncio.run(pdf())
print('ok', n, 'entradas')
