# Generador del Libro de Naranjas de Hiroshima

Para el próximo aniversario:

1. Descarga las entradas del blog (feed JSON) en una carpeta `feeds`, de 150 en 150:
   `https://www.naranjasdehiroshima.com/feeds/posts/default?alt=json&max-results=150&start-index=1`
   (y 151, 301, 451, 601…), guardadas como `feed_1.json`, `feed_151.json`…
2. `pip install beautifulsoup4 lxml pillow qrcode markdown pypdf playwright` y `playwright install chromium`
3. Libro: `python3 libro.py feeds 2007 2027 "" salida`
4. Web y tomos: `python3 sitio.py feeds salida/Libro-*.pdf salida/portada.jpg intro.md web`

El texto de presentación está en `intro.md`; lo que va entre [corchetes] sale resaltado.
