import os, csv, requests, time
from datetime import datetime
from dotenv import load_dotenv
import sys
import pandas as pd

# DB 연결을 위한 경로 추가 및 import
try:
    from db_query import DatabaseConnection
except ImportError:
    # 상위 디렉토리의 DB 폴더에서 db_query 모듈 찾기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    db_path = os.path.join(parent_dir, 'DB')
    if db_path not in sys.path:
        sys.path.insert(0, db_path)
    try:
        from db_query import DatabaseConnection
    except ImportError:
        print("데이터베이스 모듈을 찾을 수 없습니다.")
        DatabaseConnection = None

BASE = "https://ecos.bok.or.kr/api"

def now_ym(): 
    return datetime.now().strftime("%Y%m")

def ecos(key, stat, period, start, end, item=None):
    # 큰 기간을 여러 번에 나누어 호출 (1년씩)
    all_rows = []
    
    start_year = int(start[:4])
    start_month = int(start[4:])
    end_year = int(end[:4])
    end_month = int(end[4:])
    
    # 1년씩 나누어서 호출
    for year in range(start_year, end_year + 1):
        # 시작월과 끝월 계산
        if year == start_year:
            chunk_start = start
        else:
            chunk_start = f"{year}01"
            
        if year == end_year:
            chunk_end = end
        else:
            chunk_end = f"{year}12"
        
        url = f"{BASE}/StatisticSearch/{key}/json/kr/1/10000/{stat}/{period}/{chunk_start}/{chunk_end}/"
        if item: url += f"{item}/"
        
        print(f"API 호출: {chunk_start} ~ {chunk_end}")
        
        # 재시도 로직
        max_retries = 3
        for attempt in range(max_retries):
            try:
                time.sleep(2)  # 2초 대기
                r = requests.get(url, timeout=30)
                r.raise_for_status()  # HTTP 오류 체크
                
                j = r.json()
                if "StatisticSearch" in j and "row" in j["StatisticSearch"]:
                    rows = j["StatisticSearch"]["row"]
                    all_rows.extend(rows)
                    print(f"  성공: {len(rows)}개 행 수집")
                    break
                elif "RESULT" in j and j["RESULT"]["CODE"] != "INFO-000":
                    print(f"  API 오류: {j['RESULT']['MESSAGE']}")
                    break
                else:
                    print(f"  데이터 없음")
                    break
                    
            except requests.exceptions.RequestException as e:
                print(f"  시도 {attempt + 1} 실패: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # 실패시 5초 대기 후 재시도
                else:
                    print(f"  최종 실패: {chunk_start} ~ {chunk_end}")
            except Exception as e:
                print(f"  예상치 못한 오류: {e}")
                break
    
    print(f"총 수집된 행 수: {len(all_rows)}")
    return all_rows

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
        print(f"  {item_name}: {len(matching_rows)}개 행")
    
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

def create_merged_csv(all_data):
    """모든 수집된 데이터를 하나의 통합 CSV 파일로 저장 (DB와 별개)"""
    print("\n=== Merged CSV 파일 생성 시작 ===")
    
    try:
        # 모든 데이터를 날짜별로 통합
        merged_data = {}
        
        for file_info in all_data:
            file_name = file_info['file_name'].replace('.csv', '')
            rows = file_info['data']
            
            for row in rows:
                date = row.get('TIME')
                item_name = row.get('ITEM_NAME1', '')
                value_str = row.get('DATA_VALUE', '')
                unit = row.get('UNIT_NAME', '')
                stat_name = row.get('STAT_NAME', '')
                
                if date not in merged_data:
                    merged_data[date] = {}
                
                # 컬럼명 생성 (파일명_항목명 형태)
                if file_name.startswith('market_rate_'):
                    column_name = f"{item_name}"
                elif file_name.startswith('exchange_'):
                    column_name = f"{item_name}"
                elif file_name.startswith('import_price_'):
                    column_name = f"{item_name}_import_price"
                elif file_name.startswith('ppi_'):
                    column_name = f"{item_name}_ppi"
                elif item_name:
                    column_name = f"{item_name}"
                else:
                    column_name = file_name
                
                try:
                    value = float(value_str) if value_str else None
                except:
                    value = None
                
                merged_data[date][column_name] = value
        
        # DataFrame으로 변환
        df = pd.DataFrame.from_dict(merged_data, orient='index')
        df.index.name = 'date'
        df = df.sort_index()
        
        # merged CSV 파일 저장 경로
        current_dir = os.path.dirname(os.path.abspath(__file__))
        merged_file_path = os.path.join(current_dir, "economic_data_merged.csv")
        
        # CSV 파일로 저장
        df.to_csv(merged_file_path, encoding='utf-8-sig')
        
        print(f"   Merged CSV 파일 저장 완료: {merged_file_path}")
        print(f"   - 데이터 기간: {df.index.min()} ~ {df.index.max()}")
        print(f"   - 총 행 수: {len(df)}")
        print(f"   - 총 컬럼 수: {len(df.columns)}")
        
        # 컬럼 목록 출력 (처음 10개만)
        print(f"   - 주요 컬럼: {list(df.columns)[:10]}...")
        
        return True
        
    except Exception as e:
        print(f" Merged CSV 파일 생성 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_to_database(all_data):
    """수집된 모든 데이터를 MySQL 데이터베이스에 저장 (스키마별 컬럼 매핑)"""
    if DatabaseConnection is None:
        print("데이터베이스 모듈을 사용할 수 없습니다. CSV 파일로만 저장합니다.")
        return False
        
    try:
        db = DatabaseConnection()
        if not db.connect():
            print("데이터베이스 연결 실패 - CSV 파일로만 저장합니다.")
            return False
        
        # 기존 데이터 삭제 (새로운 데이터로 완전 교체)
        delete_query = "DELETE FROM ecos_data"
        cursor = db.connection.cursor()
        cursor.execute(delete_query)
        print("기존 ECOS 데이터 삭제 완료")
        
        # 항목명 → 컬럼명 매핑 (DDL의 컬럼명 일치)
        item_to_column = {
            '기준금리': 'base_rate',
            '현재생활형편CSI': 'ccsi', 
            '업황실적BSI 1)': 'construction_bsi_actual',
            '업황전망BSI 1)': 'construction_bsi_forecast',
            '소비자물가지수': 'cpi',
            '경제심리지수(원계열)': 'esi',
            '원/달러(종가 15:30)': 'exchange_usd_krw_close',
            '총지수_housing_lease_price': 'housing_lease_price',
            '총지수_housing_sale_price': 'housing_sale_price', 
            '비금속광물_import': 'import_price_non_metal_mineral',
            '철강1차제품_import': 'import_price_steel_primary',
            '선행지수순환변동치': 'leading_index',
            'M2(평잔, 계절조정계열)': 'm2_growth',
            '국고채(10년)': 'market_rate_treasury_bond_10yr',
            '국고채(3년)': 'market_rate_treasury_bond_3yr',
            '회사채(3년, AA-)': 'market_rate_corporate_bond_3yr_AA',
            '회사채(3년, BBB-)': 'market_rate_corporate_bond_3yr_BBB',
            '비금속광물_ppi': 'ppi_non_metal_mineral',
            '철강1차제품_ppi': 'ppi_steel_primary'
        }
        
        # 파일명 → 항목명 매핑 (단일 파일들)
        file_to_item = {
            'base_rate': '기준금리',
            'cpi': '소비자물가지수', 
            'esi': '경제심리지수(원계열)',
            'ccsi': '현재생활형편CSI',
            'construction_bsi_actual': '업황실적BSI 1)',
            'construction_bsi_forecast': '업황전망BSI 1)',
            'housing_sale_price': '총지수',
            'housing_lease_price': '총지수',
            'leading_index': '선행지수순환변동치',
            'm2_growth': 'M2(평잔, 계절조정계열)'
        }
        
        print("=== 데이터 매핑 시작 ===")
        
        # 날짜별로 데이터 그룹화
        date_data = {}
        for file_info in all_data:
            file_name = file_info['file_name'].replace('.csv', '')
            rows = file_info['data']
            
            print(f"\n🔄 {file_name} 처리 중... ({len(rows)}개 행)")
            
            for row in rows:
                date = row.get('TIME')
                item_name = row.get('ITEM_NAME1', '')
                value_str = row.get('DATA_VALUE', '')
                
                # 매핑할 항목명 결정
                if file_name in file_to_item:
                    # 단일 파일의 경우
                    if file_name.startswith('housing_'):
                        # 주택가격지수는 특별 처리
                        item_key = f"총지수_{file_name}"
                    else:
                        item_key = file_to_item[file_name]
                elif file_name.startswith('market_rate_'):
                    # 금리 파일
                    item_key = item_name
                elif file_name.startswith('exchange_'):
                    # 환율 파일
                    item_key = item_name
                elif file_name.startswith('import_price_'):
                    # 수입물가지수
                    if item_name in ['비금속광물', '철강1차제품']:
                        item_key = f"{item_name}_import"
                    else:
                        item_key = item_name
                elif file_name.startswith('ppi_'):
                    # 생산자물가지수
                    if item_name in ['비금속광물', '철강1차제품']:
                        item_key = f"{item_name}_ppi"
                    else:
                        item_key = item_name
                else:
                    item_key = item_name
                
                if date not in date_data:
                    date_data[date] = {}
                
                try:
                    value = float(value_str) if value_str else None
                except:
                    value = None
                    
                date_data[date][item_key] = value
                
                # 매핑 확인용 로그 (처음 몇 개만)
                if len(date_data) <= 3:
                    if item_key in item_to_column:
                        column_name = item_to_column[item_key]
                        print(f"{item_key} → {column_name}: {value}")
                    else:
                        print(f"매핑되지 않은 항목: {item_key}")
        
        print(f"\n총 {len(date_data)}개 날짜의 데이터 준비 완료")
        
        # 실제 저장될 데이터 샘플 확인
        print("\n=== 저장될 데이터 샘플 ===")
        sample_dates = list(date_data.keys())[:3]
        for date in sample_dates:
            print(f"날짜 {date}:")
            for item_key, value in date_data[date].items():
                if item_key in item_to_column:
                    print(f"  {item_key} = {value}")
        
        # MySQL 스키마에 맞춰 배치 삽입 (서버 부하 방지)
        insert_query = """
        INSERT INTO ecos_data (
            date, base_rate, ccsi, construction_bsi_actual, construction_bsi_forecast,
            cpi, esi, exchange_usd_krw_close, housing_lease_price, housing_sale_price,
            import_price_non_metal_mineral, import_price_steel_primary, leading_index, m2_growth,
            market_rate_treasury_bond_10yr, market_rate_treasury_bond_3yr, market_rate_corporate_bond_3yr_AA, market_rate_corporate_bond_3yr_BBB,
            ppi_non_metal_mineral, ppi_steel_primary
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data_tuples = []
        for date, values in date_data.items():
            row_data = [date]
            for item_key, column_name in item_to_column.items():
                row_data.append(values.get(item_key, None))
            data_tuples.append(tuple(row_data))
        
        print(f"\n=== 데이터베이스 저장 시작 ({len(data_tuples)}개 행) ===")
        
        # 배치 크기 설정 (서버 부하 방지)
        batch_size = 10  # 한 번에 10개씩 저장
        total_batches = (len(data_tuples) + batch_size - 1) // batch_size
        
        import time
        
        for i in range(0, len(data_tuples), batch_size):
            batch = data_tuples[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f" 배치 {batch_num}/{total_batches} 저장 중... ({len(batch)}개 행)")
            
            cursor.executemany(insert_query, batch)
            db.connection.commit()
            
            print(f" 배치 {batch_num} 저장 완료")
            
            # 서버 부하 방지를 위한 대기 시간 (마지막 배치가 아닌 경우만)
            if i + batch_size < len(data_tuples):
                time.sleep(3)
        
        print(f"데이터베이스에 총 {len(data_tuples)}개 행 배치 저장 완료")
        
        cursor.close()
        db.disconnect()
        return True
        
    except Exception as e:
        print(f"데이터베이스 저장 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.disconnect()
        return False
        
        data_tuples = []
        for date, values in date_data.items():
            row_data = [date]
            for item_key, column_name in item_to_column.items():
                row_data.append(values.get(item_key, None))
            data_tuples.append(tuple(row_data))
        
        cursor.executemany(insert_query, data_tuples)
        db.connection.commit()
        
        print(f"데이터베이스에 {len(data_tuples)}개 행 저장 완료")
        
        cursor.close()
        db.disconnect()
        return True
        
    except Exception as e:
        print(f"데이터베이스 저장 중 오류 발생: {e}")
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.disconnect()
        return False

def save(path, rows):
    if not rows: 
        print(f"  경고: {path} - 저장할 데이터가 없습니다")
        return []
    
    # 중복 제거
    seen = set()
    unique_rows = []
    for r in rows:
        key = f"{r['TIME']}_{r.get('ITEM_NAME1', '')}"
        if key not in seen:
            seen.add(key)
            unique_rows.append(r)
    
    rows = sorted(unique_rows, key=lambda x: x["TIME"])
    
    # CSV 파일 저장 (백업용)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["date","value","unit","stat_name","item_name"])
        for r in rows:
            w.writerow([r.get("TIME"), r.get("DATA_VALUE"), r.get("UNIT_NAME"), r.get("STAT_NAME"), r.get("ITEM_NAME1")])
    
    print(f"  CSV 저장 완료: {path} ({len(rows)}개 행)")
    return rows

def save_individual(base_name, rows):
    """개별 파일로 저장"""
    if not rows: return []
    
    items = {}
    for r in rows:
        item = r.get("ITEM_NAME1", "")
        if item:
            if item not in items: items[item] = []
            items[item].append(r)
    
    all_saved_rows = []
    for item, item_rows in items.items():
        safe_name = item.replace("(", "").replace(")", "").replace(",", "").replace("/", "_").replace(":", "_").replace(" ", "_").replace("-", "_")
        # 현재 ecos 폴더 안의 economic_data 폴더 사용
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(current_dir, "economic_data", f"{base_name}_{safe_name}.csv")
        saved_rows = save(filename, item_rows)
        all_saved_rows.extend(saved_rows)
    
    return all_saved_rows

if __name__ == "__main__":
    load_dotenv()
    key = os.getenv("ECOS_API_KEY")
    start, end = "201510", now_ym()
    
    # ecos 폴더 안에 economic_data 폴더 생성
    current_dir = os.path.dirname(os.path.abspath(__file__))
    economic_data_dir = os.path.join(current_dir, "economic_data")
    os.makedirs(economic_data_dir, exist_ok=True)
    
    # 모든 수집된 데이터를 저장할 리스트
    all_collected_data = []
    
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
    
    # 데이터 수집 (서버 부하 방지를 위한 지연 시간 포함)
    import time
    
    print("=== API 데이터 수집 시작 ===")
    
    for i, (fname, stat, per, item, keys) in enumerate(single_files):
        print(f"\n=== {fname} 수집 중 ({i+1}/{len(single_files)}) ===")
        rows = ecos(key, stat, per, start, end, item)
        rows = pick(rows, keys)
        # ecos 폴더 안의 economic_data 폴더에 저장
        file_path = os.path.join(economic_data_dir, fname)
        saved_rows = save(file_path, rows)
        all_collected_data.append({"file_name": fname, "data": saved_rows})
        print(f"{fname} 완료: {len(rows)}개 행 저장")
        
        # API 서버 부하 방지를 위한 대기 시간
        if i < len(single_files) - 1:  # 마지막이 아닌 경우만
            time.sleep(1)
    
    for i, (fname, stat, per, item, keys) in enumerate(m2_files):
        print(f"\n=== {fname} 수집 중 (성장률 계산) ({i+1}/{len(m2_files)}) ===")
        rows = ecos(key, stat, per, start, end, item)
        rows = pick(rows, keys)
        if rows:
            growth_rows = calculate_growth_rate(rows)
            # ecos 폴더 안의 economic_data 폴더에 저장
            file_path = os.path.join(economic_data_dir, fname)
            saved_rows = save(file_path, growth_rows)
            all_collected_data.append({"file_name": fname, "data": saved_rows})
            print(f"{fname} 완료: {len(growth_rows)}개 행 저장")
        else:
            print(f"{fname} 실패: 데이터 없음")
        
        # API 서버 부하 방지를 위한 대기 시간
        if i < len(m2_files) - 1:
            time.sleep(1)
    
    for i, (base_name, stat, per, item, keys) in enumerate(individual_files):
        print(f"\n=== {base_name} 개별 파일 수집 중 ({i+1}/{len(individual_files)}) ===")
        rows = ecos(key, stat, per, start, end, item)
        rows = pick(rows, keys)
        saved_rows = save_individual(base_name, rows)
        all_collected_data.append({"file_name": f"{base_name}_files", "data": saved_rows})
        print(f"{base_name} 완료: {len(saved_rows)}개 행 저장")
        
        # API 서버 부하 방지를 위한 대기 시간
        if i < len(individual_files) - 1:
            time.sleep(1)
        print(f"\n=== {base_name} 수집 중 (개별 파일) ===")
        if stat in ["404Y014", "401Y015"]:  # PPI, 수입물가지수
            rows = collect_multiple_items(key, stat, per, start, end, keys)
        else:
            rows = ecos(key, stat, per, start, end, item)
            rows = pick(rows, keys)
        saved_rows = save_individual(base_name, rows)
        all_collected_data.append({"file_name": f"{base_name}.csv", "data": saved_rows})
        print(f"{base_name} 완료: {len(rows)}개 행 처리")
    
    print("\n=== 데이터베이스 저장 시작 ===")
    
    # 데이터베이스에 저장
    if save_to_database(all_collected_data):
        print("데이터베이스 저장 완료!")
    else:
        print("데이터베이스 저장 실패 - CSV 파일만 사용")
    

    print("\n=== Merged CSV 파일 생성 시작 ===")
    
    # 통합 CSV 파일 생성 (DB와 별개)
    if create_merged_csv(all_collected_data):
        print("Merged CSV 파일 생성 완료!")
    else:
        print("Merged CSV 파일 생성 실패")
    
    print("\n=== 모든 작업 완료 ===")
    print("데이터 수집 완료!")
