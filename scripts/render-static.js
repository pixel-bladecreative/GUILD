// Render every angle x size of the static ad to PNG.
// Usage: node scripts/render-static.js [angleId]
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const { serve, ROOT } = require("./serve");

const SIZES = [
  { id: "meta-1x1", w: 1080, h: 1080 },
  { id: "meta-4x5", w: 1080, h: 1350 },
  { id: "meta-9x16", w: 1080, h: 1920 },
  { id: "gdn-1.91x1", w: 1200, h: 628 },
  { id: "gdn-1x1", w: 1200, h: 1200 },
  { id: "gdn-4x5", w: 960, h: 1200 },
];
const LOGOS = [{ id: "logo-1x1", w: 1200, h: 1200 }, { id: "logo-4x1", w: 1200, h: 300 }];

(async () => {
  const only = process.argv[2];
  const angles = JSON.parse(fs.readFileSync(path.join(ROOT, "copy/angles.json"))).angles
    .filter(a => !only || a.id === only);
  const outDir = path.join(ROOT, "creatives/out");
  fs.mkdirSync(outDir, { recursive: true });
  const { srv, base } = await serve();
  const browser = await chromium.launch();
  const shoot = async (url, w, h, file) => {
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await page.goto(url);
    await page.waitForSelector("body[data-ready]");
    await page.screenshot({ path: file });
    await page.close();
    console.log("wrote", path.relative(ROOT, file));
  };
  for (const a of angles)
    for (const s of SIZES)
      await shoot(`${base}/creatives/ad.html?angle=${a.id}&w=${s.w}&h=${s.h}`, s.w, s.h, path.join(outDir, `${a.id}_${s.id}.png`));
  if (!only)
    for (const s of LOGOS)
      await shoot(`${base}/creatives/ad.html?logo=1&w=${s.w}&h=${s.h}`, s.w, s.h, path.join(outDir, `${s.id}.png`));
  await browser.close();
  srv.close();
})();
