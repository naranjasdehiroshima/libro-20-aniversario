"""Los 21 dossiers temáticos, maquetados como una segunda parte del libro.
Toma el HTML publicado de cada dossier y lo adapta a página impresa:
enlaces internos con número de página, línea de tiempo numerada y relación final de películas."""
import os, re, json, html as H, hashlib
from bs4 import BeautifulSoup

DOS = os.environ.get('NDH_DOSSIERS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dossier'))
GC = os.path.join(DOS, '..', 'dossier-guerra-civil-blogger.html')
B = 'https://www.naranjasdehiroshima.com/'


def norm_url(u):
    u = (u or '').strip().split('#')[0].split('?')[0]
    return u.replace('http://', 'https://').replace('://naranjasdehiroshima.com', '://www.naranjasdehiroshima.com')


def lista():
    """[(n, titulo, subtitulo, ruta_html, url_web)] en orden."""
    import sys
    sys.path.insert(0, DOS)
    import urls_reales as U
    res = {d['n']: d for d in json.load(open(os.path.join(DOS, 'salida', '_resumen.json')))}
    out = [(1, 'La Guerra Civil española en el cine documental', 'Dossier nº 1', GC, B + 'p/dossier-guerra-civil-espanola.html')]
    for n in sorted(res):
        if n == 1: continue
        d = res[n]
        out.append((n, d['t'], d['sub'], os.path.join(DOS, 'salida', d['slug'] + '.html'), U.URL[n]))
    return out


def construir(local, en_libro):
    """local(url)->ruta de imagen; en_libro: {url_normalizada: id_ancla}. Devuelve (css, html, toc)."""
    ds = lista()
    web2n = {norm_url(u): n for n, _, _, _, u in ds}
    web2n[norm_url(B + 'p/dossiers-tematicos-indice.html')] = 0
    web2n[norm_url(B + 'p/dossiers-tematicos.html')] = 0
    css = None
    partes, toc = [], []
    for n, titulo, sub, ruta, url in ds:
        raw = open(ruta, encoding='utf-8').read()
        m = re.search(r'<style>(.*?)</style>', raw, re.S)
        if n != 1 and css is None: css = m.group(1)
        s = BeautifulSoup(raw, 'lxml')
        dz = s.select_one('.dz')
        for t in dz.select('script, style, .dz-volver, .dz-herr, .dz-citar, button, input, select, .ndh-sr'):
            t.decompose()
        pre = f'd{n}-'
        for t in dz.select('[id]'):
            t['id'] = pre + t['id']
        dz['id'] = f'dossier-{n}'
        # fichas numeradas
        num_de_url, filas = {}, []
        for k, art in enumerate(dz.select('article.dz-ficha'), 1):
            a = art.select_one('h4 a')
            u = norm_url(a.get('href') if a else '')
            num_de_url.setdefault(u, k)
            art['id'] = f'{pre}f{k}'
            h4 = art.select_one('h4')
            marca = s.new_tag('span', **{'class': 'dz-num'}); marca.string = str(k)
            h4.insert(0, marca)
            meta = art.select_one('.dz-meta')
            filas.append((k, a.get_text(' ', strip=True) if a else '', meta.get_text(' ', strip=True) if meta else '', u, art.get('data-sec', '')))
            for at in [x for x in art.attrs if x.startswith('data-')]:
                del art[at]
        # línea de tiempo numerada, reconstruida para papel
        lt = dz.select_one('.dz-lt')
        if lt:
            pts = []
            for p in lt.select('.dz-lt-p'):
                x = float(re.search(r'left:([\d.]+)%', p.get('style', '')).group(1))
                u = norm_url(p.get('href'))
                if u in num_de_url: pts.append((x, num_de_url[u], 'p'))
                else: pts.append((x, None, 'o'))
            years = [(float(re.search(r'left:([\d.]+)%', y['style']).group(1)), y.get_text()) for y in lt.select('.dz-lt-y')]
            pts.sort()
            filas_lt = []  # última x ocupada por fila
            html_pts = ''
            for x, k, tipo in pts:
                for r_i, ult in enumerate(filas_lt):
                    if x - ult >= 2.9: filas_lt[r_i] = x; break
                else:
                    filas_lt.append(x); r_i = len(filas_lt) - 1
                if k is None:
                    html_pts += f'<span class="lt-o" style="left:{x:.2f}%;bottom:{r_i * 4.7:.1f}mm"></span>'
                else:
                    html_pts += f'<a class="lt-p" href="#{pre}f{k}" style="left:{x:.2f}%;bottom:{r_i * 4.7:.1f}mm">{k}</a>'
            alto = max(1, len(filas_lt)) * 5.2 + 2
            ys = ''.join(f'<span class="lt-y" style="left:{x:.2f}%">{H.escape(t)}</span>' for x, t in years)
            nuevo = BeautifulSoup(f'<div class="lt" style="height:{alto:.1f}mm">{html_pts}{ys}</div>', 'lxml').div
            lt.replace_with(nuevo)
            ley = dz.select_one('.dz-tit-lt')
            if ley:
                ley.string = 'Las películas en el tiempo · año de producción · cada número remite a su ficha'
        # enlaces
        for a in dz.select('a[href]'):
            u = norm_url(a['href'])
            if a['href'].startswith('#'):
                a['href'] = '#' + pre + a['href'][1:] if not a['href'].startswith('#' + pre) else a['href']
                continue
            if u in en_libro:
                a['href'] = '#' + en_libro[u]
                if not a.find('img') and 'lt-p' not in (a.get('class') or []):
                    a['class'] = (a.get('class') or []) + ['ref']
                    a['data-pag'] = ''
            elif u in web2n:
                a['href'] = '#dossiers' if web2n[u] == 0 else f'#dossier-{web2n[u]}'
                a['class'] = (a.get('class') or []) + ['ref']; a['data-pag'] = ''
        # «Leer la entrada →» pasa a ser la página de la entrada
        for acc in dz.select('.dz-acc'):
            a = acc.find('a')
            if a and a['href'].startswith('#e'):
                a.string = 'Entrada completa'
                a['class'] = ['ref', 'ref-ent']
            elif a:
                a.string = 'Entrada en el blog'
        for a in dz.select('a.dz-img'):
            a.attrs.pop('tabindex', None); a.attrs.pop('aria-hidden', None)
        for img in dz.select('img'):
            src = img.get('src', '')
            img.attrs.pop('loading', None)
            if src.startswith('http'): img['src'] = local(src)
        # relación final de películas
        nombres_sec = {sec.get('id', '')[len(pre) + 3:]: (sec.select_one('h3').contents[0] if sec.select_one('h3') else '') for sec in dz.select('section.dz-sec')}
        trs = ''
        for k, t, meta, u, sec in filas:
            dest = en_libro.get(u)
            pag = f'<a class="ref ref-n" href="#{dest}" data-pag=""></a>' if dest else '—'
            trs += f'<tr><td class="c-n"><a href="#{pre}f{k}">{k}</a></td><td>{H.escape(t)}</td><td>{H.escape(meta)}</td><td class="c-p">{pag}</td></tr>'
        rel = f'<section class="dz-rel"><h3>Relación de películas</h3><table><thead><tr><th>Nº</th><th>Título</th><th>Ficha</th><th>Pág.</th></tr></thead><tbody>{trs}</tbody></table></section>'
        dz.append(BeautifulSoup(rel, 'lxml').section)
        # cabecera del dossier en el libro
        cab = dz.select_one('.dz-cab')
        h1 = s.new_tag('h1', **{'class': 'dz-h1'}); h1.string = titulo
        cab.insert(1, h1)
        portadilla = f'<section class="dz-portadilla" id="dossier-{n}-p"><div class="dp-n">Dossier<b>{n}</b></div><div class="dp-t">{H.escape(titulo)}</div><div class="dp-s">{H.escape(sub if n != 1 else "La guerra, la revolución y el exilio en el archivo de Naranjas de Hiroshima")}</div></section>'
        partes.append(portadilla + str(dz))
        toc.append((n, titulo))
    # índice general de la segunda parte
    filas_toc = ''.join(f'<li><a class="ref" data-pag="" href="#dossier-{n}-p"><span><i>{n}</i>{H.escape(t)}</span></a></li>' for n, t in toc)
    apertura = f'''<section class="anio parte" id="dossiers"><div class="anio-num">Dossiers</div><div class="anio-sub">Segunda parte · {len(toc)} recorridos temáticos por el archivo</div></section>
<section class="dz-entrada"><h2>Los dossiers</h2>
<p>Los dossiers temáticos nacieron en 2026, en la web, para recorrer el archivo por temas y por cineastas. Cada uno reúne las entradas del blog sobre un asunto, las ordena en capítulos y añade a cada película una ficha breve con una cita de su reseña. Aquí se reproducen completos, tal como están en la web, con dos cambios para el papel: cada título remite a la página del libro donde está la entrada, y en la línea del tiempo cada número corresponde a una ficha.</p>
<ol class="dz-toc">{filas_toc}</ol></section>'''
    css_libro = css + PRINT_CSS
    return css_libro, apertura + '\n'.join(partes), toc


PRINT_CSS = r'''
/* ---- adaptación de los dossiers al libro ---- */
.dz{zoom:.74;break-before:page;padding-top:2mm}
.dz-portadilla{break-before:page;break-after:page;height:190mm;display:flex;flex-direction:column;justify-content:flex-end;padding:0 0 18mm 0;border-left:3mm solid var(--naranja);padding-left:8mm}
.dp-n{font-family:'DM Mono',monospace;font-size:9pt;letter-spacing:.24em;text-transform:uppercase;color:var(--gris-medio)}
.dp-n b{display:block;font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:120pt;line-height:.82;letter-spacing:0;color:var(--naranja)}
.dp-t{font-family:'Bebas Neue',sans-serif;font-size:30pt;line-height:1.02;text-transform:uppercase;margin-top:4mm;padding-top:1.5mm}
.dp-s{font-style:italic;color:var(--gris);margin-top:3mm;max-width:105mm}
.dz-h1{font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:46px;line-height:1.02;text-transform:uppercase;margin:6px 0 4px;padding-top:4px}
.dz-cab{break-inside:avoid}
.dz-sec h3,.dz-rel h3{break-after:avoid}
.dz-sec>.dz-desc{break-after:avoid}
.dz-ficha{break-inside:avoid}
.dz-num{display:inline-block;min-width:24px;height:24px;line-height:24px;margin-right:9px;border-radius:12px;background:var(--n);color:#fff;font-family:'DM Mono',monospace;font-size:12px;text-align:center;vertical-align:3px;padding:0 5px}
.dz-filmo-t tr,.dz-rel tr{break-inside:avoid}
.dz-indice{break-inside:avoid}
a.ref::after{content:" · p. " attr(data-pag);font-family:'DM Mono',monospace;font-size:.78em;color:var(--gm);white-space:nowrap}
a.ref[data-pag=""]::after{content:""}
.dz-acc a.ref-ent{text-decoration:none}
.dz-acc a.ref-ent::after{content:" · página " attr(data-pag)}
.dz-tabla-wrap{overflow:visible!important}
/* línea de tiempo numerada */
.lt{position:relative;margin:30px 16px 46px;border-bottom:2px solid var(--ne);break-inside:avoid}
.dz .lt-p{position:absolute;width:17px;height:17px;margin-left:-8.5px;margin-bottom:-8.5px;border-radius:50%;background:var(--n);color:#fff;font-family:'DM Mono',monospace;font-size:8.5px;letter-spacing:-.04em;line-height:17px;text-align:center;text-decoration:none;border:1.5px solid #fff}
.lt-o{position:absolute;width:10px;height:10px;margin-left:-5px;margin-bottom:-5px;border-radius:50%;background:var(--no);opacity:.7;border:1.5px solid #fff}
.lt-y{position:absolute;bottom:-26px;transform:translateX(-50%);font-family:'DM Mono',monospace;font-size:11px;color:var(--gm)}
/* relación final */
.dz-rel{margin-top:30px;break-before:auto}
.dz-rel h3{font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:30px;text-transform:uppercase;margin:0 0 8px;padding-top:10px;border-top:3px solid var(--ne)}
.dz-rel table{width:100%;border-collapse:collapse;font-size:12.5px;line-height:1.4}
.dz-rel th{font-family:'DM Mono',monospace;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;text-align:left;color:var(--gm);border-bottom:1.5px solid var(--ne);padding:5px 6px}
.dz-rel td{border-bottom:1px solid var(--l);padding:5px 6px;vertical-align:top}
.dz-rel td:nth-child(3){color:var(--g);font-size:11.5px}
.dz-rel .c-n,.dz-rel .c-p{font-family:'DM Mono',monospace;white-space:nowrap;color:var(--gm)}
.dz-rel .c-n a{color:var(--no)}
.dz-rel a.ref-n::after{content:attr(data-pag);font-size:1em;color:var(--ne)}
/* índice de la segunda parte */
.dz-entrada{break-before:page;break-after:page}
.dz-entrada h2{font-family:'Bebas Neue',sans-serif;font-weight:400;font-size:32pt;text-transform:uppercase;margin:0 0 5mm;border-bottom:.3mm solid var(--negro);padding-top:1.5mm}
.dz-entrada p{text-align:justify;hyphens:auto}
.dz-toc{list-style:none;margin:6mm 0 0;padding:0}
.dz-toc li{border-bottom:.2mm solid var(--linea);padding:1.6mm 0}
.dz-toc a{display:flex;justify-content:space-between;align-items:baseline;color:var(--negro)}
.dz-toc a::after{content:attr(data-pag);font-family:'DM Mono',monospace;color:var(--gris-medio);font-size:8pt}
.dz-toc i{font-style:normal;font-family:'DM Mono',monospace;color:var(--naranja-osc);display:inline-block;width:8mm}
'''
