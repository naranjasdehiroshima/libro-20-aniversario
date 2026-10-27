# Generador del Libro de Naranjas de Hiroshima

Para el próximo aniversario:

1. Descarga las entradas del blog **año por año** (la paginación normal del feed de Blogger se salta entradas):
   ```
   for y in $(seq 2007 2027); do
     curl -s "https://www.naranjasdehiroshima.com/feeds/posts/default?alt=json&max-results=150&orderby=published&published-min=$y-01-01T00:00:00-06:00&published-max=$((y+1))-01-01T00:00:00-06:00" -o feeds/feed_$y.json
   done
   ```
2. `pip install beautifulsoup4 lxml pillow qrcode markdown pypdf playwright` y `playwright install chromium`
3. Libro: `python3 libro.py feeds 2007 2027 "" salida`
4. Web, tomos, lector y portada animada: `python3 sitio.py feeds salida/Libro-*.pdf salida/portada.jpg intro.md web`

El texto de presentación está en `intro.md`; lo que va entre [corchetes] sale resaltado.
