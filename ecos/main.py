import os, csv, requests
from datetime import datetime
from dotenv import load_dotenv

BASE = "https://ecos.bok.or.kr/api"

def now_ym(): return datetime.now().strftime("%Y%m")

def ecos(key, stat, period, start, end, item=None):
    url = f"{BASE}/StatisticSearch/{key}/json/kr/1/10000/{stat}/{period}/{start}/{end}/"
    if item: url += f"{item}/"
    r = requests.get(url, timeout=20)
    j = r.json()
    
    return j.get("StatisticSearch", {}).get("row", [])

def pick(rows, keys):
    if not keys: return rows
    return [r for r in rows if any(k in (r.get("ITEM_NAME1") or "") for k in keys)]

def dedup(rows):
    d = {}
    for r in rows: d[r["TIME"]] = r
    return [d[k] for k in sorted(d)]

def save(path, rows):
    rows = dedup(sorted(rows, key=lambda x: x["TIME"]))
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["date","value","unit","stat_name","item_name"])
        for r in rows:
            w.writerow([r.get("TIME"), r.get("DATA_VALUE"), r.get("UNIT_NAME"), r.get("STAT_NAME"), r.get("ITEM_NAME1")])

if __name__ == "__main__":
    load_dotenv()
    key = os.getenv("ECOS_API_KEY")
    start, end = "202401", now_ym()
    os.makedirs("economic_data", exist_ok=True)

    cfg = [
        ("base_rate.csv", "722Y001", "M", "0101000", ["한국은행 기준금리"]),
        ("market_rate.csv", "721Y001", "M", None, ["국고채(3년)", "국고채(10년)", "회사채(3년,AA-)", "회사채(3년,BBB-)"]),
        ("exchange_rate.csv", "731Y006", "M", None, ["원/달러(종가 15:30)"]),
        ("cpi.csv", "901Y009", "M", "0", ["총지수"]),
        ("ppi_materials.csv", "404Y014", "M", None, ["비금속광물", "목재및목제품", "기타비금속광물제품", "철강1차제품", "금속가공제품", "전선및케이블"]),
        ("import_price.csv", "401Y015", "M", None, ["비금속광물", "목재및목제품", "기타비금속광물제품", "철강1차제품", "금속가공제품", "전선및케이블"]),
        ("m2_growth.csv", "101Y003", "M", None, ["전기대비증감률"]),
        ("esi.csv", "513Y001", "M", None, ["경제심리지수"]),
        ("ccsi.csv", "511Y002", "M", None, ["소비자심리지수"]),
        ("bsi_construction_actual.csv", "512Y007", "M", "F4100", ["건설업"]),
        ("bsi_construction_outlook.csv", "512Y008", "M", "F4100", ["건설업"]),
        ("leading_index.csv", "901Y067", "M", None, ["선행지수순환변동치"]),
        ("house_price.csv", "901Y062", "M", None, ["총지수"]),
        ("house_rent.csv", "901Y063", "M", None, ["총지수"]),
    ]

    for fname, stat, per, item, keys in cfg:
        rows = ecos(key, stat, per, start, end, item)
        rows = pick(rows, keys)
        if rows:
            save(os.path.join("economic_data", fname), rows)
