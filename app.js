/* Terrestrial Ledger — annual land CO2 uptake by region.
   Data: data.json, built by scripts/fetch_data.py from the Global Carbon
   Budget 2025 (GCB) and Friedlingstein et al. 2025, Figure 15 / Sect. 3.8.2
   (RECCAP-2 regions, decadal means 2015-2024).
   Units: GtC/yr for the global series (1 GtC = 1 PgC = 3.664 GtCO2);
   regional fluxes in GtC/yr. Uptake is POSITIVE on this page; ELUC is
   shown as a positive emission.
   Live counter: spreads the latest annual land rate evenly across the
   year. It is an estimate, not a measurement. The 2025 preliminary
   figure is a NET land flux and is deliberately NOT added to the
   cumulative counter (see Methods). */
let DATA = null;
let selectedRegion = null;

const $ = (id) => document.getElementById(id);
const fmt = (n, d = 0) => n == null || isNaN(n) ? "—" : Number(n).toLocaleString("en-CA", { maximumFractionDigits: d, minimumFractionDigits: d });
const pct = (n) => n == null || isNaN(n) ? "—" : (n > 0 ? "+" : "") + n.toFixed(1) + "%";
const sgn = (n, d = 2) => n == null || isNaN(n) ? "—" : (n > 0 ? "+" : "") + n.toFixed(d);

function regionList() {
  return Object.entries(DATA.regions).map(([name, r]) => ({ name, ...r }));
}

function drawChart() {
  const svg = $("worldChart");
  const W = 900, H = 320, PL = 56, PR = 16, PT = 18, PB = 34;
  const world = DATA.world;
  const maxV = Math.max(...world.map((w) => Math.max(w.sland_gtc, w.eluc_gtc)));
  const minY = world[0].year, maxY = world[world.length - 1].year;
  const x = (y) => PL + (y - minY) / (maxY - minY) * (W - PL - PR);
  const y = (v) => PT + (1 - v / (maxV * 1.05)) * (H - PT - PB);
  let s = "";
  for (let g = 0; g <= 4; g++) {
    const v = maxV * g / 4, yy = y(v);
    s += `<line x1="${PL}" y1="${yy}" x2="${W - PR}" y2="${yy}" stroke="#e3eae6"/><text x="${PL - 8}" y="${yy + 4}" text-anchor="end" font-size="11" fill="#5a6b64">${fmt(v, 1)}</text>`;
  }
  for (const yr of [1960, 1975, 1990, 2005, 2024]) {
    s += `<text x="${x(yr)}" y="${H - 10}" text-anchor="middle" font-size="11" fill="#5a6b64">${yr}</text>`;
  }
  s += `<text x="${PL}" y="${PT - 4}" font-size="11" fill="#5a6b64">GtC per year</text>`;
  s += `<path d="${world.map((w, i) => (i ? "L" : "M") + x(w.year).toFixed(1) + "," + y(w.eluc_gtc).toFixed(1)).join(" ")}" fill="none" stroke="#8a5a1f" stroke-width="2" stroke-dasharray="6 4"/>`;
  s += `<path d="${world.map((w, i) => (i ? "L" : "M") + x(w.year).toFixed(1) + "," + y(w.sland_gtc).toFixed(1)).join(" ")}" fill="none" stroke="#1d6b3c" stroke-width="2.5"/>`;
  svg.innerHTML = s;
  const v = (yr, k) => (world.find((w) => w.year === yr) || {})[k];
  const dec = DATA.summary.decadal_means_gtc;
  $("worldStats").innerHTML =
    `<span>1960: ${fmt(v(1960, "sland_gtc"), 2)} GtC</span><span>1980: ${fmt(v(1980, "sland_gtc"), 2)} GtC</span>` +
    `<span>2000: ${fmt(v(2000, "sland_gtc"), 2)} GtC</span><span>2010: ${fmt(v(2010, "sland_gtc"), 2)} GtC</span>` +
    `<span>2024: ${fmt(v(2024, "sland_gtc"), 2)} GtC (${pct(DATA.summary.yoy_pct)} vs 2023)</span>` +
    `<span>1960s mean: ${fmt(dec["1960"], 2)}</span><span>2010s mean: ${fmt(dec["2010"], 2)}</span>` +
    `<span>2015–2024 mean: ${fmt(DATA.summary.mean_2015_2024_gtc, 2)} GtC</span>` +
    `<span>Weakest year: 1983 (${fmt(v(1983, "sland_gtc"), 2)} GtC)</span>` +
    `<span>Strongest year: 2011 (${fmt(v(2011, "sland_gtc"), 2)} GtC)</span>`;
}

function renderProcesses() {
  $("pumpGrid").innerHTML = DATA.processes.map((p) => {
    const wide = p.abbr === "BALANCE" ? " wide" : "";
    return `<div class="pump${wide}"><div class="abbr">${p.abbr}</div><h3>${p.name}</h3><p>${p.role}</p><p class="caption">Source: ${p.source}</p></div>`;
  }).join("");
}

function renderTable() {
  const sort = $("sort").value;
  let rows = regionList();
  if (sort === "name") rows.sort((a, b) => a.name.localeCompare(b.name));
  else if (sort === "sland") rows.sort((a, b) => b.sland_gtc - a.sland_gtc);
  else if (sort === "eluc") rows.sort((a, b) => b.eluc_bkm_gtc - a.eluc_bkm_gtc);
  else rows.sort((a, b) => b.net_dgvm_gtc - a.net_dgvm_gtc);
  $("tbody").innerHTML = rows.map((r) => {
    const clsNet = r.net_dgvm_gtc >= 0 ? "pos" : "neg";
    const clsInv = r.net_inv_gtc >= 0 ? "pos" : "neg";
    const procs = (DATA.region_detail[r.name] || {}).processes || [];
    return `<tr data-region="${r.name}"><td>${r.name}</td>` +
      `<td class="${clsNet}">${sgn(r.net_dgvm_gtc)}</td>` +
      `<td class="${clsInv}">${sgn(r.net_inv_gtc)}</td>` +
      `<td>${r.sland_gtc.toFixed(2)}</td>` +
      `<td>${r.eluc_bkm_gtc.toFixed(2)}</td>` +
      `<td>${procs.join(" + ")}</td></tr>`;
  }).join("");
  document.querySelectorAll("#tbody tr").forEach((tr) =>
    tr.addEventListener("click", () => selectRegion(tr.dataset.region)));
}

function processLong(abbr) {
  const p = DATA.processes.find((x) => x.abbr === abbr);
  return p ? `${p.abbr} — ${p.name}` : abbr;
}

function selectRegion(name) {
  selectedRegion = name;
  const r = DATA.regions[name];
  const d = DATA.region_detail[name] || {};
  if (!r) return;
  const ecvTags = (d.ecvs || []).map((e) => `<span class="eov-tag">${e}</span>`).join("");
  const procs = (d.processes || []).map(processLong).join("; ");
  const srcNote = r.value_source === "fig"
    ? "Values for this region are read from Figure 15 to the nearest 0.05 GtC/yr (see Methods)."
    : "Values for this region are stated in the paper text (Friedlingstein et al. 2025, §3.8.2).";
  $("detail").innerHTML =
    `<h3>${name}</h3>` +
    `<p>Decadal mean (2015–2024) net land flux <strong>${sgn(r.net_dgvm_gtc)} GtC/yr</strong> by DGVMs, ` +
    `<strong>${sgn(r.net_inv_gtc)} GtC/yr</strong> by atmospheric inversions — natural sink ` +
    `${r.sland_gtc.toFixed(2)} GtC/yr minus land-use emissions ${r.eluc_bkm_gtc.toFixed(2)} GtC/yr.</p>` +
    `<p class="caption">${srcNote}</p>` +
    `<h3>Why it takes up what it does</h3><p>${d.drivers || ""}</p>` +
    `<p class="caption">Drivers source: ${d.driver_source || ""}</p>` +
    `<h3>Processes behind it</h3><p>${procs}</p>` +
    `<p class="caption">Process framing: the six terrestrial carbon processes above. No published source splits a region's net flux into process shares; the attribution above is qualitative.</p>` +
    `<h3>GCOS variables that watch this region</h3><p>${ecvTags}</p>` +
    `<p class="caption">ECV names and groups: GCOS Essential Climate Variables, terrestrial domain.</p>` +
    `<h3>The four numbers (GtC/yr, 2015–2024 mean)</h3>` +
    `<div class="table-wrap"><table><thead><tr><th>Natural sink (SLAND)</th><th>Land-use emissions (ELUC)</th><th>Net flux, DGVMs</th><th>Net flux, inversions</th></tr></thead><tbody><tr><td>${r.sland_gtc.toFixed(2)}</td><td>${r.eluc_bkm_gtc.toFixed(2)}</td><td class="${r.net_dgvm_gtc >= 0 ? "pos" : "neg"}">${sgn(r.net_dgvm_gtc)}</td><td class="${r.net_inv_gtc >= 0 ? "pos" : "neg"}">${sgn(r.net_inv_gtc)}</td></tr></tbody></table></div>` +
    `<p class="caption">Positive is a sink (carbon into the land); ELUC is shown as a positive emission. DGVM and inversion net fluxes are independent estimates of the same quantity — where they disagree, the disagreement is the story.</p>`;
  $("detail").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderCompare() {
  const names = regionList().map((r) => r.name);
  for (const id of ["cmp1", "cmp2", "cmp3"]) {
    const sel = $(id);
    sel.innerHTML = `<option value="">—</option>` + names.map((n) => `<option value="${n}">${n}</option>`).join("");
  }
  $("cmp1").value = "South America";
  $("cmp2").value = "Russia";
  $("cmp3").value = "Africa";
  const draw = () => {
    const picks = ["cmp1", "cmp2", "cmp3"].map((id) => $(id).value).filter(Boolean);
    $("compareGrid").innerHTML = picks.map((name) => {
      const r = DATA.regions[name];
      const d = DATA.region_detail[name] || {};
      return `<div class="compare-card"><h3>${name}</h3>` +
        `<div class="kv"><span>Net flux, DGVMs</span><span>${sgn(r.net_dgvm_gtc)} GtC/yr</span></div>` +
        `<div class="kv"><span>Net flux, inversions</span><span>${sgn(r.net_inv_gtc)} GtC/yr</span></div>` +
        `<div class="kv"><span>Natural sink</span><span>${r.sland_gtc.toFixed(2)} GtC/yr</span></div>` +
        `<div class="kv"><span>Land-use emissions</span><span>${r.eluc_bkm_gtc.toFixed(2)} GtC/yr</span></div>` +
        `<div class="kv"><span>Dominant processes</span><span>${(d.processes || []).join(" + ")}</span></div>` +
        `<p class="sub" style="margin-top:10px">${d.drivers || ""}</p>` +
        `<p class="caption">Drivers: ${d.driver_source || ""}</p></div>`;
    }).join("");
  };
  for (const id of ["cmp1", "cmp2", "cmp3"]) $(id).addEventListener("change", draw);
  draw();
}

function renderECV() {
  const order = ["Hydrology", "Cryosphere", "Biology", "Human use"];
  const rows = [];
  for (const grp of order) {
    DATA.ecvs.filter((e) => e.group === grp).forEach((e) => {
      rows.push(`<tr><td>${e.name}</td><td>${e.group}</td><td>${e.role}</td></tr>`);
    });
  }
  $("eovBody").innerHTML = rows.join("");
}

function downloadCSV(filename, text) {
  const blob = new Blob([text], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function startCounter() {
  // 2024 land rate, spread evenly. 2024 is a leap year (366 days);
  // the counter applies the annual rate over the current year (2026, 365 days).
  const annualTonnesCO2 = DATA.summary.latest_sland_gtco2 * 1e9; // t CO2/yr
  const ratePerSec = annualTonnesCO2 / (365 * 24 * 3600); // ≈ 226 t/s
  const cumulativeEnd2024GtC = DATA.summary.cumulative_1959_latest_gtc;
  const start2026 = Date.UTC(2026, 0, 1);
  const openedAt = Date.now();
  $("rateLine").textContent = `${fmt(ratePerSec, 0)} tonnes of CO₂ per second (2024 land rate, spread evenly)`;
  function tick() {
    const now = Date.now();
    const sinceOpenedT = ratePerSec * (now - openedAt) / 1000;
    $("sinceOpened").textContent = `${fmt(sinceOpenedT, 1)} t`;
    const elapsed2026Sec = Math.max(0, (now - start2026) / 1000);
    const cumGtC2 = cumulativeEnd2024GtC + (ratePerSec / 3.664) * elapsed2026Sec / 1e9;
    $("cumulativeLive").textContent = `${fmt(cumGtC2, 2)} GtC`;
    $("cumulativeSub").textContent = `118.1 GtC at end-2024 + ${fmt((ratePerSec / 3.664) * elapsed2026Sec / 1e9, 2)} GtC estimated in 2026 to date (2025 preliminary is a net flux and is not added — see Methods)`;
  }
  tick();
  setInterval(tick, 250);
}

async function init() {
  const res = await fetch("data.json");
  DATA = await res.json();
  $("latestYear").textContent = DATA.meta.latest_year;
  const s = DATA.summary;
  $("world2024").textContent = `${fmt(s.latest_sland_gtc, 2)} GtC`;
  $("worldYoY").textContent = `${pct(s.yoy_pct)} vs ${s.latest_year - 1} · ${fmt(s.latest_sland_gtco2, 2)} GtCO₂`;
  drawChart();
  renderProcesses();
  renderTable();
  renderCompare();
  renderECV();
  startCounter();
  $("sort").addEventListener("change", renderTable);
  $("pickSouthAmerica").addEventListener("click", () => selectRegion("South America"));
  $("csvRegions").addEventListener("click", () => {
    const head = "Region,Natural sink SLAND (GtC/yr),Land-use emissions ELUC bookkeeping (GtC/yr),Net flux DGVMs (GtC/yr),Net flux inversions (GtC/yr),Value source,Dominant processes\n";
    const body = regionList().map((r) => {
      const procs = (DATA.region_detail[r.name] || {}).processes || [];
      return `"${r.name}",${r.sland_gtc},${r.eluc_bkm_gtc},${r.net_dgvm_gtc},${r.net_inv_gtc},${r.value_source},"${procs.join(" + ")}"`;
    }).join("\n");
    downloadCSV("terrestrial-ledger-regions.csv", head + body + "\n");
  });
  $("csvGlobal").addEventListener("click", () => {
    const head = "Year,Land sink (GtC/yr),Land sink (GtCO2/yr),Fossil emissions (GtC/yr),Land-use change (GtC/yr),Atmospheric growth (GtC/yr),Ocean sink (GtC/yr),Net land flux (GtC/yr)\n";
    const body = DATA.world.map((w) => `${w.year},${w.sland_gtc},${w.sland_gtco2},${w.efos_gtc},${w.eluc_gtc},${w.gatm_gtc},${w.socean_gtc},${w.net_land_gtc}`).join("\n");
    downloadCSV("terrestrial-ledger-global-series.csv", head + body + "\n");
  });
}
init().catch((e) => { document.querySelector("main").insertAdjacentHTML("afterbegin", `<p class="note">Could not load data.json — ${e.message}. Serve this folder over HTTP (not file://) or check the data file.</p>`); });
