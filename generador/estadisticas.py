"""Cifras del archivo de Naranjas de Hiroshima a partir del catálogo (xlsx), el feed del blog y los más vistos."""
import re, json, glob, collections, unicodedata, urllib.request, html as H

def nz(s): return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower().strip()

ALI = {'eeuu': 'Estados Unidos', 'e.e.u.u': 'Estados Unidos', 'u.s.a': 'Estados Unidos', 'usa': 'Estados Unidos', 'estados unidos': 'Estados Unidos',
       'ee.uu': 'Estados Unidos', 'ee. uu': 'Estados Unidos', 'mexico': 'México', 'inglaterra': 'Reino Unido', 'uk': 'Reino Unido', 'reino unido': 'Reino Unido',
       'urss': 'Unión Soviética', 'u.r.s.s': 'Unión Soviética', 'union sovietica': 'Unión Soviética', 'holanda': 'Países Bajos', 'paises bajos': 'Países Bajos',
       'peru': 'Perú', 'espana': 'España', 'catalunya': 'España'}

def minutos(s):
    if not s: return None
    s = str(s).lower().replace(',', '.')
    h = re.search(r'(\d+(?:\.\d+)?)\s*h', s); m = re.search(r'(\d+)\s*(?:min|\'|m\b)', s)
    if h: return float(h.group(1)) * 60 + (int(m.group(1)) if m and s.index(m.group(0)) > s.index(h.group(0)) else 0)
    if m: return int(m.group(1))
    hm = re.match(r'^(\d+):(\d\d)$', s.strip())
    if hm: return int(hm.group(1)) * 60 + int(hm.group(2))
    n = re.match(r'^(\d+)$', s.strip())
    return int(n.group(1)) if n else None

def calcular(xlsx, feeds):
    import openpyxl
    wb = openpyxl.load_workbook(xlsx, read_only=True)
    rows = list(wb['Catálogo Documentales'].iter_rows(values_only=True)); cab = rows[0]
    R = [dict(zip(cab, r)) for r in rows[1:] if r[0]]
    mins = [m for m in (minutos(r['Duración']) for r in R) if m]
    anios = [int(m.group(0)) for m in (re.search(r'(18|19|20)\d\d', str(r['Año'] or '')) for r in R) if m]
    dec = collections.Counter(y // 10 * 10 for y in anios)
    dirs = collections.Counter()
    for r in R:
        for d in re.split(r',|;| y | & |/|\n', str(r['Dirección'] or '')):
            d = d.strip(' .')
            if d and nz(d) not in ('none', 'varios', 'vv.aa', 'varios directores', 'anonimo', 'desconocido'): dirs[d] += 1
    pa = collections.Counter()
    for r in R:
        for p in re.split(r',|;|/| y |\n', str(r['País'] or '')):
            p = p.strip(' .-')
            if not p or p == 'None' or re.search(r'\d', p) or len(p) > 30: continue
            k = nz(p).rstrip('.'); pa[ALI.get(k, ALI.get(k.replace(' ', ''), p))] += 1
    es = []
    for f in glob.glob(feeds + '/feed_*.json'): es += json.load(open(f))['feed'].get('entry', [])
    tg = collections.Counter(c['term'].strip() for e in es for c in e.get('category', []))
    dirn = {nz(d) for d in dirs}
    paisn = {nz(p) for p in pa} | set(ALI) | {'latinoamerica', 'u.s.a.', 'palestina - israel', 'oriente medio', 'europa', 'africa', 'asia', 'euskadi',
                                              'madrid', 'barcelona', 'mexico df', 'chiapas', 'oaxaca', 'palestina', 'kurdistan', 'noruega', 'peru'}
    fuera = {'Carteles Naranjas', 'Recomendaciones Programa 1', 'Otras cosas', 'Documentales Naranjas', 'Naranjas de Hiroshima', 'Aniversario',
             '18Aniversario', 'Serie', 'pequeña', 'Licencias Copyleft', 'Licencias Libres', 'Mujeres', 'Politica'}
    temas = [(t, n) for t, n in tg.most_common(500)
             if not re.match(r'^(\d{4}s?|\d{4}-\d{4})$', t) and nz(t) not in dirn and nz(t) not in paisn and t not in fuera][:14]
    vistos = []
    try:
        from bs4 import BeautifulSoup
        req = urllib.request.Request('https://www.naranjasdehiroshima.com/', headers={'User-Agent': 'Mozilla/5.0'})
        s = BeautifulSoup(urllib.request.urlopen(req, timeout=40).read(), 'lxml')
        w = s.find(id='PopularPosts2')
        vistos = [(a.get_text(strip=True), a['href']) for a in w.select('.item-title a')][:10] if w else []
    except Exception:
        pass
    return {
        'documentales': len(R), 'horas': round(sum(mins) / 60), 'con_duracion': len(mins),
        'decadas': sorted(dec.items()), 'n_decadas': len(dec), 'anio_min': min(anios), 'anio_max': max(anios),
        'cineastas': len(dirs), 'cineastas_top': [(d, n) for d, n in dirs.most_common(12) if n >= 4],
        'paises': len(pa), 'paises_top': pa.most_common(10),
        'etiquetas': len(tg), 'temas': temas, 'directoras': tg.get('Directoras', 0), 'carteles': tg.get('Carteles Naranjas', 0),
        'cc': tg.get('Creative Commons', 0), 'vistos': vistos,
    }

def seccion(E):
    def fmt(n): return f'{n:,}'
    decmax = max(n for _, n in E['decadas'])
    barras_dec = ''.join(
        f"<div class='dc' title='{d}s: {n} documentales'><span class='dc-n'>{n}</span><i style='height:{max(2, round(100 * n / decmax))}%'></i><span class='dc-l'>{'1890' if d == 1890 else str(d)[2:] + 's'}</span></div>"
        for d, n in E['decadas'])
    def hbar(items, href=None):
        mx = max(n for _, n in items)
        out = ''
        for t, n in items:
            et = H.escape(t)
            nombre = f"<a href='{href(t)}'>{et}</a>" if href else et
            out += f"<li><span class='hb-t'>{nombre}</span><span class='hb-b'><i style='width:{round(100 * n / mx)}%'></i></span><span class='hb-n'>{n}</span></li>"
        return out
    lab = lambda t: 'https://www.naranjasdehiroshima.com/search/label/' + urllib.request.quote(t)
    vistos = ''.join(f"<li><a href='{u}'>{H.escape(t)}</a></li>" for t, u in E['vistos'])
    cine = ', '.join(f"{H.escape(d)} ({n})" for d, n in E['cineastas_top'])
    tiles = [
        (fmt(E['documentales']), 'documentales catalogados'),
        (fmt(E['horas']), 'horas de metraje'),
        (str(E['n_decadas']), f"décadas · {E['anio_min']}–{E['anio_max']}"),
        (str(E['paises']), 'países'),
        (f"{E['cineastas'] // 50 * 50}+", 'cineastas'),
        (str(E['directoras']), 'entradas de directoras'),
        (str(E['carteles']), 'Carteles Naranjas diseñados'),
        (fmt(E['etiquetas']), 'etiquetas para explorar'),
    ]
    tiles_html = ''.join(f"<div class='tile'><b>{v}</b><span>{l}</span></div>" for v, l in tiles)
    css = """
.tiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--linea);border:1px solid var(--linea);margin-bottom:40px}
.tile{background:var(--blanco);padding:18px 18px 16px;display:flex;flex-direction:column;gap:4px}
.tile b{font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:46px;line-height:1;color:var(--naranja-osc)}
.tile span{font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--gris)}
.graf{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,460px),1fr));gap:40px 48px}
.graf h3{margin:0 0 4px;font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:28px;text-transform:uppercase;line-height:1.05}
.graf .nota{margin:0 0 14px;font-size:14px;color:var(--gris-m)}
.dcs{display:flex;align-items:flex-end;gap:6px;height:220px;padding-top:22px;border-bottom:1px solid var(--gris)}
.dc{flex:1;height:100%;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;position:relative}
.dc i{display:block;width:100%;max-width:38px;background:var(--naranja);border-radius:4px 4px 0 0}
.dc:hover i{background:var(--naranja-osc)}
.dc-n{font-family:'DM Mono',monospace;font-size:11px;color:var(--gris);margin-bottom:4px}
.dc-l{position:absolute;bottom:-22px;font-family:'DM Mono',monospace;font-size:11px;color:var(--gris-m)}
.hb{list-style:none;margin:0;padding:0}
.hb li{display:grid;grid-template-columns:minmax(0,13em) minmax(0,1fr) 3em;gap:12px;align-items:center;padding:5px 0}
.hb-t{font-size:14px;line-height:1.3}.hb-t a{color:var(--negro);text-decoration:none}.hb-t a:hover{color:var(--naranja-osc);text-decoration:underline}
.hb-b{height:12px;background:var(--crema-o);border-radius:0 4px 4px 0}.hb-b i{display:block;height:100%;background:var(--naranja);border-radius:0 4px 4px 0}
.hb li:hover .hb-b i{background:var(--naranja-osc)}
.hb-n{font-family:'DM Mono',monospace;font-size:12px;color:var(--gris);text-align:right}
.vistos{margin:0;padding-left:1.6em;font-size:15px;line-height:1.5}.vistos li{padding:4px 0}.vistos li::marker{font-family:'Bebas Neue',sans-serif;color:var(--naranja-osc);font-size:20px}
.vistos a{color:var(--negro);text-decoration:none}.vistos a:hover{color:var(--naranja-osc);text-decoration:underline}
.cine{margin-top:14px;font-size:14px;color:var(--gris)}
@media(max-width:820px){.tiles{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:620px){.hb li{grid-template-columns:minmax(0,9em) minmax(0,1fr) 2.6em}.tile b{font-size:38px}.dcs{gap:3px}.dc-l{font-size:9px}}
"""
    html = f"""<section id="cifras"><div class="wrap"><h2 class="sec">El archivo en cifras</h2>
<div class="tiles">{tiles_html}</div>
<div class="graf">
  <figure style="margin:0"><h3>Documentales por década</h3><p class="nota">Por año de realización · {E['documentales']} documentales catalogados</p>
    <div class="dcs" role="img" aria-label="Documentales por década de realización">{barras_dec}</div></figure>
  <figure style="margin:0"><h3>Temas más tratados</h3><p class="nota">Etiquetas del blog con más entradas</p><ol class="hb">{hbar(E['temas'][:12], lab)}</ol></figure>
  <figure style="margin:0"><h3>Países más presentes</h3><p class="nota">País de producción de los documentales</p><ol class="hb">{hbar(E['paises_top'])}</ol>
    <p class="cine"><b>Cineastas más presentes:</b> {cine}.</p></figure>
  <figure style="margin:0"><h3>Los más vistos</h3><p class="nota">Las entradas más leídas del blog desde siempre</p><ol class="vistos">{vistos}</ol></figure>
</div></div></section>"""
    return css, html
