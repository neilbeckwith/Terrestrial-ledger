# Terrestrial Ledger — land CO₂ uptake by region

A static web app: annual land CO₂ uptake, 1959–2024, by region — explained
by the six terrestrial carbon processes and observed through the 20 GCOS
terrestrial Essential Climate Variables, under the GTOS framework.

## What it shows

- **The active ledger (live counter)** — tonnes of CO₂ taken up since the
  page opened, and a live running cumulative total since 1959. This spreads
  the latest annual land rate (2024: 1.94 GtC/yr) evenly across the year;
  it is an estimate, not a measurement.
- **Historic trend** — world annual land uptake 1959–2024, from 0.45 GtC/yr
  to 1.94 GtC/yr, with decadal means (1960s 0.93 → 2010s 2.54 GtC/yr) and
  land-use-change emissions alongside. Weakest year 1983 (0.21 GtC, El
  Niño); strongest 2011 (3.29 GtC).
- **The six processes** — the science behind the numbers: photosynthesis
  (GPP 123 ± 8 PgC/yr), plant & soil respiration (soils alone 98 ± 12
  PgC/yr), soil carbon storage (~1,500 GtC in the top metre), permafrost
  carbon (~1,300 PgC), fire disturbance (~2 GtC/yr) and land-use change
  (1.25 GtC/yr in 2024), plus the coupling: the sink is the small
  difference of huge fluxes (~2% of GPP), which is why it swings ±1 GtC
  a year and why climate change cut the 2015–2024 sink by 25%.
- **Every region** — ten RECCAP-2 regions, decadal means 2015–2024 from
  Friedlingstein et al. 2025, Figure 15 and §3.8.2: natural sink, land-use
  emissions, and net flux from DGVMs and from atmospheric inversions side
  by side. North America 0.4 and Russia 0.6 (inversions) are the largest
  net sinks; South America, Africa and Southeast Asia are net sources by
  inversions. Click a row for the region's drivers, processes and
  observing variables.
- **Compare regions** — three pickers, side by side.
- **Accumulated carbon** — 118.1 GtC taken up 1959–2024 (433 GtCO₂), 22.0%
  of the 537 GtC humans emitted over the same period. Over 1850–2024 the
  land as a whole was a net source of 75 ± 80 GtC, because land-use
  emissions (250 GtC) exceeded the natural sink (175 GtC).
- **GCOS terrestrial Essential Climate Variables** — all 20 ECVs by GCOS
  group (Hydrology, Cryosphere, Biology, Human use), with each variable's
  role in the ledger, plus the variables that constrain the uptake. The
  framework is GTOS: TOPC is sponsored jointly by GCOS, the FAO-led GTOS
  and WCRP.
- **CSV downloads** — region table and global series.

## Data

- Global annual land sink (SLAND), 1959–2024: Global Carbon Budget 2025
  (Friedlingstein et al. 2025, ESSD 18, 3211–3288), via the ICOS Carbon
  Portal spreadsheet. 2024: 1.94 GtC/yr (7.12 GtCO₂/yr), −3.7% vs 2023,
  16.5% of 2024 total human emissions (11.79 GtC). Uncertainty ±0.5
  GtC/yr on average (±1.1 in 2024).
- Regional breakdown: Friedlingstein et al. 2025, §3.8.2 and Figure 15 —
  decadal-mean (2015–2024) RECCAP-2 region fluxes. These are *decadal
  means*, not an annual series; no published annual regional land series
  exists. Values stated in the paper text are used verbatim; the rest are
  read from Figure 15 to the nearest 0.05 GtC/yr (flagged in data.json).
  The ten regional DGVM nets sum to 1.30 GtC/yr against the global
  2015–2024 mean net land flux of 0.99 GtC/yr — the gap is the DGVM
  underestimate of ELUC in South America and Southeast Asia, stated on
  the page.
- 2025 preliminary: 2.36 ± 0.16 GtC/yr net land sink (Ciais et al. 2026,
  low-latency budget) — quoted in the text, not in the series, and not
  added to the cumulative counter: it is a *net* land flux (sink minus
  land-use emissions), a different quantity from the SLAND series.
- Variables: GCOS ECV list (gcos.wmo.int), terrestrial domain, accessed
  2026-11-26. Framework: GTOS / TOPC. Processes: Beer et al. 2010;
  Bond-Lamberty & Thomson 2010; Batjes 1996; Jobbágy & Jackson 2000;
  Hugelius et al. 2014; van der Werf et al. 2017 (GFED4.1s).

`data.json` is built by `scripts/fetch_data.py` from the Global Carbon
Budget 2025 spreadsheet (downloaded from ICOS) and Friedlingstein et al.
2025, Figure 15 and §3.8.2 (transcribed). Re-run it to refresh the data
when a new Global Carbon Budget is published. Sources are credited in the
captions on the page and in the Methods section.

## Run locally

```bash
cd terrestrial-ledger
python3 -m http.server 8000
# open http://127.0.0.1:8000/
```

No build step, no dependencies. `index.html` + `styles.css` + `app.js` + `data.json`.

## Deploy

- **GitHub Pages:** publish this folder as-is to a new public repo
  (`Terrestrial-ledger`) with Pages enabled. A workflow like the
  carbon-ledge one (`.github/workflows/deploy-pages.yml`) can publish it
  on push.
- **Any static host** (Vercel, Netlify, etc.): publish this folder as-is.

This repo is not created yet — build locally, present to Neil, push only
after he approves that specific push.
