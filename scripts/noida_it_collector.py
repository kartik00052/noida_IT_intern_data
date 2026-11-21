#!/usr/bin/env python3
"""
Noida / Greater Noida IT companies collector
Run:  pip install requests
      python noida_it_collector.py --enrich --limit 200
Output: noida_it_companies.csv, noida_it_companies.json
"""
import argparse, csv, json, math, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "noida-it-research/1.0 (student project)"}
BBOX = "28.30,77.28,28.66,77.62"  # south,west,north,east (Noida + Greater Noida)
OVERPASS = ["https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"]

# APPROXIMATE park anchors (lat, lon, radius_m). Used only to guess park; verify/edit.
PARKS = [
    ("P01", "Sector 62 IT Hub",        28.6270, 77.3730, 1500),
    ("P02", "Sector 63 / 64 Hub",      28.6240, 77.3800, 1200),
    ("P03", "Noida SEZ (NSEZ)",        28.5960, 77.3320, 1500),
    ("P04", "Sector 16 / Film City",   28.5980, 77.3250, 1000),
    ("P05", "Sector 125 Hub",          28.5450, 77.3330, 1500),
    ("P06", "Sector 126-132 Corridor", 28.5300, 77.3600, 2500),
    ("P07", "Sector 135-137 Corridor", 28.5100, 77.4050, 2500),
    ("P08", "Sector 142-144 Hub",      28.5000, 77.4300, 2000),
    ("P09", "Knowledge Park Greater Noida", 28.4750, 77.4980, 3000),
    ("P10", "Greater Noida West",      28.6000, 77.4300, 4000),
]
# Name keywords of known developments -> matched against company name/address
PARK_KEYWORDS = ["candor", "logix", "stellar", "advant", "assotech", "tech boulevard",
                 "unitech infospace", "embassy oxygen", "dlf", "nsl", "galaxy business",
                 "green boulevard", "knowledge boulevard", "ihdp", "techspace", "it park"]

EXCLUDE_OFFICE = {"government", "ngo", "estate_agent", "insurance", "lawyer", "accountant",
                  "educational_institution", "political_party", "religion", "travel_agent",
                  "tax_advisor", "association", "diplomatic", "foundation", "guide"}
TECH_HINT = re.compile(r"tech|soft|info|system|digital|cyber|data|cloud|lab|solution|analytic|"
                       r"\bit\b|ai\b|net|web|app|dev|consult|global|semi|electronic|robot|fin", re.I)

CATEGORY_RULES = [  # heuristic -> labelled INFERRED in output
    ("Fintech", r"fin|pay|bank|credit|wallet"), ("AI/ML", r"\bai\b|machine|analytic|data"),
    ("Cybersecurity", r"cyber|secur"), ("Healthcare Technology", r"health|med|pharma"),
    ("Semiconductor", r"semi|chip|vlsi|electronic"), ("SaaS", r"saas|cloud"),
    ("IT Services", r"soft|tech|infotech|system|solution|digital|consult"),
]

TECH = {
    "Java": r"\bjava\b", "Spring Boot": r"spring ?boot", "Python": r"\bpython\b",
    "JavaScript": r"javascript", "TypeScript": r"typescript", "React": r"\breact(\.js|js)?\b",
    "Angular": r"\bangular", "Node.js": r"node\.?js", "Django": r"django", "FastAPI": r"fastapi",
    ".NET": r"\.net\b|c#", "C++": r"c\+\+", "Go": r"\bgolang\b|\bgo developer",
    "SQL": r"\bsql\b", "PostgreSQL": r"postgres", "MongoDB": r"mongodb", "Redis": r"\bredis",
    "Spark": r"\bspark\b", "Kafka": r"kafka", "Airflow": r"airflow", "Snowflake": r"snowflake",
    "Databricks": r"databricks", "PyTorch": r"pytorch", "TensorFlow": r"tensorflow",
    "LangChain": r"langchain", "LLM": r"\bllm", "RAG": r"\brag\b", "MLOps": r"mlops",
    "AWS": r"\baws\b|amazon web", "Azure": r"azure", "GCP": r"google cloud|\bgcp\b",
    "Docker": r"docker", "Kubernetes": r"kubernetes|\bk8s", "Terraform": r"terraform",
    "Jenkins": r"jenkins", "SAP": r"\bsap\b", "Salesforce": r"salesforce",
}


def hav(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(x))


def overpass():
    q = f"""[out:json][timeout:150];
    (nwr["office"]["name"]({BBOX});
     nwr["name"~"tech|soft|infotech|systems|digital|cyber|data|cloud|labs|analytics|IT Park|techspace",i]
        ["building"~"office|commercial"]({BBOX}););
    out center tags;"""
    for url in OVERPASS:
        for attempt in range(1, 4):
            try:
                r = requests.post(url, data={"data": q}, headers=UA, timeout=180)
                r.raise_for_status()
                return r.json()["elements"]
            except Exception as e:
                print(f"[warn] {url} attempt {attempt}/3: {e}", file=sys.stderr)
                if attempt < 3:
                    time.sleep(2 ** attempt)
    sys.exit("Overpass failed on all mirrors after 3 attempts each. Retry later.")


def norm(n):
    return re.sub(r"\b(pvt|private|ltd|limited|india|llp|inc|technologies|technology)\b|[^a-z0-9]", "",
                  n.lower())


def assign_park(name, addr, lat, lon):
    text = f"{name} {addr}".lower()
    for k in PARK_KEYWORDS:
        if k in text:
            return None, k.title(), "name/address keyword"
    best = None
    for pid, pname, plat, plon, rad in PARKS:
        d = hav(lat, lon, plat, plon)
        if d <= rad and (best is None or d < best[0]):
            best = (d, pid, pname)
    return (best[1], best[2], f"within {int(best[0])}m of approx anchor") if best else (None, None, None)


def classify(name):
    for cat, pat in CATEGORY_RULES:
        if re.search(pat, name, re.I):
            return cat
    return "IT Services"


def build(elements, limit):
    seen, rows = {}, []
    for e in elements:
        t = e.get("tags", {})
        name = t.get("name", "").strip()
        if not name or t.get("office") in EXCLUDE_OFFICE:
            continue
        if not (t.get("office") in {"it", "software", "company", "research", "telecommunication"}
                or TECH_HINT.search(name)):
            continue
        lat = e.get("lat") or e.get("center", {}).get("lat")
        lon = e.get("lon") or e.get("center", {}).get("lon")
        if lat is None:
            continue
        key = norm(name)
        if not key or key in seen:
            continue
        addr = ", ".join(filter(None, [t.get("addr:housenumber"), t.get("addr:street"),
                                       t.get("addr:suburb"), t.get("addr:city")]))
        pid, pname, why = assign_park(name, addr, lat, lon)
        site = t.get("website") or t.get("contact:website")
        if site and not site.startswith("http"):
            site = "http://" + site
        seen[key] = 1
        rows.append({
            "company_id": f"C{len(rows)+1:04d}", "company_name": name,
            "company_category": classify(name), "category_confidence": "INFERRED",
            "osm_office_tag": t.get("office"), "park_id": pid, "park_name": pname,
            "park_match_basis": why, "address": addr or None, "latitude": lat, "longitude": lon,
            "phone": t.get("phone") or t.get("contact:phone"),
            "email": t.get("email") or t.get("contact:email"),
            "website": site, "linkedin_url": None, "careers_url": None,
            "tech_stack": [], "tech_confidence": "UNKNOWN", "tech_evidence_url": None,
            "source": f"https://www.openstreetmap.org/{e['type']}/{e['id']}",
            "verification_status": "OSM_LISTED_UNVERIFIED", "last_verified": str(date.today()),
        })
    # prefer entries with website/park so the 'best' 200 come first
    rows.sort(key=lambda r: (r["website"] is None, r["park_id"] is None and r["park_name"] is None))
    rows = rows[:limit]
    for i, r in enumerate(rows, 1):
        r["company_id"] = f"C{i:04d}"
    return rows


def get(url):
    try:
        r = requests.get(url, headers=UA, timeout=10)
        return r.text if r.ok and "text" in r.headers.get("content-type", "") else ""
    except Exception:
        return ""


def enrich(r):
    if not r["website"]:
        return r
    home = get(r["website"])
    if not home:
        return r
    ln = re.search(r'href="(https?://[a-z.]*linkedin\.com/company/[^"?#]+)', home, re.I)
    r["linkedin_url"] = ln.group(1) if ln else None
    if not r["phone"]:
        tel = re.search(r'href="tel:([+\d\-\s()]{7,20})"', home)
        r["phone"] = tel.group(1).strip() if tel else None
    m = re.search(r'href="([^"]*(?:career|jobs|join-us|work-with-us)[^"]*)"', home, re.I)
    if m:
        r["careers_url"] = urljoin(r["website"], m.group(1))
        page = get(r["careers_url"]).lower()
        found = sorted(k for k, p in TECH.items() if re.search(p, page, re.I))
        if found:
            r["tech_stack"], r["tech_confidence"] = found, "PUBLICLY_REPORTED"
            r["tech_evidence_url"] = r["careers_url"]
    return r


def save(rows, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "noida_it_companies.json", "w", encoding="utf-8") as f:
        json.dump({"metadata": {"generated": str(date.today()), "total": len(rows),
                                 "note": "Parks assigned via approx anchors; verify before use"},
                   "companies": rows}, f, indent=2, ensure_ascii=False)
    with open(out_dir / "noida_it_companies.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({**r, "tech_stack": "; ".join(r["tech_stack"])})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--enrich", action="store_true", help="scan websites for careers/phone/tech")
    ap.add_argument("--seed", help="optional CSV with columns: company_name,website,park_name")
    ap.add_argument("--out-dir", type=Path, default=ROOT / 'data',
                    help="output directory (default: repo data/)")
    a = ap.parse_args()

    print("Querying OpenStreetMap...")
    rows = build(overpass(), a.limit)
    if not rows:
        print("No companies matched the Overpass query; nothing written.", file=sys.stderr)
        sys.exit(1)

    if a.seed:  # add your own verified companies
        known = {norm(r["company_name"]) for r in rows}
        for s in csv.DictReader(open(a.seed, encoding="utf-8")):
            if norm(s["company_name"]) not in known:
                rows.append({**{k: None for k in rows[0]}, "company_name": s["company_name"],
                             "website": s.get("website"), "park_name": s.get("park_name"),
                             "company_category": "IT Services", "category_confidence": "INFERRED",
                             "tech_stack": [], "tech_confidence": "UNKNOWN",
                             "verification_status": "USER_SEEDED",
                             "last_verified": str(date.today())})
        for i, r in enumerate(rows, 1):
            r["company_id"] = f"C{i:04d}"

    if a.enrich:
        print(f"Enriching {len(rows)} companies (careers, phone, tech)...")
        with ThreadPoolExecutor(12) as ex:
            rows = list(ex.map(enrich, rows))

    if not rows:
        print("No companies to save; nothing written.", file=sys.stderr)
        sys.exit(1)
    save(rows, a.out_dir)
    withsite = sum(1 for r in rows if r["website"])
    print(f"Done: {len(rows)} companies, {withsite} with website, "
          f"{sum(1 for r in rows if r['careers_url'])} careers links, "
          f"{sum(1 for r in rows if r['tech_stack'])} with tech evidence.")
