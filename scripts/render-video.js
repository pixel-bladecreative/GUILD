// Render motion-graphics spots frame-by-frame with Playwright, encode with ffmpeg.
// Usage:
//   node scripts/render-video.js [spotId|all] [sizeId|all] [--stills] [--audio]
//   --stills : write a PNG contact sheet at 1s intervals instead of video (fast check)
//   --audio  : mux video/audio/<spot>.mix.wav if present (else silent track)
const { chromium } = require("playwright");
const { spawn, execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const { serve, ROOT } = require("./serve");

const SIZES = [
  { id: "9x16", w: 1080, h: 1920 },
  { id: "4x5", w: 1080, h: 1350 },
  { id: "16x9", w: 1920, h: 1080 },
];
const args = process.argv.slice(2);
const flags = new Set(args.filter(a => a.startsWith("--")));
const [spotArg = "all", sizeArg = "all"] = args.filter(a => !a.startsWith("--"));
const cfg = JSON.parse(fs.readFileSync(path.join(ROOT, "video/spots.json")));
const spots = cfg.spots.filter(s => spotArg === "all" || s.id === spotArg);
const sizes = SIZES.filter(s => sizeArg === "all" || s.id === sizeArg);
const OUT = path.join(ROOT, "video/out");
fs.mkdirSync(OUT, { recursive: true });

async function renderOne(browser, base, spot, size) {
  const page = await browser.newPage({ viewport: { width: size.w, height: size.h }, deviceScaleFactor: 1 });
  await page.goto(`${base}/video/spot.html?spot=${spot.id}&w=${size.w}&h=${size.h}`);
  await page.waitForSelector("body[data-ready]");
  const { fps, duration } = cfg;
  const name = `${spot.id}_${size.id}`;

  if (flags.has("--stills")) {
    const dir = path.join(ROOT, "tmp/stills", name);
    fs.mkdirSync(dir, { recursive: true });
    const times = [0.8, 2.0, 3.5, 5.0, 6.5, 8.0, 10.0, 11.5, 13.0, 14.8];
    for (const t of times) {
      await page.evaluate(t => window.__seek(t), t);
      await page.screenshot({ path: path.join(dir, `t${t.toFixed(1).padStart(4, "0")}.png`) });
    }
    await page.close();
    console.log("stills", name);
    return;
  }

  const mix = path.join(ROOT, `video/audio/${spot.id}.mix.wav`);
  const withAudio = flags.has("--audio") && fs.existsSync(mix);
  const file = path.join(OUT, `${name}.mp4`);
  const ff = spawn("ffmpeg", [
    "-y", "-loglevel", "error",
    "-f", "image2pipe", "-framerate", String(fps), "-c:v", "png", "-i", "-",
    ...(withAudio ? ["-i", mix] : ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]),
    "-map", "0:v", "-map", "1:a",
    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", String(fps),
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
    "-t", String(duration), "-movflags", "+faststart", file,
  ], { stdio: ["pipe", "inherit", "inherit"] });
  const total = Math.round(fps * duration);
  for (let i = 0; i < total; i++) {
    await page.evaluate(t => window.__seek(t), i / fps);
    const buf = await page.screenshot({ type: "png" });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on("close", c => (c === 0 ? res() : rej(new Error("ffmpeg " + c)))));
  await page.close();
  console.log("wrote", path.relative(ROOT, file), withAudio ? "(with audio)" : "(silent)");
}

(async () => {
  const { srv, base } = await serve();
  const browser = await chromium.launch();
  for (const spot of spots) for (const size of sizes) await renderOne(browser, base, spot, size);
  await browser.close();
  srv.close();
})().catch(e => { console.error(e); process.exit(1); });
