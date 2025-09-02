import os, csv, requests, time
from datetime import datetime
from dotenv import load_dotenv

BASE = "https://ecos.bok.or.kr/api"

def now_ym(): 
    return datetime.now().strftime("%Y%m")

def ecos(key, stat, period, start, end, item=None):
    url = f"{BASE}/StatisticSearch/{key}/json/kr/1/10000/{stat}/{period}/{start}/{end}/"
    if item: url += f"{item}/"
    time.sleep(1)  # API 호출 간격
    
    try:
        r = requests.get(url, timeout=30)
        j = r.json()
        return j["StatisticSearch"]["row"] if "StatisticSearch" in j and "row" in j["StatisticSearch"] else []
    except:
        return []

def pick(rows, keys):
    if not keys: return rows
    return [r for r in rows if r.get("ITEM_NAME1") in keys]

def collect_multiple_items(key, stat, period, start, end, item_names):
    """여러 품목을 수집하여 하나의 리스트로 반환"""
    all_rows = []
    rows = ecos(key, stat, period, start, end, None)
    
    for item_name in item_names:
        matching_rows = [r for r in rows if r.get("ITEM_NAME1") == item_name]
        all_rows.extend(matching_rows)
    
    return all_rows

def calculate_growth_rate(rows):
    """전기대비 증가율 계산"""
    rows = sorted(rows, key=lambda x: x["TIME"])
    growth_rows = []
    
    for i in range(1, len(rows)):
        try:
            prev_val = float(rows[i-1]["DATA_VALUE"])
            curr_val = float(rows[i]["DATA_VALUE"])
            if prev_val != 0:
                growth_rate = ((curr_val - prev_val) / prev_val) * 100
                growth_row = rows[i].copy()
                growth_row["DATA_VALUE"] = f"{growth_rate:.2f}"
                growth_row["UNIT_NAME"] = "%"
                growth_rows.append(growth_row)
        except:
            continue
    return growth_rows

def save(path, rows):
    if not rows: return
    
    # 중복 제거
    seen = set()
    unique_rows = []
    for r in rows:
        key = f"{r['TIME']}_{r.get('ITEM_NAME1', '')}"
        if key not in seen:
            seen.add(key)
            unique_rows.append(r)
    
    rows = sorted(unique_rows, key=lambda x: x["TIME"])
    
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["date","value","unit","stat_name","item_name"])
        for r in rows:
            w.writerow([r.get("TIME"), r.get("DATA_VALUE"), r.get("UNIT_NAME"), r.get("STAT_NAME"), r.get("ITEM_NAME1")])

def save_individual(base_name, rows):
    """개별 파일로 저장"""
    if not rows: return
    
    items = {}
    for r in rows:
        item = r.get("ITEM_NAME1", "")
        if item:
            if item not in items: items[item] = []
            items[item].append(r)
    
    for item, item_rows in items.items():
        safe_name = item.replace("(", "").replace(")", "").replace(",", "").replace("/", "_").replace(":", "_").replace(" ", "_").replace("-", "_")
        filename = f"economic_data/{base_name}_{safe_name}.csv"
        save(filename, item_rows)

if __name__ == "__main__":
    load_dotenv()
    key = os.getenv("ECOS_API_KEY")
    start, end = "202401", now_ym()
    os.makedirs("economic_data", exist_ok=True)
    
    # 단일 파일
    single_files = [
        ("base_rate.csv", "722Y001", "M", "0101000", None),
        ("cpi.csv", "901Y009", "M", "0", None),
        ("esi.csv", "513Y001", "M", None, ["경제심리지수(원계열)"]),
        ("ccsi.csv", "511Y002", "M", None, ["현재생활형편CSI"]),
        ("construction_bsi_actual.csv", "512Y007", "M", None, ["업황실적BSI 1)"]),
        ("construction_bsi_forecast.csv", "512Y008", "M", None, ["업황전망BSI 1)"]),
        ("housing_sale_price.csv", "901Y062", "M", None, ["총지수"]),
        ("housing_lease_price.csv", "901Y063", "M", None, ["총지수"]),
        ("leading_index.csv", "901Y067", "M", None, ["선행지수순환변동치"]),
    ]
    
    # M2 (전기대비 증가율)
    m2_files = [("m2_growth.csv", "101Y003", "M", None, ["M2(평잔, 계절조정계열)"])]
    
    # 개별 파일
    individual_files = [
        ("market_rate", "721Y001", "M", None, ["국고채(3년)", "국고채(10년)", "회사채(3년, AA-)", "회사채(3년, BBB-)"]),
        ("exchange_usd", "731Y006", "M", None, ["원/달러(종가 15:30)"]),
        ("ppi", "404Y014", "M", None, ["철강1차제품", "비금속광물"]),
        ("import_price", "401Y015", "M", None, ["철강1차제품", "비금속광물"]),
    ]
    
    # 데이터 수집
    for fname, stat, per, item, keys in single_files:
        rows = ecos(key, stat, per, start, end, item)
        rows = pick(rows, keys)
        save(f"economic_data/{fname}", rows)
    
    for fname, stat, per, item, keys in m2_files:
        rows = ecos(key, stat, per, start, end, item)
        rows = pick(rows, keys)
        if rows:
            growth_rows = calculate_growth_rate(rows)
            save(f"economic_data/{fname}", growth_rows)
    
    for base_name, stat, per, item, keys in individual_files:
        if stat in ["404Y014", "401Y015"]:  # PPI, 수입물가지수
            rows = collect_multiple_items(key, stat, per, start, end, keys)
        else:
            rows = ecos(key, stat, per, start, end, item)
            rows = pick(rows, keys)
        save_individual(base_name, rows)
    
    print("데이터 수집 완료!")
