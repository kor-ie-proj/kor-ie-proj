import os, csv, requests
from datetime import datetime
from dotenv import load_dotenv

BASE = "https://ecos.bok.or.kr/api"

def now_ym(): return datetime.now().strftime("%Y%m")

def ecos(key, stat, period, start, end, item=None, max_retries=3):
    url = f"{BASE}/StatisticSearch/{key}/json/kr/1/10000/{stat}/{period}/{start}/{end}/"
    if item: url += f"{item}/"
    
    for attempt in range(max_retries):
        try:
            r = requests.get(url, timeout=30)  # 타임아웃을 30초로 증가
            r.raise_for_status()
            j = r.json()
            
            if "StatisticSearch" in j and "row" in j["StatisticSearch"]:
                return j["StatisticSearch"]["row"]
            else:
                print(f"Warning: No data found for {stat} - {url}")
                return []
        except requests.exceptions.Timeout as e:
            if attempt < max_retries - 1:
                print(f"Timeout for {stat}, retrying... ({attempt + 1}/{max_retries})")
                continue
            else:
                print(f"Error: Timeout after {max_retries} attempts for {stat}: {e}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {stat}: {e}")
            return []
        except ValueError as e:
            print(f"Error parsing JSON for {stat}: {e}")
            return []

def pick(rows, keys):
    if not keys: return rows
    result = []
    for r in rows:
        item_name = r.get("ITEM_NAME1") or ""
        # 정확한 품목명 매칭
        if any(item_name == k for k in keys):
            result.append(r)
    return result

def collect_multiple_items(key, stat, period, start, end, item_names):
    """여러 품목을 수집하여 하나의 리스트로 반환"""
    all_rows = []
    
    # 전체 데이터를 가져와서 필터링
    rows = ecos(key, stat, period, start, end, None)
    
    for item_name in item_names:
        matching_rows = [r for r in rows if r.get("ITEM_NAME1") == item_name]
        all_rows.extend(matching_rows)
        if matching_rows:
            print(f"    - {item_name}: {len(matching_rows)}개 데이터")
    
    return all_rows

def dedup(rows):
    d = {}
    for r in rows: 
        key = f"{r['TIME']}_{r.get('ITEM_NAME1', '')}"
        d[key] = r
    return list(d.values())

def save(path, rows):
    rows = dedup(sorted(rows, key=lambda x: (x["TIME"], x.get("ITEM_NAME1", ""))))
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["date","value","unit","stat_name","item_name"])
        for r in rows:
            w.writerow([r.get("TIME"), r.get("DATA_VALUE"), r.get("UNIT_NAME"), r.get("STAT_NAME"), r.get("ITEM_NAME1")])

if __name__ == "__main__":
    load_dotenv()
    key = os.getenv("ECOS_API_KEY")
    
    if not key or key == "YOUR_API_KEY_HERE":
        print("Error: ECOS_API_KEY가 설정되지 않았습니다.")
        print("1. .env 파일을 열어서 ECOS_API_KEY를 설정하세요.")
        print("2. 한국은행 ECOS API 사이트(https://ecos.bok.or.kr/)에서 API 키를 발급받으세요.")
        exit(1)
    
    start, end = "202401", now_ym()
    os.makedirs("economic_data", exist_ok=True)
    
    print(f"데이터 수집 기간: {start} ~ {end}")
    print("=" * 50)

    cfg = [
        # 1) 한국은행 기준금리
        ("base_rate.csv", "722Y001", "M", "0101000", None),
        
        # 2) 시장금리 - 국고채 3년/10년 금리 & 회사채 금리 (AA-, BBB-)
        ("market_interest_rate.csv", "721Y001", "M", None, ["국고채(3년)", "국고채(10년)", "회사채(3년,AA-)", "회사채(3년,BBB-)"]),
        
        # 3) 환율 - 원/달러
        ("exchange_rate_usd.csv", "731Y006", "M", None, ["원/달러(종가 15:30)","원/달러(종가)","원/달러(종가 02:00)"]),
        
        # 4) 소비자물가지수
        ("cpi.csv", "901Y009", "M", "0", None),
        
        # 5) 생산자물가지수 - 특정 품목들 (6개 품목 모두)
        ("ppi_specific.csv", "404Y014", "M", None, ["비금속광물", "목재및목제품", "기타비금속광물제품", "철강1차제품", "금속가공제품", "전선및케이블"]),
        
        # 6) 수입물가지수 - 총지수로 대체 (개별 품목 데이터 없음)
        ("import_price_index.csv", "401Y015", "M", None, ["총지수"]),
        
        # 7) M2 증가율 (올바른 통계코드와 계정항목)
        ("m2_growth_rate.csv", "101Y014", "M", None, ["M2(광의통화)"]),
        
        # 8) 경제심리지수(ESI)
        ("esi.csv", "513Y001", "M", "10000", None),
        
        # 9) 소비자심리지수(CCSI)
        ("ccsi.csv", "511Y002", "M", "99988", None),
        
        # 10) 건설업BSI 실적 (올바른 통계코드 사용)
        ("construction_bsi_actual.csv", "512Y007", "M", "4100", None),
        
        # 11) 건설업BSI 전망 (올바른 통계코드 사용)
        ("construction_bsi_forecast.csv", "512Y008", "M", "4100", None),
        
        # 12) 선행지수 순환변동치
        ("leading_index.csv", "901Y067", "M", None, ["선행지수순환변동치"]),
        
        # 13) 주택매매가격지수(KB) (올바른 계정항목)
        ("housing_sale_price.csv", "901Y062", "M", "99999", None),
        
        # 14) 주택전세가격지수(KB) (올바른 계정항목)
        ("housing_lease_price.csv", "901Y063", "M", "99999", None),
    ]

    for fname, stat, per, item, keys in cfg:
        print(f"수집 중: {fname} (통계코드: {stat})")
        
        # 생산자물가지수와 수입물가지수는 특별 처리
        if stat == "404Y014" and keys:  # 생산자물가지수 6개 품목
            rows = collect_multiple_items(key, stat, per, start, end, keys)
        elif stat == "401Y015" and keys:  # 수입물가지수 
            rows = collect_multiple_items(key, stat, per, start, end, keys)
        else:
            rows = ecos(key, stat, per, start, end, item)
            rows = pick(rows, keys)
        
        if rows:
            save(os.path.join("economic_data", fname), rows)
            print(f"✓ 저장 완료: {len(rows)}개 데이터")
        else:
            print(f"✗ 데이터 없음")
        print("-" * 30)
    
    print("데이터 수집 완료!")
