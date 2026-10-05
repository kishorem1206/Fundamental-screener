#!/usr/bin/env python3
"""
Generate nifty_total_market.json seed file.

Steps:
1. Batch-download 5d price data for all candidate symbols (one yfinance call).
2. Filter to symbols that have actual data.
3. Fetch company info in parallel (ThreadPoolExecutor).
4. Emit scripts/seeds/nifty_total_market.json in the same format as nifty50.json.

Run: python3 scripts/generate_ntm_seed.py
"""

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yfinance as yf

# ── Symbol roster ────────────────────────────────────────────────────────────
# (symbol, index_hint) where index_hint drives market_cap_category fallback.
# Nifty 50 are included so universe memberships are updated correctly.

NIFTY_50 = [
    "ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK","BAJAJ-AUTO",
    "BAJAJFINSV","BAJFINANCE","BHARTIARTL","BPCL","BRITANNIA",
    "CIPLA","COALINDIA","DIVISLAB","DRREDDY","EICHERMOT",
    "GRASIM","HCLTECH","HDFCBANK","HDFCLIFE","HEROMOTOCO",
    "HINDALCO","HINDUNILVR","ICICIBANK","INDUSINDBK","INFY",
    "ITC","JSWSTEEL","KOTAKBANK","LT","M&M",
    "MARUTI","NESTLEIND","NTPC","ONGC","POWERGRID",
    "RELIANCE","SBILIFE","SBIN","SHRIRAMFIN","SUNPHARMA",
    "TATACONSUM","TATAMOTORS","TATASTEEL","TCS","TECHM",
    "TITAN","TRENT","ULTRACEMCO","UPL","WIPRO",
]

NIFTY_NEXT_50 = [
    "ABB","ADANIENT","AMBUJACEM","ATGL","BANDHANBNK",
    "BANKBARODA","BEL","BERGEPAINT","BHARATFORG","BSE",
    "CANBK","CGPOWER","CHOLAFIN","COLPAL","CUMMINSIND",
    "DABUR","DLF","DMART","GAIL","GODREJCP",
    "GODREJPROP","HAL","HAVELLS","ICICIGI","ICICIPRULI",
    "INDIGO","IOC","IRCTC","IRFC","JSWENERGY",
    "LODHA","LTIM","LTTS","LUPIN","M&MFIN",
    "MARICO","MPHASIS","MUTHOOTFIN","NAUKRI","NHPC",
    "OFSS","PAGEIND","PFC","PIDILITIND","POLYCAB",
    "RECLTD","SIEMENS","TATAPOWER","TORNTPHARM","VEDL",
]

NIFTY_MIDCAP_150 = [
    "AARTIIND","ABCAPITAL","ABFRL","ALKEM","APLAPOLLO",
    "ASHOKLEY","ASTRAL","AUBANK","AUROPHARMA","BALKRISIND",
    "BATAINDIA","BIKAJI","BLUESTARCO","BRIGADE","BSOFT",
    "CAMS","CARBORUNIV","CDSL","CEATLTD","CLEAN",
    "COFORGE","CONCOR","CROMPTON","DEEPAKNTR","DELHIVERY",
    "DIXON","EMAMILTD","ESCORTS","EXIDEIND","FIVESTAR",
    "FEDERALBNK","FORTIS","GLENMARK","GMRINFRA","GODREJIND",
    "GRANULES","GRSE","HDFCAMC","HINDPETRO","HONAUT",
    "HUDCO","IDFCFIRSTB","INDIAMART","INDHOTEL","IPCALAB",
    "JBCHEPHARM","JKCEMENT","JUBILANT","JUBLFOOD","KALPATPOWR",
    "KARURVYSYA","KEC","KFINTECH","KPITTECH","LALPATHLAB",
    "LATENTVIEW","LICHSGFIN","LUXIND","MAXHEALTH","MAZDOCK",
    "MCXINDIA","METROPOLIS","MFSL","MGL","MOTILALOFS",
    "MRPL","NATIONALUM","NAVINFLUOR","NCC","NLCINDIA",
    "NMDC","NYKAA","OBEROIRLTY","OIL","PAYTM",
    "PERSISTENT","PETRONET","PNB","PRAJ","PRESTIGE",
    "PRINCEPIPE","RADICO","RAILTEL","RAMCOCEM","RBLBANK",
    "RVNL","SCHAEFFLER","SJVN","SKFINDIA","SOBHA",
    "SOLARINDS","STARHEALTH","SUMICHEM","SUNDARMFIN","SUNDRMFAST",
    "SUNTV","SUZLON","TATACHEM","TATAELXSI","TIINDIA",
    "TITAGARH","TORNTPOWER","TRIDENT","TTKPRESTIG","UJJIVANSFB",
    "UNIPARTS","UTIAMC","VAIBHAVGBL","VGUARD","VINATIORGA",
    "VBL","VOLTAS","WELCORP","WELSPUNIND","ZEEL",
    # extra midcap candidates
    "AARTIFERT","ATUL","AVANTIFEED","CANFINHOME","CESC",
    "CENTURYPLY","CENTURYTEX","CHAMBLFERT","CHENNPETRO","CLSEL",
    "COCHINSHIP","DCMSHRIRAM","EIDPARRY","EQUITASBNK",
    "GHCL","GNFC","GPPL","GRINDWELL","GSFC",
    "HAPPSTMNDS","HFCL","HIMATSEIDE","HINDCOPPER",
    "INDIGOPNTS","JKPAPER","JKTYRE","JMFINANCIL","JYOTHYLAB",
    "KAJARIACER","KPRMILL","KSCL","LGBBROSLTD","LLOYDMETAL",
    "LUMAXIND","MAPMYINDIA","MIDHANI","MMTC","MOIL",
    "MOTHERSON","MUTHOOTMFIN","NAVNETEDUL","NBCC","NILKAMAL",
    "NSLNISP","ORCHPHARMA","PFIZER","POLYMED","PNCINFRA",
    "PSPPROJECT","PURVA","RAJESHEXPO","RATNAMANI",
    "REDINGTON","RENUKA","RITES","ROUTE","RPOWER",
    "SAURASHCEM","SBICARD","SOMANYCERA","SOUTHBANK","SRTRANSFIN",
    "STARCEMENT","SUBROS","SUPRAJIT","SUVEN","SWANENERGY",
    "SWSOLAR","TATAINVEST","TCIEXP","THIRUMALAI","UFLEX",
    "UNIONBANK","VSTIND","VMART","WELSPUNLIV","WOCKPHARMA",
    "YESBANK","ZFCVINDIA",
]

NIFTY_SMALLCAP_250 = [
    "AAVAS","AARTIDRUGS","AFFLE","AKZOINDIA","ALLCARGO",
    "AMARAJABAT","ANURAS","APTUS","ARCHEAN","ARVINDFASN",
    "ASAHIINDIA","ASTERDM","BALRAMCHIN","BAYERCROP","BFUTILITIE",
    "BIRLASOFT","BOROLTD","CAMPUS","CARERATING","CERA",
    "CHEMCON","DEEPAK","DHANUKA","DBCORP","DATAMATICS",
    "DHANI","EDELWEISS","EIH","EMKAY","ESTER",
    "FINCABLES","FLAIR","GALAXYSURF","GARWARE","GODREJAGRO",
    "GESHIP","GRAPHITE","GUJFLUORO","HAPPSTMNDS","HINDOILEXP",
    "IBULHSGFIN","IIFLSEC","INDIACEM","INDIANB","INOXWIND",
    "IOLCP","IRCON","ITDC","JBMA","JINDALSAW",
    "KAVVERI","KEEI","KELTECH","KOCL","KOLTE",
    "LEMONTREE","LGBBROS","MACROTECH","MANAPPURAM","MEDIASSIST",
    "MINDTREE","MNGL","MHRIL","MONTECARLO","MOSCHIP",
    "NACLIND","NITIRAJ","NMDC","NOCIL","NTPCGREEN",
    "OLECTRA","ORIENTELEC","PATANJALI","PCJEWELLER","PDSL",
    "PGHH","PILOTNDRV","PIRAMALPHM","POLYMED","PRAJIND",
    "PREMIERPOL","PRINCEPIPE","PURVA","RAJESHEXPO",
    "RCOM","RELINFRA","RENUKA","RITCO","RUPA",
    "SAPPHIRE","SEPC","SIRCA","SMLISUZU","SOBHA",
    "SOLARA","SOMANYCERA","SOUTHBANK","STCINDIA","STERLING",
    "SSWL","SUBROS","SUPRAJIT","SUVEN","SWANENERGY",
    "SWSOLAR","TATAINVEST","TBOTEK","THIRUMALAI","TNPL",
    "THOMASCOOK","THYROCARE","TRIVENI","UFLEX","UJJIVANSFB",
    "USHAMARTIN","VSTIND","VMART","WELSPUNLIV","WINDMACHINE",
    "WOCKPHARMA","YESBANK","ZFCVINDIA","ZENTEC",
    # additional smallcap candidates
    "AARTIDRUGS","AJANTPHARM","ALEMBICLTD","ALEMBICPH","AMRUTANJAN",
    "ANDHRSUGAR","ASTRAMICRO","BEML","BFINVEST","BLKASHYAP",
    "BURNPUR","CALCOM","CAPLIPOINT","CCL","CCHHL",
    "CRISIL","DBREALTY","DEEPAKNTR","DFMFOODS","DISA",
    "DPWIRES","DYNPRO","EASTSILK","EFFICIENEW","ELGIEQUIP",
    "EMMBI","EMAMIREALT","ENDURANCE","ENGINERSIN","EPIGRAL",
    "EROSMEDIA","FAARSA","FCEL","FINPIPE","FORCEMOT",
    "GABRIEL","GAEL","GALAXYSURF","GARGSONS","GESHIP",
    "GHCL","GLAXO","GMMPFAUDLR","GNFC","GPIL",
    "GTLINFRA","GUJALKALI","GULFOILLUB","HBLPOWER","HERITGFOOD",
    "HEROMOTOCO","HEXAWARE","HINDZINC","HUBTOWN","ICICIB22",
    "IGIL","IITL","IMAGEINDI","IMFA","INDIAGLYCOL",
    "INFOSONICS","INTELLECT","ISGEC","ISMT","ITDCEM",
    "JKIL","JKLAKSHMI","JKPAPER","JSPL","JUBL",
    "KALYANKJIL","KANCHI","KBCGLOBAL","KCP","KILITCH",
    "KNRCON","KPIL","KRBL","KREBSBIO","KUNALORG",
    "L&TFH","LAOPALA","LOTUSEYE","LXCHEM","LYPSA",
    "MAHINDCIE","MAHLOG","MAHSCOOTER","MAITHANALL","MARSHALLS",
    "MATASFIN","MATTHAN","MBAPL","MBLINFRA","MCCL",
    "MEDANTA","MEDIAPANEL","MHAH","MICELINDIA","MINCHEM",
    "MOHITIND","MOSCHIP","MPCL","MRFIN","MSTPL",
    "NAGAFERT","NATHBIOGEN","NCLIND","NETFLTD","NEULANDLAB",
    "NIITTECH","NILE","NILKAMAL","NIRBHAY","NKIND",
    "NOVOCO","NSIL","NSLNISP","NUVOCO","OBCL",
    "ONMOBILE","ORCHPHARMA","ORIFLAME","ORTINLABS","PDSL",
    "PGHH","PHOENIXLTD","PLASTIBLEN","PMCFIN","POINTWELL",
    "POLYMED","POOJA","POWERMECH","PRAJIND","PREMIERPOL",
    "PRINCEPIPE","PRSMJOHNSN","PSALINS","PSPPROJECT","PVRINOX",
    "QUICKHEAL","QUINT","RADHAGOV","RAILTEL","RAJIND",
    "RAJRATAN","RANBAXY","RATNAMANI","RBLBANK","RCCL",
    "RCF","RECRO","RELAXO","REPCO","RITES",
    "ROUTE","RPOWER","RSWM","RUPA","RUSHIL",
    "SADBHAV","SAFARI","SALASAR","SALONA","SAREGAMA",
    "SATIN","SATIA","SAURASHCEM","SBICARD","SBICPSE",
    "SBILIFE","SELAN","SENCO","SEPC","SETCO",
    "SHAREINDIA","SHARDACROP","SHARDAMOTR","SHILPI","SHIVALIK",
    "SHIVOM","SHOPERSTOP","SIEMENS","SIGNATUREG","SILGO",
    "SIMAL","SINTERCOM","SIRCA","SIS","SITI",
    "SJS","SJVNL","SKIPPER","SKYGOLD","SMLISUZU",
    "SNOWMAN","SOBHA","SOLARA","SOLARINDS","SOMANYCERA",
    "SONATSOFTW","SPENCERS","SRTRANSFIN","SRTRANSPORTS","STARTIND",
    "STCINDIA","STERLING","STML","STUDENTFIN","SUKHJITS",
    "SUNTECK","SUPRAJIT","SUPRIYA","SUVEN","SUZLONFIN",
    "SWSOLAR","SYMPHONY","SYNGENE","TAHERLABS","TAINWALA",
    "TALBROS","TANLA","TAPARIA","TASTYBITEF","TATACOFFEE",
    "TATAINVEST","TATAMTRDVR","TBOTEK","TCIEXP","TCNSBRANDS",
    "TECHNOE","TECHNOELEC","TEJAS","THANGAMAYL","THIRUMALAI",
    "TIMETECHNO","TNPL","TORNTPHARM","TRIDENT","TRIVENI",
    "TTKHLTCARE","TTKPRESTIG","TV18BRDCST","TVTODAY","TVSSCS",
    "TVSSRICHAK","TVSMOTOR","UGARSUGAR","UJJIVANSFB","ULTRAMARINE",
    "UMANGDAIRY","UNIPHOS","UNOMINDA","UPCL","URJA",
    "USHAMARTIN","V2RETAIL","VAIBHAVGBL","VARROC","VGUARD",
    "VIKASECO","VIPIND","VIRINCHI","VMART","VOLTAMP",
    "VSTIND","WAAREEENER","WABCO","WEBELSOLAR","WELSPUNLIV",
    "WELSPUNIND","WINDMACHINE","WIMPLAST","WONDERLA","WOCKPHARMA",
    "XCHANGING","YESBANK","YUKEN","ZEELEARN","ZENSARTECH",
]

# ── Build candidate list ──────────────────────────────────────────────────────

def _build_candidates() -> list[tuple[str, str, str]]:
    """Returns list of (symbol, index_label, market_cap_category)."""
    seen: set[str] = set()
    result: list[tuple[str, str, str]] = []

    def add(symbols, label, mcap):
        for s in symbols:
            if s not in seen:
                seen.add(s)
                result.append((s, label, mcap))

    add(NIFTY_50, "NIFTY_50", "LARGE_CAP")
    add(NIFTY_NEXT_50, "NIFTY_NEXT_50", "LARGE_CAP")
    add(NIFTY_MIDCAP_150, "NIFTY_MIDCAP_150", "MID_CAP")
    add(NIFTY_SMALLCAP_250, "NIFTY_SMALLCAP_250", "SMALL_CAP")
    return result

# ── Sector mapping from Yahoo Finance ────────────────────────────────────────

_YF_SECTOR_MAP: dict[str, tuple[str, str]] = {
    "Technology":             ("Information Technology", "Information Technology"),
    "Financial Services":     ("Financial Services",      "Financial Services"),
    "Consumer Cyclical":      ("Consumer Discretionary",  "Consumer Discretionary"),
    "Consumer Defensive":     ("Consumer Staples",        "Consumer Staples"),
    "Healthcare":             ("Healthcare",               "Healthcare"),
    "Industrials":            ("Industrials",              "Industrials"),
    "Basic Materials":        ("Materials",                "Materials"),
    "Energy":                 ("Energy",                   "Energy"),
    "Utilities":              ("Utilities",                "Utilities"),
    "Real Estate":            ("Real Estate",              "Real Estate"),
    "Communication Services": ("Communication Services",   "Communication Services"),
}

def _map_sector(yf_sector: str) -> tuple[str, str]:
    return _YF_SECTOR_MAP.get(yf_sector, ("Other", "Other"))

# ── Market-cap category from reported value ───────────────────────────────────
# yfinance returns marketCap in INR for .NS tickers

def _categorize_mcap(mcap: float | None, fallback: str) -> str:
    if not mcap:
        return fallback
    # INR thresholds: LARGE > ₹20,000 Cr = 200B; MID > ₹5,000 Cr = 50B; SMALL > ₹500 Cr = 5B
    if mcap >= 200_000_000_000:
        return "LARGE_CAP"
    if mcap >= 50_000_000_000:
        return "MID_CAP"
    if mcap >= 5_000_000_000:
        return "SMALL_CAP"
    return "MICRO_CAP"

# ── Universe membership map ───────────────────────────────────────────────────

_UNIVERSE_PROGRESSION = {
    "NIFTY_50":         ["NIFTY_50", "NIFTY_500", "NIFTY_TOTAL_MARKET"],
    "NIFTY_NEXT_50":    ["NIFTY_500", "NIFTY_TOTAL_MARKET"],
    "NIFTY_MIDCAP_150": ["NIFTY_500", "NIFTY_TOTAL_MARKET"],
    "NIFTY_SMALLCAP_250": ["NIFTY_500", "NIFTY_TOTAL_MARKET"],
}

# ── Fetch info for one symbol ─────────────────────────────────────────────────

def _fetch_info(symbol: str, fallback_mcap: str) -> dict | None:
    yf_sym = f"{symbol}.NS"
    try:
        t = yf.Ticker(yf_sym)
        info = t.info
        name = info.get("longName") or info.get("shortName")
        if not name:
            return None
        yf_sector = info.get("sector", "")
        sector, macro = _map_sector(yf_sector)
        mcap = info.get("marketCap")
        return {
            "name": name,
            "sector": sector,
            "macro_sector": macro,
            "industry": info.get("industry", ""),
            "mcap_category": _categorize_mcap(mcap, fallback_mcap),
            "isin": None,
        }
    except Exception:
        return None

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    candidates = _build_candidates()
    print(f"Candidates: {len(candidates)}")

    # Step 1 — batch-download 5d bars to find which symbols exist
    print("Batch-validating symbols via yfinance download …")
    all_ns = [f"{s}.NS" for s, _, _ in candidates]

    try:
        import pandas as pd
        prices = yf.download(all_ns, period="5d", progress=False, threads=True, auto_adjust=True)
        if hasattr(prices.columns, "levels"):
            # multi-level columns → get 'Close' level
            close = prices["Close"] if "Close" in prices else prices.xs("Close", axis=1, level=0)
        else:
            close = prices
        valid_ns = {col for col in close.columns if close[col].dropna().shape[0] > 0}
    except Exception as e:
        print(f"Batch download error: {e}\nFalling back: all candidates assumed valid.")
        valid_ns = {f"{s}.NS" for s, _, _ in candidates}

    valid_candidates = [(s, idx, mc) for s, idx, mc in candidates if f"{s}.NS" in valid_ns]
    print(f"Valid symbols: {len(valid_candidates)}")

    # Step 2 — fetch company info in parallel
    print("Fetching company info in parallel (20 workers) …")
    start = time.time()
    stock_infos: dict[str, dict] = {}

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(_fetch_info, s, mc): (s, idx, mc) for s, idx, mc in valid_candidates}
        done = 0
        for fut in as_completed(futures):
            s, idx, mc = futures[fut]
            done += 1
            if done % 50 == 0:
                print(f"  {done}/{len(valid_candidates)} done …")
            info = fut.result()
            if info:
                stock_infos[s] = {**info, "index_label": idx}

    print(f"Got info for {len(stock_infos)} stocks in {time.time()-start:.0f}s")

    # Step 3 — build seed JSON
    seed_stocks = []
    for s, idx, mc in valid_candidates:
        info = stock_infos.get(s)
        if not info:
            # Use symbol as placeholder name if info fetch failed
            info = {
                "name": s,
                "sector": "Other",
                "macro_sector": "Other",
                "industry": "",
                "mcap_category": mc,
                "isin": None,
                "index_label": idx,
            }
        seed_stocks.append({
            "symbol": s,
            "exchange": "NSE",
            "companyName": info["name"],
            "isin": info.get("isin"),
            "sector": info["sector"],
            "industry": info.get("industry", ""),
            "basicIndustry": "",
            "macroSector": info["macro_sector"],
            "marketCapCategory": info["mcap_category"],
            "universes": _UNIVERSE_PROGRESSION.get(idx, ["NIFTY_TOTAL_MARKET"]),
        })

    seed = {
        "_meta": {
            "created": "2026-08-22",
            "source": "NSE Nifty Total Market — generated via yfinance Aug 2025",
            "notes": "Covers Nifty 50, Next 50, Midcap 150, Smallcap 250 + additional candidates.",
            "total": len(seed_stocks),
        },
        "universes": [
            {
                "id": "NIFTY_50",
                "name": "Nifty 50",
                "description": "NSE Nifty 50 Index — top 50 companies by free-float market capitalisation",
                "isBuiltIn": True,
            },
            {
                "id": "NIFTY_500",
                "name": "Nifty 500",
                "description": "NSE Nifty 500 Index — top 500 companies by free-float market capitalisation",
                "isBuiltIn": True,
            },
            {
                "id": "NIFTY_TOTAL_MARKET",
                "name": "Nifty Total Market",
                "description": "NSE Nifty Total Market — ~750 actively traded equity stocks",
                "isBuiltIn": True,
            },
        ],
        "stocks": seed_stocks,
    }

    out_path = Path(__file__).parent / "seeds" / "nifty_total_market.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(seed, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ Wrote {len(seed_stocks)} stocks → {out_path}")


if __name__ == "__main__":
    main()
