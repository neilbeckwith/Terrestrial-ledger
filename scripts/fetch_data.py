#!/usr/bin/env python3
"""Fetch land CO2 uptake data for Terrestrial Ledger and build data.json.

Sources (all public, all cited on the page):
  1. Global Carbon Budget 2025 spreadsheet (Friedlingstein et al. 2025,
     Earth Syst. Sci. Data 18, 3211-3288, doi:10.5194/essd-18-3211-2026;
     data doi:10.18160/GCP-2025), via the ICOS Carbon Portal. Sheets used:
     "Terrestrial Sink" (GCB adjusted annual land sink SLAND, GtC/yr,
     1959-2024) and "Historical Budget" (fossil, land-use, atmospheric
     growth, ocean and land sinks, 1750-2024). The two SLAND series are
     cross-checked against each other.
  2. Friedlingstein et al. 2025, Sect. 3.8.2 and Figure 15: decadal-mean
     (2015-2024) land fluxes for the 10 RECCAP-2 land regions - SLAND
     from the DGVM ensemble, ELUC from the bookkeeping models, net land
     flux (SLAND - ELUC) from DGVMs and from atmospheric inversions.
     Values stated in the paper text are used verbatim; values not stated
     in the text are read from Figure 15 to the nearest 0.05 GtC/yr and
     flagged as chart-read in the notes. There is no published annual
     regional land series - these are decadal means, not an annual series.
  3. Ciais et al. 2026 (low-latency global carbon budget 2025, arXiv
     2609.34226): preliminary 2025 net land sink, quoted in the page text
     only, not in the annual series - and it is a NET land flux (sink
     minus land-use emissions), a different quantity from the SLAND
     series plotted here.
  4. GCOS Essential Climate Variables, terrestrial domain (20 ECVs),
     as listed at gcos.wmo.int/en/essential-climate-variables (accessed
     2026-11-26), grouped as GCOS groups them: Hydrology, Cryosphere,
     Biology, Human Use of Natural Resources. Framework: GTOS (Global
     Terrestrial Observing System); TOPC (Terrestrial Observation Panel
     for Climate) is sponsored jointly by GCOS, the FAO-led GTOS and
     WCRP (GCOS submission to UNFCCC SBSTA 37, 2012).
  5. Process numbers: GPP 123 +- 8 PgC/yr (Beer et al. 2010, Science 329,
     834-838); soil respiration 98 +- 12 PgC/yr in 2008, Q10 1.5
     (Bond-Lamberty & Thomson 2010, Nature 464, 579-582); soil organic
     carbon 1,462-1,548 PgC in the top 1 m (Batjes 1996; Jobbagy &
     Jackson 2000: 1,502 PgC); permafrost-region SOC ~1,300 PgC,
     1,035 +- 150 PgC in 0-3 m soils (Hugelius et al. 2014,
     Biogeosciences 11, 6573-6593); vegetation ~550 GtC (Houghton 2007,
     via Ciais et al. 2013).

Unit note: 1 GtC = 1 PgC = 3.664 GtCO2 (the GCB spreadsheet factor).
Sign convention on the page: uptake is POSITIVE (carbon into the land);
ELUC is shown as a positive emission (carbon out of the land).
"""
import http.cookiejar
import json
import os
import urllib.request

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data.json")

GCB_URL = ("https://data.icos-cp.eu/licence_accept"
           "?ids=%5B%22qSjPBsV1drZnYdH-yCJMmkGn%22%5D")
GCB_XLSX = os.path.join(ROOT, "Global_Carbon_Budget_2025_v1.0.xlsx")
GTCO2_PER_GTC = 3.664

# --- RECCAP-2 regions, Friedlingstein et al. 2025, Fig. 15 + Sect. 3.8.2 ----
# Decadal means 2015-2024, GtC/yr. Positive = sink (carbon into the land).
# sland: DGVM natural land sink. eluc_bkm: land-use emissions, bookkeeping
# models (positive = emission). net_dgvm: SLAND - ELUC from DGVMs.
# net_inv: net land flux from atmospheric inversions.
# Values stated in the paper text are exact; the rest are read from
# Figure 15 to the nearest 0.05 GtC/yr (flagged "fig" below).
REGIONS = [
    # (region, sland, eluc_bkm, net_dgvm, net_inv, src)
    ("North America", 0.40, 0.00, 0.40, 0.40, "text"),
    ("South America", 0.40, 0.50, 0.10, -0.10, "text"),
    ("Europe", 0.10, 0.00, 0.10, 0.30, "fig"),
    ("Africa", 0.50, 0.40, 0.10, -0.30, "text"),
    ("Russia", 0.35, 0.00, 0.30, 0.60, "fig"),
    ("West Asia", 0.05, 0.00, 0.05, 0.00, "fig"),
    ("Southeast Asia", 0.20, 0.40, 0.00, -0.10, "text"),
    ("East Asia", 0.20, 0.00, 0.20, 0.20, "fig"),
    ("South Asia", 0.10, 0.10, 0.00, 0.20, "fig"),
    ("Australasia", 0.05, 0.00, 0.05, 0.05, "fig"),
]

# --- Terrestrial carbon processes (the modelling core) ----------------------
# PHOTO photosynthesis, RESP respiration, SOIL soil storage,
# PERMA permafrost, FIRE fire, LUC land-use change, BALANCE the coupling.
PROCESSES = [
    {"abbr": "PHOTO", "name": "Photosynthesis — gross primary production",
     "role": "Plants fix about 123 ± 8 PgC/yr from the air (Beer et al. "
             "2010) — the largest carbon flux on Earth, roughly ten times "
             "fossil-fuel emissions. Tropical forests and savannahs do 60% "
             "of it. Every tonne in the land sink entered through this door.",
     "source": "Beer et al. 2010, Science 329, 834–838"},
    {"abbr": "RESP", "name": "Plant & soil respiration",
     "role": "Nearly all of GPP returns to the air as CO₂. Soils alone "
             "breathe out 98 ± 12 PgC/yr (Bond-Lamberty & Thomson 2010), "
             "rising about 0.1 PgC/yr as the planet warms, with a "
             "temperature sensitivity (Q10) of about 1.5. The sink is what "
             "photosynthesis keeps ahead of respiration.",
     "source": "Bond-Lamberty & Thomson 2010, Nature 464, 579–582"},
    {"abbr": "SOIL", "name": "Soil carbon storage",
     "role": "Soils hold about 1,500 GtC of organic carbon in the top metre "
             "(Batjes 1996; Jobbágy & Jackson 2000) — roughly twice the "
             "carbon in the air and three times the ~550 GtC in vegetation. "
             "Litter feeds it, microbes eat it; the balance is the slow store.",
     "source": "Batjes 1996; Jobbágy & Jackson 2000"},
    {"abbr": "PERMA", "name": "Permafrost carbon",
     "role": "Permafrost-region soils hold about 1,300 PgC (range "
             "1,100–1,500), some 800 PgC of it perennially frozen "
             "(Hugelius et al. 2014). Thaw releases it as CO₂ and CH₄ — "
             "about 18 GtC per degree of global warming (IPCC 2021). The "
             "DGVMs behind the land sink mostly do not simulate abrupt thaw.",
     "source": "Hugelius et al. 2014, Biogeosciences 11, 6573–6593"},
    {"abbr": "FIRE", "name": "Fire disturbance",
     "role": "Fire returns about 2 GtC/yr to the air in a typical recent "
             "year (GFED4.1s). 2023–2024 ran hot — 1.7–2.2 GtC in "
             "January–September alone, driven by Canada's record fires — "
             "while Africa contributes about half of global fire emissions "
             "(GCB 2025 §3.8.3).",
     "source": "van der Werf et al. 2017 (GFED4.1s); GCB 2025 §3.8.3"},
    {"abbr": "LUC", "name": "Land-use change",
     "role": "Clearing forest and draining peat emits 1.25 GtC/yr (2024, "
             "GCB 2025), and regrowth on abandoned land takes some back. "
             "It is the only process humans directly control, and the "
             "largest uncertainty in the budget (±0.7 GtC/yr).",
     "source": "Friedlingstein et al. 2025 (GCB 2025)"},
    {"abbr": "BALANCE", "name": "The small difference of huge fluxes",
     "role": "GPP (~123 PgC/yr) minus respiration and fire leaves a net "
             "sink of about 2 GtC/yr — roughly 2% of what photosynthesis "
             "fixes. That is why the land sink swings by ±1 GtC from year "
             "to year with drought and El Niño, why its uncertainty "
             "(±0.5–1.1 GtC/yr) is large next to its size, and why climate "
             "change — which cut the 2015–2024 sink by 25% (GCB 2025) — "
             "matters so much. Warming raises respiration (Q10 ≈ 1.5) and "
             "fire, while rising CO₂ fertilises photosynthesis; the balance "
             "is what the annual series measures.",
     "source": "Friedlingstein et al. 2025 (GCB 2025)"},
]

# --- GCOS terrestrial ECVs ---------------------------------------------------
# gcos.wmo.int/en/essential-climate-variables (accessed 2026-11-26), 20 ECVs.
# Groups are GCOS's own: Hydrology, Cryosphere, Biology, Human Use.
ECVS = [
    # (name, group, role in the ledger)
    ("Groundwater", "Hydrology",
     "Water stored below ground sustains dry-season growth and sets drought resilience."),
    ("Lakes", "Hydrology",
     "Lake area and level track water storage; lakes bury carbon in sediments."),
    ("River discharge", "Hydrology",
     "Rivers carry land carbon to the sea — the GCB's river-outgassing adjustment is 0.65 GtC/yr."),
    ("Terrestrial water storage", "Hydrology",
     "GRACE-measured water storage; land-flux anomalies track it (Ciais et al. 2026)."),
    ("Evaporation from land", "Hydrology",
     "The water flux that accompanies photosynthesis; drought cuts both together."),
    ("Soil moisture", "Hydrology",
     "Controls photosynthesis, respiration and fire risk — the master switch on the sink's year-to-year swings."),
    ("Glaciers", "Cryosphere",
     "Meltwater and newly exposed land; a small direct carbon role, a large climate signal."),
    ("Ice sheets and ice shelves", "Cryosphere",
     "Not a carbon flux itself; their melt sets sea level and the long-term climate the sink lives in."),
    ("Permafrost", "Cryosphere",
     "Thaw releases the ~1,300 PgC stored in permafrost-region soils as CO₂ and CH₄."),
    ("Snow", "Cryosphere",
     "Insulates soil, sets the spring thaw and the start of the growing season."),
    ("Above-ground biomass", "Biology",
     "The living carbon stock (~550 GtC in vegetation); its change is the sink."),
    ("Albedo", "Biology",
     "How much sunlight land reflects; darkening warms and brightening cools — a feedback on the sink."),
    ("Fire", "Biology",
     "Satellite fire counts and burned area give fire emissions, about 2 GtC/yr."),
    ("Fraction of absorbed photosynthetically active radiation (FAPAR)", "Biology",
     "The fraction of sunlight plants absorb — the direct satellite measure of photosynthesis at work."),
    ("Land cover", "Biology",
     "What grows where; deforestation and regrowth show up here first."),
    ("Land surface temperature", "Biology",
     "Heat stress cuts photosynthesis and raises respiration."),
    ("Leaf area index", "Biology",
     "Leaf area per ground area; sets how much light the canopy can catch."),
    ("Soil carbon", "Biology",
     "The stock itself (~1,500 GtC in the top metre) and its change."),
    ("Anthropogenic greenhouse gas emissions", "Human use",
     "Fossil + land-use emissions — the denominator the sink is measured against."),
    ("Anthropogenic water use", "Human use",
     "Irrigation and extraction change soil moisture, growth and river flow."),
]

# --- Region drivers ----------------------------------------------------------
# Qualitative attribution only -- no published source splits a region's net
# flux into process shares, and the page says so. Drivers are as stated in
# Friedlingstein et al. 2025 Sect. 3.8.2-3.8.3 (and the cited process papers).
REGION_DETAIL = {
    "North America": {
        "drivers": "Boreal and temperate forests, regrowing after past "
                   "clearing and fertilised by rising CO₂, give a steady "
                   "sink, and net land-use losses are near zero. The sink "
                   "is now being cut by fire: Canada's record 2023 fires "
                   "and three straight high years — January–September 2025 "
                   "fire emissions of 0.3–0.4 GtC, 2.2× the 2015–2024 "
                   "average.",
        "driver_source": "Friedlingstein et al. 2025, §§3.8.2–3.8.3",
        "processes": ["PHOTO", "RESP", "SOIL", "FIRE", "LUC"],
        "ecvs": ["Land cover", "Above-ground biomass", "Fire",
                 "Fraction of absorbed photosynthetically active radiation (FAPAR)",
                 "Leaf area index", "Soil moisture", "Soil carbon",
                 "Land surface temperature"],
    },
    "South America": {
        "drivers": "The Amazon is the largest tropical forest carbon store, "
                   "but deforestation and degradation emit about 0.5 GtC/yr "
                   "(bookkeeping), nearly cancelling the natural sink. "
                   "Inversions see a small net source; DGVMs a small sink — "
                   "the disagreement is the budget's largest regional "
                   "uncertainty. The 2023–24 El Niño drought turned "
                   "tropical lands into a source.",
        "driver_source": "Friedlingstein et al. 2025, §3.8.2",
        "processes": ["PHOTO", "RESP", "SOIL", "FIRE", "LUC"],
        "ecvs": ["Land cover", "Above-ground biomass", "Fire",
                 "Fraction of absorbed photosynthetically active radiation (FAPAR)",
                 "Soil moisture", "Soil carbon", "Land surface temperature",
                 "Evaporation from land"],
    },
    "Europe": {
        "drivers": "Managed forests and farmland regrowth give a modest "
                   "sink; inversions (0.3 GtC/yr) see more than DGVMs "
                   "(0.1). Land-use emissions are near zero.",
        "driver_source": "Friedlingstein et al. 2025, §3.8.2",
        "processes": ["PHOTO", "SOIL", "LUC"],
        "ecvs": ["Land cover", "Above-ground biomass",
                 "Fraction of absorbed photosynthetically active radiation (FAPAR)",
                 "Leaf area index", "Soil carbon", "Soil moisture"],
    },
    "Africa": {
        "drivers": "Congo Basin forest and savannahs fix about 0.5 GtC/yr, "
                   "but deforestation, shifting cultivation and fire emit "
                   "about 0.4 GtC/yr — Africa contributes about half of "
                   "global fire emissions. Inversions see a net source "
                   "(−0.3); DGVMs a small sink (0.1).",
        "driver_source": "Friedlingstein et al. 2025, §§3.8.2–3.8.3",
        "processes": ["PHOTO", "RESP", "FIRE", "LUC", "SOIL"],
        "ecvs": ["Fire", "Land cover", "Above-ground biomass",
                 "Fraction of absorbed photosynthetically active radiation (FAPAR)",
                 "Soil moisture", "Soil carbon", "Evaporation from land"],
    },
    "Russia": {
        "drivers": "Boreal forest and tundra: the largest inversion sink "
                   "(0.6 GtC/yr) but DGVMs say 0.3 — the paper's "
                   "north–south conundrum in one region. Permafrost holds "
                   "~1,300 PgC beneath it; thaw is the long-term risk.",
        "driver_source": "Friedlingstein et al. 2025, §3.8.2",
        "processes": ["PHOTO", "RESP", "SOIL", "PERMA", "FIRE"],
        "ecvs": ["Permafrost", "Snow", "Land cover",
                 "Above-ground biomass", "Fire", "Soil carbon",
                 "Land surface temperature", "Soil moisture"],
    },
    "West Asia": {
        "drivers": "Arid and semi-arid lands: small fluxes, near-neutral. "
                   "Water, not carbon, is the limiting factor — irrigation "
                   "and groundwater set what grows.",
        "driver_source": "Friedlingstein et al. 2025, Fig. 15",
        "processes": ["PHOTO", "RESP", "SOIL"],
        "ecvs": ["Soil moisture", "Groundwater", "Evaporation from land",
                 "Land cover", "Anthropogenic water use"],
    },
    "Southeast Asia": {
        "drivers": "Peat swamp forests store huge carbon per hectare; "
                   "draining and burning them emits 0.4 GtC/yr "
                   "(bookkeeping) — twice what DGVMs simulate, which the "
                   "paper flags as a likely DGVM underestimate. Net: about "
                   "neutral by DGVMs, a source by inversions.",
        "driver_source": "Friedlingstein et al. 2025, §3.8.2",
        "processes": ["PHOTO", "LUC", "FIRE", "SOIL"],
        "ecvs": ["Land cover", "Fire", "Soil carbon", "Soil moisture",
                 "Above-ground biomass",
                 "Fraction of absorbed photosynthetically active radiation (FAPAR)"],
    },
    "East Asia": {
        "drivers": "Regrowing forests — above all China's afforestation — "
                   "plus intensive cropland give a 0.2 GtC/yr sink that both "
                   "methods agree on. Land-use emissions are near zero.",
        "driver_source": "Friedlingstein et al. 2025, §3.8.2",
        "processes": ["PHOTO", "SOIL", "LUC"],
        "ecvs": ["Land cover", "Above-ground biomass",
                 "Fraction of absorbed photosynthetically active radiation (FAPAR)",
                 "Leaf area index", "Soil carbon", "Soil moisture"],
    },
    "South Asia": {
        "drivers": "Monsoon-fed croplands and forests: a small sink "
                   "(about 0.0–0.2 GtC/yr), strongly tied to monsoon rain "
                   "and irrigation.",
        "driver_source": "Friedlingstein et al. 2025, Fig. 15",
        "processes": ["PHOTO", "RESP", "SOIL"],
        "ecvs": ["Soil moisture", "River discharge", "Groundwater",
                 "Evaporation from land", "Land cover",
                 "Anthropogenic water use"],
    },
    "Australasia": {
        "drivers": "Arid interior and savannahs: a small, wildly variable "
                   "sink — wet years store carbon, drought and fire years "
                   "release it. ENSO sets the rhythm.",
        "driver_source": "Friedlingstein et al. 2025, Fig. 15",
        "processes": ["PHOTO", "RESP", "FIRE", "SOIL"],
        "ecvs": ["Soil moisture", "Fire", "Land cover",
                 "Evaporation from land", "Terrestrial water storage",
                 "Land surface temperature"],
    },
}


def download_gcb(path):
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [("User-Agent", "terrestrial-ledger fetch_data.py")]
    opener.open(GCB_URL)          # sets the licence cookie (302)
    with opener.open(GCB_URL) as r:  # with cookie -> the .xlsx
        data = r.read()
    if data[:2] != b"PK":
        raise SystemExit("GCB download did not return an xlsx file")
    with open(path, "wb") as f:
        f.write(data)
    print(f"downloaded {path} ({len(data)} bytes)")


def parse_gcb(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    # Terrestrial Sink sheet: header row 30, data from row 31, col1 year,
    # col2 GCB (adjusted), col3 GCB unadjusted
    ws = wb["Terrestrial Sink"]
    assert ws.cell(row=30, column=1).value == "Year"
    assert ws.cell(row=30, column=2).value == "GCB"
    series = []
    r = 31
    while True:
        y = ws.cell(row=r, column=1).value
        if y is None:
            break
        series.append((int(y), float(ws.cell(row=r, column=2).value)))
        r += 1
    # Historical Budget sheet: header row 16; col2 EFOS excl. carbonation,
    # col3 ELUC, col4 GATM, col5 SOCEAN, col6 SLAND, col7 cement carb, col8 BIM
    ws = wb["Historical Budget"]
    assert str(ws.cell(row=16, column=1).value).strip() == "Year"
    hist = {}
    r = 17
    while True:
        y = ws.cell(row=r, column=1).value
        if y is None:
            break
        hist[int(y)] = {
            "efos": ws.cell(row=r, column=2).value,
            "eluc": ws.cell(row=r, column=3).value,
            "gatm": ws.cell(row=r, column=4).value,
            "socean": ws.cell(row=r, column=5).value,
            "sland": ws.cell(row=r, column=6).value,
            "cement": ws.cell(row=r, column=7).value,
            "bim": ws.cell(row=r, column=8).value,
        }
        r += 1
    # cross-check: Terrestrial Sink GCB column must match Historical SLAND
    worst = 0.0
    for y, v in series:
        hv = hist[y]["sland"]
        worst = max(worst, abs(v - hv))
    print(f"cross-check Terrestrial Sink vs Historical Budget: worst diff "
          f"{worst:.6f} GtC/yr over {len(series)} years")
    assert worst < 0.01, "GCB series disagree between sheets"
    return series, hist


def build_regions():
    regions = {}
    for name, sland, eluc, net_dgvm, net_inv, src in REGIONS:
        regions[name] = {
            "sland_gtc": sland,
            "eluc_bkm_gtc": eluc,
            "net_dgvm_gtc": net_dgvm,
            "net_inv_gtc": net_inv,
            "value_source": src,
        }
    sum_dgvm = round(sum(r["net_dgvm_gtc"] for r in regions.values()), 2)
    sum_inv = round(sum(r["net_inv_gtc"] for r in regions.values()), 2)
    print(f"regions: DGVM nets sum to {sum_dgvm} GtC/yr, inversion nets "
          f"sum to {sum_inv} GtC/yr")
    return regions, sum_dgvm, sum_inv


def main():
    if not os.path.exists(GCB_XLSX):
        download_gcb(GCB_XLSX)
    series, hist = parse_gcb(GCB_XLSX)
    regions, sum_dgvm, sum_inv = build_regions()

    world = []
    for y, v in series:
        h = hist[y]
        world.append({
            "year": y,
            "sland_gtc": round(v, 3),
            "sland_gtco2": round(v * GTCO2_PER_GTC, 2),
            "efos_gtc": round(h["efos"], 3),
            "eluc_gtc": round(h["eluc"], 3),
            "gatm_gtc": round(h["gatm"], 3),
            "socean_gtc": round(h["socean"], 3),
            "net_land_gtc": round(v - h["eluc"], 3),
        })
    latest = world[-1]
    prev = world[-2]
    cum_gtc = round(sum(w["sland_gtc"] for w in world), 1)
    cum_emis = round(sum(hist[y]["efos"] + hist[y]["eluc"]
                         for y, _ in series), 1)
    decadal = {}
    for start in (1960, 1970, 1980, 1990, 2000, 2010):
        vals = [w["sland_gtc"] for w in world if start <= w["year"] < start + 10]
        decadal[str(start)] = round(sum(vals) / len(vals), 2)
    vals1524 = [w["sland_gtc"] for w in world if 2015 <= w["year"] <= 2024]
    net1524 = [w["net_land_gtc"] for w in world if 2015 <= w["year"] <= 2024]
    total_emis_latest = latest["efos_gtc"] + latest["eluc_gtc"]

    data = {
        "meta": {
            "title": "Terrestrial Ledger — annual land CO2 uptake by region",
            "latest_year": latest["year"],
            "first_year": world[0]["year"],
            "units": "GtC/yr (1 GtC = 1 PgC = 3.664 GtCO2)",
            "sources": {
                "gcb": "Friedlingstein et al. 2025, Global Carbon Budget 2025, "
                       "Earth Syst. Sci. Data 18, 3211-3288, "
                       "doi:10.5194/essd-18-3211-2026; data "
                       "doi:10.18160/GCP-2025 (spreadsheet via ICOS Carbon Portal)",
                "regions": "Friedlingstein et al. 2025, Sect. 3.8.2 and "
                           "Figure 15: decadal-mean (2015-2024) land fluxes "
                           "for the 10 RECCAP-2 land regions",
                "gcos": "GCOS Essential Climate Variables, terrestrial domain "
                        "(20 ECVs), gcos.wmo.int/en/essential-climate-variables "
                        "(accessed 2026-11-26); framework GTOS/TOPC, sponsored "
                        "jointly by GCOS, the FAO-led GTOS and WCRP",
                "processes": "Beer et al. 2010; Bond-Lamberty & Thomson 2010; "
                             "Batjes 1996; Jobbagy & Jackson 2000; Hugelius et "
                             "al. 2014; van der Werf et al. 2017 (GFED4.1s)",
            },
            "notes": [
                "GCB land sink (SLAND) is the natural land uptake: the "
                "average of 22 dynamic global vegetation models (S2 "
                "simulation), RSS-adjusted for land-cover bias, "
                "uncertainty +-0.5 GtC/yr on average (wider in single "
                "years; +-1.1 GtC/yr in 2024).",
                "Regional fluxes are DECADAL MEANS (2015-2024) from GCB "
                "2025 Fig. 15 / Sect. 3.8.2, not an annual series. No "
                "published annual regional land series exists. Values "
                "stated in the paper text are exact; the rest are read "
                "from Figure 15 to the nearest 0.05 GtC/yr (value_source "
                "'fig'). Net flux = SLAND - ELUC; positive = sink.",
                "Regional DGVM nets sum to more than the global net land "
                "flux (SLAND minus bookkeeping ELUC) because DGVMs "
                "underestimate ELUC in South America and Southeast Asia "
                "(GCB 2025 Sect. 3.8.2). The page states the reconciliation.",
                "Sign convention on this page: uptake is positive "
                "(carbon into the land); ELUC is shown as a positive "
                "emission (carbon out of the land).",
            ],
        },
        "world": world,
        "summary": {
            "latest_year": latest["year"],
            "latest_sland_gtc": latest["sland_gtc"],
            "latest_sland_gtco2": latest["sland_gtco2"],
            "prev_sland_gtc": prev["sland_gtc"],
            "yoy_pct": round((latest["sland_gtc"] - prev["sland_gtc"])
                             / prev["sland_gtc"] * 100, 1),
            "latest_total_emissions_gtc": round(total_emis_latest, 2),
            "latest_land_share_of_emissions_pct": round(
                latest["sland_gtc"] / total_emis_latest * 100, 1),
            "mean_2015_2024_gtc": round(sum(vals1524) / len(vals1524), 2),
            "mean_2015_2024_net_land_gtc": round(sum(net1524) / len(net1524), 2),
            "cumulative_1959_latest_gtc": cum_gtc,
            "cumulative_1959_latest_gtco2": round(cum_gtc * GTCO2_PER_GTC, 0),
            "cumulative_emissions_1959_latest_gtc": cum_emis,
            "cumulative_land_share_pct": round(cum_gtc / cum_emis * 100, 1),
            "decadal_means_gtc": decadal,
            "regions_dgvm_net_sum_gtc": sum_dgvm,
            "regions_inv_net_sum_gtc": sum_inv,
            "preliminary_2025_net_land_gtc": 2.36,
            "preliminary_2025_source": "Ciais et al. 2026, low-latency "
                "global carbon budget 2025, arXiv:2609.34226 (2.36 +- 0.16 "
                "GtC/yr; preliminary, not in the GCB series). NOTE: this is "
                "the NET land flux (sink minus land-use emissions), a "
                "different quantity from the SLAND series plotted here.",
        },
        "regions": regions,
        "region_detail": REGION_DETAIL,
        "ecvs": [{"name": n, "group": g, "role": r} for n, g, r in ECVS],
        "processes": PROCESSES,
        "region_reconciliation": {
            "dgvm_net_sum_gtc": sum_dgvm,
            "inv_net_sum_gtc": sum_inv,
            "global_net_land_2015_2024_gtc":
                round(sum(net1524) / len(net1524), 2),
            "note": "The ten regional DGVM net fluxes sum to "
                    f"{sum_dgvm} GtC/yr, above the global 2015-2024 mean "
                    "net land flux (SLAND minus bookkeeping ELUC) of "
                    f"{round(sum(net1524) / len(net1524), 2)} GtC/yr. The "
                    "gap is the DGVM underestimate of ELUC: in South "
                    "America the bookkeeping models put ELUC at ~0.5 "
                    "GtC/yr against ~0.3 in the DGVMs, and in Southeast "
                    "Asia ~0.4 against ~0.2 (GCB 2025 Sect. 3.8.2). "
                    "Regional shares are therefore not computed against a "
                    "single total on this page.",
        },
    }
    with open(OUT, "w") as f:
        json.dump(data, f, indent=1)
    print(f"wrote {OUT}")
    print(f"latest: {latest['year']} SLAND {latest['sland_gtc']} GtC/yr "
          f"({latest['sland_gtco2']} GtCO2/yr), "
          f"{data['summary']['yoy_pct']:+.1f}% vs {prev['year']}, "
          f"{data['summary']['latest_land_share_of_emissions_pct']}% of "
          f"total emissions")
    print(f"cumulative {world[0]['year']}-{latest['year']}: {cum_gtc} GtC "
          f"({data['summary']['cumulative_land_share_pct']}% of emissions)")


if __name__ == "__main__":
    main()
