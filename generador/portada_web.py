"""Portada animada por capas para la web del libro. Reutiliza el diseño (CSS en mm) de la portada impresa."""
import os, re, shutil

def construir(HERE, OUT):
    os.makedirs(os.path.join(OUT, 'portada'), exist_ok=True)
    for src, dst in (('fondo_portada.jpg', 'fondo.jpg'), ('boom.webp', 'sam-l.webp'), ('cam.webp', 'sam-r.webp'), ('titulo_logo.png', 'titulo.png')):
        shutil.copy(os.path.join(HERE, src), os.path.join(OUT, 'portada', dst))
    css = open(os.path.join(HERE, 'libro.css'), encoding='utf-8').read()
    a = css.index('/* Portada 20 aniversario'); b = css.index('/* Texto de presentación */')
    base = css[a:b]
    base = re.sub(r'\.portada\{[^}]*\}', '.portada{position:absolute;left:0;top:0;width:170mm;height:240mm;overflow:hidden;background:#120E0B;color:#F3E9D6;text-align:center;transform-origin:0 0}', base, count=1)
    base = base.replace('.pt-', '.portada .pt-')
    anim = """
.portada-wrap{position:relative;width:100%;aspect-ratio:170/240;border-radius:3px;overflow:hidden;box-shadow:0 24px 50px rgba(0,0,0,.6);display:block;cursor:pointer}
.portada .pt-fondo{position:absolute;inset:-6% -4%;background:url('portada/fondo.jpg') center/cover no-repeat;animation:pt-deriva 38s ease-in-out infinite alternate;will-change:transform}
.portada .pt-polvo{position:absolute;inset:0;pointer-events:none;mix-blend-mode:screen;opacity:.5;
  background:repeating-linear-gradient(90deg,transparent 0 37mm,rgba(255,240,220,.35) 37mm 37.2mm,transparent 37.2mm 91mm),repeating-linear-gradient(90deg,transparent 0 63mm,rgba(255,240,220,.25) 63mm 63.15mm,transparent 63.15mm 140mm);
  animation:pt-rayas 1.3s steps(1) infinite}
.portada .pt-parpadeo{position:absolute;inset:0;pointer-events:none;background:#000;opacity:0;animation:pt-parpadeo 5.5s infinite}
.portada .pt-rayos{animation:pt-gira 90s linear infinite;will-change:transform}
.portada .pt-lata-cara{animation:pt-gira 26s linear infinite reverse}
.portada .pt-etq{animation:pt-vaiven 7s ease-in-out infinite alternate;transform-origin:50% -10%}
.portada .pt-sam-l{animation:pt-entra-l 1.4s cubic-bezier(.2,.8,.2,1) both,pt-guardia 4.6s 1.4s ease-in-out infinite alternate;transform-origin:50% 100%}
.portada .pt-sam-r{animation:pt-entra-r 1.4s .15s cubic-bezier(.2,.8,.2,1) both,pt-guardia 5.2s 1.6s ease-in-out infinite alternate-reverse;transform-origin:50% 100%}
.portada .pt-nombre{animation:pt-proyecta 1.6s .2s ease-out both}
.portada .pt-nombre img{animation:pt-titila 9s 2s infinite}
.portada .pt-jp{animation:pt-aparece 2.4s .8s ease-out both}
.portada .pt-claqueta{animation:pt-claqueta .9s .5s cubic-bezier(.3,1.6,.5,1) both}
.portada .pt-fechas{animation:pt-aparece 1.4s 1.2s ease-out both}
@keyframes pt-gira{to{transform:rotate(360deg)}}
@keyframes pt-deriva{from{transform:translate3d(0,-2%,0) scale(1.02)}to{transform:translate3d(-1.5%,3%,0) scale(1.05)}}
@keyframes pt-vaiven{from{transform:rotate(-5.5deg)}to{transform:rotate(-2.5deg)}}
@keyframes pt-guardia{from{transform:translateY(0) rotate(0)}to{transform:translateY(-1.6mm) rotate(-1.2deg)}}
@keyframes pt-entra-l{from{opacity:0;transform:translateX(-40mm)}to{opacity:1;transform:none}}
@keyframes pt-entra-r{from{opacity:0;transform:translateX(40mm)}to{opacity:1;transform:none}}
@keyframes pt-proyecta{0%{opacity:0;filter:blur(3mm) brightness(2.2)}55%{opacity:1;filter:blur(.4mm) brightness(1.4)}100%{opacity:1;filter:none}}
@keyframes pt-titila{0%,96%,100%{opacity:1}97%{opacity:.55}98%{opacity:.95}99%{opacity:.7}}
@keyframes pt-aparece{from{opacity:0;transform:translateY(3mm)}to{opacity:1;transform:none}}
@keyframes pt-claqueta{from{transform:rotate(-7deg) translateY(-3mm);transform-origin:0 100%}to{transform:none;transform-origin:0 100%}}
@keyframes pt-rayas{0%{background-position:0 0,0 0;opacity:.45}33%{background-position:-23mm 0,41mm 0;opacity:.2}66%{background-position:17mm 0,-12mm 0;opacity:.55}}
@keyframes pt-parpadeo{0%,90%,100%{opacity:0}91%{opacity:.08}92%{opacity:0}94%{opacity:.05}95%{opacity:0}}
.portada.pausa *,.portada.pausa{animation-play-state:paused!important}
@media (prefers-reduced-motion:reduce){.portada *,.portada{animation:none!important}}
.portada .pt-etq-num b,.portada .pt-anios,.portada .pt-fechas,.portada .pt-etq-num i{text-transform:uppercase}
"""
    html = """<a class="portada-wrap" href="lector.html" aria-label="Leer el libro en línea">
  <div class="portada" aria-hidden="true">
    <div class="pt-fondo"></div>
    <div class="pt-top">
      <div class="pt-libro">Libro de</div>
      <div class="pt-nombre"><img src="portada/titulo.png" alt=""></div>
      <div class="pt-etiqueta">Edición 20 aniversario</div>
    </div>
    <div class="pt-claqueta"></div>
    <div class="pt-escena">
      <div class="pt-rayos"></div>
      <div class="pt-lata">
        <div class="pt-lata-cara"></div>
        <div class="pt-etq">
          <div class="pt-etq-top"><span>Naranjas de Hiroshima</span><span>NdH</span></div>
          <div class="pt-etq-num"><b id="pt-cuenta">20</b><i>años</i></div>
          <div class="pt-etq-bot"><span>2007 — 2027</span><span>Lata 020</span></div>
        </div>
      </div>
      <img class="pt-sam pt-sam-l" src="portada/sam-l.webp" alt="">
      <img class="pt-sam pt-sam-r" src="portada/sam-r.webp" alt="">
      <div class="pt-jp pt-jp-l">ドキュメンタリー映画</div>
      <div class="pt-jp pt-jp-r">広島オレンジ</div>
      <div class="pt-anios">difundiendo cine documental</div>
    </div>
    <div class="pt-fechas">2007 <i></i> 2027</div>
    <div class="pt-pie">{N} entradas · Cine documental · Creative Commons</div>
    <div class="pt-polvo"></div>
    <div class="pt-parpadeo"></div>
  </div>
</a>"""
    js = """
(function(){
  var wrap = document.querySelector('.portada-wrap'), p = wrap && wrap.querySelector('.portada');
  if (!p) return;
  var MM = 96 / 25.4, ANCHO = 170 * MM;
  function escala(){ p.style.transform = 'scale(' + (wrap.clientWidth / ANCHO) + ')'; }
  escala(); if (window.ResizeObserver) new ResizeObserver(escala).observe(wrap); else addEventListener('resize', escala);
  var quieto = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!quieto) {
    var n = document.getElementById('pt-cuenta'), i = 0;
    n.textContent = '00';
    setTimeout(function paso(){ i++; n.textContent = (i < 10 ? '0' : '') + i; if (i < 20) setTimeout(paso, 28 + i * 4); }, 900);
    var fondo = p.querySelector('.pt-fondo'), rayos = p.querySelector('.pt-escena');
    wrap.addEventListener('pointermove', function(e){
      var r = wrap.getBoundingClientRect(), x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
      rayos.style.transform = 'translate(' + (x * -6) + 'px,' + (y * -6) + 'px)';
      fondo.style.translate = (x * 14) + 'px ' + (y * 14) + 'px';
    });
    wrap.addEventListener('pointerleave', function(){ rayos.style.transform = ''; fondo.style.translate = ''; });
    if (window.IntersectionObserver) new IntersectionObserver(function(es){ p.classList.toggle('pausa', !es[0].isIntersecting); }).observe(wrap);
    document.addEventListener('visibilitychange', function(){ p.classList.toggle('pausa', document.hidden); });
  }
})();
"""
    return base + anim, html, js
