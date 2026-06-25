// Generátor grafiky pro Google Play listing (ikona 512x512 + feature 1024x500).
// Renderuje HTML přes Playwright Chromium do PNG v přesných rozměrech.
// Spuštění (z C:\projekty\STRATEGIE): node docs/google_play_grafika/gen.mjs
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import path from 'path';

const outDir = path.dirname(fileURLToPath(import.meta.url));

// Logo STRATEGIE = 3 rostoucí sloupce (teal -> zelená) + datový bod.
// Přesně dle ic_launcher_foreground.xml (viewport 108x108).
const LOGO = `
<svg viewBox="0 0 108 108" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="2.2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <g filter="url(#glow)">
    <rect x="30"   y="56" width="13" height="19" rx="2.6" fill="#2DD4BF"/>
    <rect x="47.5" y="44" width="13" height="31" rx="2.6" fill="#34D399"/>
    <rect x="65"   y="31" width="13" height="44" rx="2.6" fill="#4ADE80"/>
    <circle cx="71.5" cy="20" r="5.5" fill="#A7F3D0"/>
  </g>
</svg>`;

const ICON_HTML = `<!doctype html><html><head><meta charset="utf-8"><style>
  html,body{margin:0;padding:0;width:512px;height:512px;overflow:hidden}
  .canvas{width:512px;height:512px;position:relative;
    background:radial-gradient(120% 120% at 50% 38%, #102338 0%, #0a1626 45%, #050b14 100%);}
  .glow{position:absolute;inset:0;
    background:radial-gradient(38% 34% at 50% 44%, rgba(45,212,191,.28) 0%, rgba(45,212,191,0) 70%);}
  .logo{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
    width:300px;height:300px;filter:drop-shadow(0 14px 28px rgba(0,0,0,.45));}
  .logo svg{width:100%;height:100%}
</style></head><body>
  <div class="canvas"><div class="glow"></div><div class="logo">${LOGO}</div></div>
</body></html>`;

const FEATURE_HTML = `<!doctype html><html><head><meta charset="utf-8"><style>
  html,body{margin:0;padding:0;width:1024px;height:500px;overflow:hidden;
    font-family:'Segoe UI',system-ui,Arial,sans-serif}
  .canvas{width:1024px;height:500px;position:relative;
    background:linear-gradient(115deg, #0c1d33 0%, #0a1626 55%, #060d18 100%);}
  .bigbars{position:absolute;right:-40px;top:-30px;width:560px;height:560px;opacity:.10}
  .glow{position:absolute;left:6%;top:18%;width:420px;height:420px;
    background:radial-gradient(closest-side, rgba(45,212,191,.22), rgba(45,212,191,0));}
  .wrap{position:absolute;left:80px;top:0;height:500px;display:flex;flex-direction:column;
    justify-content:center;gap:18px;width:760px}
  .row{display:flex;align-items:center;gap:26px}
  .mark{width:108px;height:108px}
  .mark svg{width:100%;height:100%}
  .name{font-size:78px;font-weight:800;color:#fff;letter-spacing:3px;line-height:1}
  .tag{font-size:30px;font-weight:600;color:#9fe7d8;letter-spacing:.5px;margin-left:4px}
  .sub{font-size:21px;font-weight:500;color:#aebfcf;margin-left:4px;margin-top:2px}
</style></head><body>
  <div class="canvas">
    <div class="bigbars">${LOGO}</div>
    <div class="glow"></div>
    <div class="wrap">
      <div class="row">
        <div class="mark">${LOGO}</div>
        <div class="name">STRATEGIE</div>
      </div>
      <div class="tag">Firma v kapse — chytře a přehledně</div>
      <div class="sub">Docházka · lidé · komunikace · firemní informace · AI asistent</div>
    </div>
  </div>
</body></html>`;

async function shot(browser, html, w, h, file) {
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
  await page.setContent(html, { waitUntil: 'networkidle' });
  await page.screenshot({ path: path.join(outDir, file), clip: { x: 0, y: 0, width: w, height: h } });
  await page.close();
  console.log('OK ->', file, w + 'x' + h);
}

const browser = await chromium.launch();
await shot(browser, ICON_HTML, 512, 512, 'icon_512.png');
await shot(browser, FEATURE_HTML, 1024, 500, 'feature_1024x500.png');
await browser.close();
console.log('HOTOVO');
