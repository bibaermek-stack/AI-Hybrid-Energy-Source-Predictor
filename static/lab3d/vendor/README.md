# three.js for the 3D lab

`three-lab.min.js` is three.js r160 (MIT, © three.js authors) cut down to the classes
`lab3d.js` imports, plus `OrbitControls` and `OBJLoader`. It is bundled here so the
lab needs no CDN: the page is served from the site (Streamlit component) and from the
API (the app's WebView), and a blocked or slow CDN used to leave the 3D view empty.

Rebuild after importing a new class in `lab3d.js` (add it to `three-lab.entry.js`):

```bash
npm install three@0.160.0 esbuild@0.24.0
npx esbuild three-lab.entry.js --bundle --format=esm --minify --legal-comments=inline \
  --outfile=three-lab.min.js
```
