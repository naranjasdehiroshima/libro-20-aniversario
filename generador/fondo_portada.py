"""Fondo de la portada: tiras de 16mm con fotogramas de documentales del archivo, en duotono naranja."""
import glob, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageFont

FOTOS, OUT = sys.argv[1], sys.argv[2]
random.seed(20)
W, H = 2008, 2835                      # 170 × 240 mm a 300 ppp
BASE = (18, 13, 10)
fotos = sorted(glob.glob(FOTOS + '/*.jpg'))

def duotono(im):
    g = ImageOps.grayscale(im)
    g = ImageOps.autocontrast(g, cutoff=2)
    return ImageOps.colorize(g, black=(20, 12, 8), mid=(190, 78, 26), white=(250, 222, 186), midpoint=110)

try:
    fuente = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 15)
except Exception:
    fuente = ImageFont.load_default()

def tira(largo, fotos_tira, desfase):
    """Una tira de 16mm de doble perforación, en vertical."""
    ancho = 430
    t = Image.new('RGB', (ancho, largo), (24, 17, 13))
    d = ImageDraw.Draw(t)
    perf_w, perf_h, paso = 34, 26, 64            # perforaciones a ambos lados
    for y in range(-desfase % paso, largo, paso):
        for x in (16, ancho - 16 - perf_w):
            d.rounded_rectangle([x, y, x + perf_w, y + perf_h], radius=6, fill=(238, 176, 112))
    fw = ancho - 2 * 70; fh = int(fw / 1.37); hueco = 24
    y = -desfase % (fh + hueco) - (fh + hueco)
    i = 0
    while y < largo:
        f = Image.open(next(fotos_tira)).convert('RGB')
        f = ImageOps.fit(f, (fw, fh), centering=(0.5, 0.4))
        f = duotono(f)
        t.paste(f, (70, y))
        d.rectangle([70, y, 70 + fw, y + fh], outline=(10, 7, 5), width=3)
        # código de borde, como en las películas reales
        d.text((ancho - 60, y + fh // 2), f'NdH {2007 + (i % 20)}', fill=(232, 196, 120), font=fuente, anchor='mm')
        y += fh + hueco; i += 1
    # el texto de borde va girado sobre el margen
    return t

lienzo = Image.new('RGB', (W, H), BASE)
random.shuffle(fotos)
n_tiras = 5
fuente_fotos = iter(fotos)          # cada fotograma, una película distinta: nunca se repite
xs = [-150, 300, 760, 1220, 1680]
for k, x in enumerate(xs):
    largo = int(H * 1.35)
    t = tira(largo, fuente_fotos, desfase=random.randint(0, 300))
    t = t.convert('RGBA').rotate(-9 if k % 2 == 0 else -7, resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0, 0))
    pos = (x - 120, -int(H * 0.17) + random.randint(-60, 60))
    sombra = Image.new('RGBA', t.size, (0, 0, 0, 0)); sombra.putalpha(t.getchannel('A').point(lambda v: int(v * 0.6)))
    lienzo.paste((0, 0, 0), (pos[0] + 18, pos[1] + 10), sombra.getchannel('A').filter(ImageFilter.GaussianBlur(14)))
    lienzo.paste(t, pos, t)

# rayas y polvo de proyección
d = ImageDraw.Draw(lienzo)
for _ in range(14):
    x = random.randint(0, W)
    d.line([(x, random.randint(0, H // 3)), (x + random.randint(-6, 6), random.randint(H // 2, H))], fill=(240, 220, 200), width=random.choice([1, 2]))
for _ in range(260):
    x, y, r = random.randint(0, W), random.randint(0, H), random.choice([1, 1, 2, 3])
    c = random.choice([(10, 7, 5), (245, 230, 210)])
    d.ellipse([x, y, x + r, y + r], fill=c)

# grano
ruido = Image.effect_noise((W, H), 38).convert('L')
lienzo = Image.blend(lienzo, Image.merge('RGB', (ruido, ruido, ruido)), 0.07)

# viñeta y oscurecimiento arriba/abajo para que se lea el texto
mascara = Image.radial_gradient('L').resize((W, H)).point(lambda v: max(0, min(255, (v - 90) * 2)))
oscuro = Image.new('RGB', (W, H), (12, 8, 6))
lienzo = Image.composite(oscuro, lienzo, Image.eval(mascara, lambda v: int(v * 0.85)))
grad = Image.linear_gradient('L').resize((W, H))
arriba = Image.eval(grad.transpose(Image.FLIP_TOP_BOTTOM), lambda v: max(0, (v - 150)) * 2)
abajo = Image.eval(grad, lambda v: max(0, (v - 175)) * 2)
lienzo = Image.composite(oscuro, lienzo, Image.eval(Image.merge('L', (arriba,)), lambda v: min(220, v)))
lienzo = Image.composite(oscuro, lienzo, Image.eval(abajo, lambda v: min(230, v)))
lienzo.save(OUT, 'JPEG', quality=84, optimize=True, progressive=True)
print('ok', OUT)
