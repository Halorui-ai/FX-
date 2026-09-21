/* KPI compact/cozy/expanded + detail overlay. Run: node tests/kpi-density-e2e.cjs */
const { chromium } = require("playwright-core");
const http = require("http");
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const PORT = 8765;

function contentType(p) {
  if (p.endsWith(".html")) return "text/html; charset=utf-8";
  if (p.endsWith(".js")) return "text/javascript; charset=utf-8";
  if (p.endsWith(".css")) return "text/css; charset=utf-8";
  if (p.endsWith(".png")) return "image/png";
  if (p.endsWith(".woff2")) return "font/woff2";
  return "application/octet-stream";
}

const server = http.createServer((req, res) => {
  const urlPath = decodeURIComponent((req.url || "/").split("?")[0]);
  let rel = urlPath === "/" ? "/dashboard-release-monitor-v5.6.html" : urlPath;
  const file = path.normalize(path.join(ROOT, rel));
  if (!file.startsWith(ROOT)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); res.end("not found"); return; }
    res.writeHead(200, { "Content-Type": contentType(file) });
    res.end(data);
  });
});

function fail(msg) { console.error("FAIL", msg); process.exitCode = 1; }

(async () => {
  await new Promise(r => server.listen(PORT, r));
  const browser = await chromium.launch({
    channel: "chrome",
    headless: true
  }).catch(() => chromium.launch({ channel: "msedge", headless: true }));
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.on("pageerror", e => console.error("pageerror", e.message));
  await page.goto("http://127.0.0.1:" + PORT + "/dashboard-release-monitor-v5.6.html", { waitUntil: "load", timeout: 60000 });
  await page.click("#btnDemo");
  await page.waitForSelector("#dashboard:not(.hidden)", { timeout: 20000 });
  await page.waitForTimeout(800);
  if (await page.locator("#btnLive").isVisible()) await page.click("#btnLive");

  const compact = await page.evaluate(() => ({
    dens: window.__dashTest.dens("kpi_overview"),
    chips: window.__dashTest.hasChips("kpi_overview"),
    mini: window.__dashTest.hasMini("kpi_overview"),
    val: document.querySelector("#kpi_overviewVal")?.textContent
  }));
  console.log("compact", compact);
  if (compact.dens !== "compact") fail("overview default should be compact, got " + compact.dens);
  if (compact.chips) fail("compact should not show chips");
  if (compact.mini) fail("compact should not show mini chart");

  await page.click("#btnEditMode");
  await page.waitForTimeout(200);

  const cozy = await page.evaluate(() => window.__dashTest.setKpiSize("kpi_overview", 6, 3));
  await page.waitForTimeout(300);
  const cozyDom = await page.evaluate(() => ({
    dens: window.__dashTest.dens("kpi_overview"),
    chips: window.__dashTest.hasChips("kpi_overview"),
    mini: window.__dashTest.hasMini("kpi_overview")
  }));
  console.log("cozy", cozy, cozyDom);
  if (cozyDom.dens !== "cozy") fail("6x3 should be cozy, got " + JSON.stringify(cozy));
  if (!cozyDom.chips) fail("cozy should show chips");
  if (cozyDom.mini) fail("cozy should not show mini chart");

  const expanded = await page.evaluate(() => window.__dashTest.setKpiSize("kpi_overview", 8, 5));
  await page.waitForTimeout(400);
  const expDom = await page.evaluate(() => ({
    dens: window.__dashTest.dens("kpi_overview"),
    chips: window.__dashTest.hasChips("kpi_overview"),
    mini: window.__dashTest.hasMini("kpi_overview")
  }));
  console.log("expanded", expanded, expDom);
  if (expDom.dens !== "expanded") fail("8x5 should be expanded");
  if (!expDom.mini) fail("expanded needs large body (.l-body)");

  await page.evaluate(() => window.__dashTest.setKpiSize("kpi_transit", 6, 4));
  await page.waitForTimeout(300);
  const tr = await page.evaluate(() => ({
    dens: window.__dashTest.dens("kpi_transit"),
    chips: window.__dashTest.hasChips("kpi_transit"),
    mini: window.__dashTest.hasMini("kpi_transit")
  }));
  console.log("transit expanded", tr);
  if (tr.dens !== "expanded" || !tr.mini) fail("transit 6x4 should be expanded with mini");

  const rateSet = await page.evaluate(() => window.__dashTest.setKpiSize("kpi_rate", 7, 4));
  await page.waitForTimeout(400);
  const rate = await page.evaluate(() => ({
    dens: window.__dashTest.dens("kpi_rate"),
    chips: window.__dashTest.hasChips("kpi_rate"),
    pie: window.__dashTest.hasMini("kpi_rate"),
    gs: (() => {
      const item = [...document.querySelectorAll("#cardGrid .grid-stack-item")].find(el => el.querySelector('[data-card="kpi_rate"]'));
      return item ? { w: item.getAttribute("gs-w"), h: item.getAttribute("gs-h") } : null;
    })()
  }));
  console.log("rate expanded", rateSet, rate);
  if (rate.dens !== "expanded" || !rate.chips || !rate.pie) fail("rate expanded should have chips + pie " + JSON.stringify({ rateSet, rate }));

  await page.click("#btnEditMode");
  await page.waitForTimeout(200);

  await page.locator('[data-card="kpi_overview"] .kpi-seg [data-tab="arrive"]').click();
  await page.waitForTimeout(200);
  const afterTab = await page.evaluate(() => window.__dashTest.detailOpen());
  console.log("click tab -> detail", afterTab);
  if (afterTab) fail("clicking dimension tab should not open detail");

  await page.locator('[data-card="kpi_overview"] .hero-num').click();
  await page.waitForTimeout(400);
  const afterHero = await page.evaluate(() => window.__dashTest.detailOpen());
  console.log("click hero -> detail", afterHero);
  if (!afterHero) fail("clicking KPI hero should open detail overlay");
  const title = await page.locator("#detailPanelTitle").textContent();
  console.log("detail title", title);
  if (!title || !title.includes("放行单")) fail("detail title mismatch");

  const shotDir = path.join(ROOT, "tests");
  await page.screenshot({ path: path.join(shotDir, "kpi-density-expanded.png"), fullPage: true });

  await browser.close();
  server.close();
  if (process.exitCode) {
    console.error("KPI density e2e FAILED");
    process.exit(1);
  }
  console.log("KPI density e2e PASSED");
})().catch(err => {
  console.error(err);
  process.exit(1);
});
