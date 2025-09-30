# DART 재무데이터 수집

전자공시시스템(DART) API를 활용한 건설업 기업 재무제표 자동 수집 시스템

## 프로젝트 개요

건설업 32개 기업의 분기별 재무제표를 DART API를 통해 체계적으로 수집하여 MySQL 데이터베이스 및 CSV 파일로 저장하는 시스템입니다.

### 주요 특징
- 수집 기간: 2015년 4분기부터 현재까지 (약 10년간 분기별 데이터)
- 대상 기업: 건설업 32개 상장기업 (그룹별 관리)
- 데이터 형식: 분기별 재무제표 (연결재무제표 우선)
- 저장 방식: MySQL 데이터베이스 + CSV/Excel 백업

## 수집 대상 기업
1. 삼성물산 (028260)
2. 효성중공업 (298040)
3. 현대건설 (000720)
4. HJ중공업 (097230)
5. DL이앤씨 (375500)
6. GS건설 (006360)
7. 대우건설 (047040)
8. HDC현대산업개발 (294870)
9. 아이에스동서 (010780)
10. 태영건설 (009410)
11. 서희건설 (035890)
12. 동원개발 (013120)
13. 코오롱글로벌 (003070)
14. 계룡건설 (013580)
15. 티케이케미칼 (104480)
16. 금호건설 (002990)
17. 이수화학 (005950)
18. 경동인베스트 (012320)
19. 자이에스앤디 (317400)
20. 동부건설 (005960)
21. 진흥기업 (002780)
22. KCC건설 (021320)
23. HS화성 (002460)
24. 서한 (011370)
25. HL D&I (014790)
26. 한신공영 (004960)
27. 남광토건 (001260)
28. 삼부토건 (001470)
29. 우원개발 (046940)
30. 대원 (007680)
31. 남화토건 (091590)
32. 신원종합개발 (017000)

## 수집 데이터 항목

### 재무상태표 (분기말 잔액)
- **자산총계**: 기업의 전체 자산 규모
- **부채총계**: 기업의 전체 부채 규모
- **자본총계**: 기업의 순자산 (자산-부채)

### 손익계산서 (분기별 실적)
- **매출액**: 분기별 순매출액 (누적값 → 분기값 변환)
- **영업이익**: 분기별 영업이익 (누적값 → 분기값 변환)
- **분기순이익**: 분기별 당기순이익 (누적값 → 분기값 변환)

### 데이터 특성
- **수집 기간**: 2015년 Q4부터 현재까지
- **업데이트 주기**: 분기별 (분기 종료 후 45일 이내)
- **재무제표 형태**: 연결재무제표(CFS) 우선, 별도재무제표(OFS) 보완
- **단위**: 억원 (원 단위에서 자동 변환)

## 파일 구조

```
dart/
├── dart_data.ipynb                    # 메인 수집 노트북
├── dart_out/                          # 수집 결과 저장 폴더
│   ├── 건설업1~10번_2015~2025_연결_분기재무_정규화.csv/.xlsx
│   ├── 건설업11~21번_2015~2025_연결_분기재무_정규화.csv/.xlsx
│   ├── 건설업22~32번_2015~2025_연결_분기재무_정규화.csv/.xlsx
│   ├── dart_merged_data.csv           # 전체 통합 데이터
│   ├── dart_결측치01.csv             # 수기 보완 데이터 1
│   ├── dart_결측치02.csv             # 수기 보완 데이터 2
│   └── dart_결측치03.csv             # 수기 보완 데이터 3
└── README.md                          # 문서
```
## 설치 및 실행

### 1. 환경 설정

#### 필수 패키지 설치
```bash
pip install dart-fss pandas tqdm tenacity openpyxl
```

#### DART API 키 설정
1. [DART 사이트](https://opendart.fss.or.kr/) 접속 후 회원가입
2. API 인증키 발급 신청
3. 프로젝트 루트에 `.env` 파일 생성

```env
DART_API_KEY=your_dart_api_key_here
```

### 2. 데이터 수집 실행

#### Jupyter Notebook 실행
```bash
cd dart
jupyter notebook dart_data.ipynb
```

#### 셀별 실행 순서
1. **패키지 설치 및 설정** (Cell 1-2): 라이브러리 설치 및 API 설정
2. **1~10번 기업 수집** (Cell 3): 주요 대형 건설사 데이터 수집
3. **11~21번 기업 수집** (Cell 4): 중견 건설사 데이터 수집
4. **22~32번 기업 수집** (Cell 5): 중소 건설사 데이터 수집
5. **수집 결과 요약** (Cell 6): 전체 수집 결과 확인
6. **수기 데이터 병합** (Cell 7): 결측치 보완 데이터 통합
7. **데이터베이스 저장** (Cell 8-9): MySQL 데이터베이스 저장

### 3. 실행 결과

- **그룹별 CSV/Excel 파일**: `dart_out/` 폴더에 저장
- **통합 CSV 파일**: `dart_merged_data.csv`로 저장
- **MySQL 저장**: `dart_data` 테이블에 증분 저장
- **실행 로그**: 콘솔에 수집 진행 상황 및 결과 통계 출력

## 시스템 구조

### 데이터 수집 프로세스
1. **기업 식별 앵커링**: 주식코드 기반 정확한 corp_code 매핑
2. **재무제표 형태 선택**: CFS(연결) 우선, OFS(별도) 보완
3. **분기별 데이터 수집**: 1Q/H1/3Q/Annual 보고서 개별 조회
4. **누적값 분기값 변환**: 손익계산서 누적값을 분기값으로 변환
5. **결측치 보완**: 수기 입력 데이터와 자동 병합

### 핵심 기능

#### 지능형 기업 식별 시스템
- **앵커링 매핑**: 주식코드 기반 정확한 기업 식별
- **라인리지 폴백**: 합병/분할 기업의 과거 데이터 연계
- **자동 업데이트**: 기업 정보 변경 시 자동 반영

#### 재무제표 수집 최적화
- **FS 형태 고정**: 연도별 CFS/OFS 중 하나로 통일
- **sj_div 필터링**: 재무상태표(BS), 손익계산서(IS/CIS) 구분
- **계정 매칭**: 다양한 계정명을 표준 계정으로 정규화

#### 데이터 품질 관리
- **중복 제거**: 동일 기업-연도-분기 데이터 중복 방지
- **논리적 검증**: 자산=부채+자본 등 재무제표 항등식 확인
- **이상치 탐지**: 전분기 대비 급격한 변화 감지

## 데이터베이스 스키마

### dart_data 테이블 구조
```sql
CREATE TABLE dart_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    corp_name VARCHAR(100) NOT NULL,        -- 기업명
    corp_code VARCHAR(20) NOT NULL,         -- DART 기업코드
    year INT NOT NULL,                      -- 연도
    quarter VARCHAR(10) NOT NULL,           -- 분기 (Q1, Q2, Q3, Q4)
    report_date DATE,                       -- 보고서 기준일
    total_assets DECIMAL(20,2),             -- 자산총계 (억원)
    total_liabilities DECIMAL(20,2),        -- 부채총계 (억원)
    total_equity DECIMAL(20,2),             -- 자본총계 (억원)
    revenue DECIMAL(20,2),                  -- 매출액 (억원)
    operating_profit DECIMAL(20,2),         -- 영업이익 (억원)
    quarterly_profit DECIMAL(20,2),         -- 분기순이익 (억원)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_corp_year_quarter (corp_code, year, quarter),
    UNIQUE KEY unique_record (corp_code, year, quarter)
);
```

### CSV 파일 형식
```csv
corp_name,corp_code,year,quarter,report_date,자산총계,부채총계,자본총계,매출액,영업이익,분기순이익
삼성물산,00126434,2024,Q1,2024-03-31,125430.50,67890.25,57540.25,18750.30,1250.75,980.45
현대건설,00164478,2024,Q1,2024-03-31,98765.40,54321.20,44444.20,12345.60,890.30,720.15
```

## 수집 로직 상세

### 1. 기업 식별 및 앵커링
```python
# 주식코드 기반 정확한 corp_code 매핑
PRIMARY_STOCK_ANCHOR = {
    "삼성물산": "028260",    # 합병 후 신주
    "태영건설": "009410"
}

# 라인리지 폴백 (합병/분할 기업 과거 데이터)
LINEAGE_RULES = {
    "DL이앤씨": ("대림산업", 2020),         # 2020년까지 대림산업 데이터
    "HDC현대산업개발": ("현대산업개발", 2017) # 2017년까지 현대산업개발 데이터
}
```

### 2. 재무제표 형태 선택 전략
```python
def _probe_fs_div_for_year(corp_code, year):
    # 연도별로 CFS(연결) 가용성 확인
    # CFS 있으면 해당 연도 전체를 CFS로 고정
    # 없으면 OFS(별도)로 고정하여 일관성 유지
```

### 3. 누적값 분기값 변환
```python
# 손익계산서: 누적값을 분기값으로 변환
sales_q = {
    "Q1": raw["1Q"]["매출액"],
    "Q2": raw["H1"]["매출액"] - raw["1Q"]["매출액"],
    "Q3": raw["3Q"]["매출액"] - raw["H1"]["매출액"],
    "Q4": raw["ANNUAL"]["매출액"] - raw["3Q"]["매출액"]
}

# 재무상태표: 분기말 잔액 그대로 사용
assets_q = {
    "Q1": raw["1Q"]["자산총계"],
    "Q2": raw["H1"]["자산총계"],
    "Q3": raw["3Q"]["자산총계"],
    "Q4": raw["ANNUAL"]["자산총계"]
}
```

### 4. 계정명 정규화
```python
TARGET_ACCOUNTS = {
    "자산총계": ["자산총계", "총자산"],
    "부채총계": ["부채총계", "총부채"],
    "자본총계": ["자본총계", "총자본", "자본총계(지배+비지배)"],
    "매출액": ["매출액", "매출", "매출수익", "영업수익", "수익"],
    "영업이익": ["영업이익", "영업손익"],
    "당기순이익": ["분기순이익", "당기순이익", "반기순이익"]
}
```

## 설정 및 관리

### 수집 기간 설정
```python
# 현재 월에 따른 자동 분기 판단
START_YEAR_LOAD = 2014  # 2014년부터 로드하여 2015년부터 사용
CURRENT_YEAR = datetime.now().year
CURRENT_MONTH = datetime.now().month

# 분기별 수집 범위 자동 설정
if CURRENT_MONTH <= 3:      # 1-3월이면 전년도 4분기까지
    END_YEAR = CURRENT_YEAR - 1
elif CURRENT_MONTH <= 6:    # 4-6월이면 올해 1분기까지
    END_YEAR = CURRENT_YEAR
    MAX_QUARTER = "Q1"
elif CURRENT_MONTH <= 9:    # 7-9월이면 올해 2분기까지
    END_YEAR = CURRENT_YEAR
    MAX_QUARTER = "Q2"
else:                       # 10-12월이면 올해 3분기까지
    END_YEAR = CURRENT_YEAR
    MAX_QUARTER = "Q3"
```

### API 호출 최적화
```python
SLEEP = 0.15  # API 호출 간격 (초)
REPRT = {
    "1Q": "11013",     # 1분기보고서
    "H1": "11012",     # 반기보고서
    "3Q": "11014",     # 3분기보고서
    "ANNUAL": "11011"  # 사업보고서
}
```

### 데이터 검증 및 모니터링
```python
# 수집 결과 확인
def check_database_results():
    # 총 레코드 수, 기업별/연도별 분포 확인
    # 최근 데이터 샘플 출력
    # 결측치 현황 리포트

# 결측치 현황 분석
missing_summary = (
    result_df.assign(_miss=result_df[NUM_COLS].isna().all(axis=1))
    .query("_miss == True")
    .groupby(["corp_name", "year"])
    .agg(missing_quarters=("quarter", "unique"))
)
```

## 오류 해결

### 일반적인 문제 및 해결방법

1. **API 키 오류**
   ```
   RuntimeError: DART_API_KEY 환경변수가 설정되지 않았습니다.
   ```
   - `.env` 파일의 `DART_API_KEY` 확인
   - DART 사이트에서 API 키 상태 확인

2. **기업 식별 오류**
   ```
   ValueError: stock_code 'XXXXXX' 회사를 찾지 못했습니다.
   ```
   - 주식코드 변경 또는 상장폐지 확인
   - 수동 corp_code 매핑 추가

3. **데이터베이스 연결 오류**
   ```
   데이터베이스 연결 실패 - CSV 파일로만 저장됩니다.
   ```
   - MySQL 서버 실행 상태 확인
   - `DB/.env` 파일의 연결 정보 확인

4. **메모리 부족**
   - 기업 그룹을 나누어서 개별 실행
   - 수집 기간 단축 (연도별 분할 수집)

### 데이터 품질 검증
```python
# 재무제표 항등식 검증
assert (result_df['자산총계'] >= result_df['부채총계']).all()
equity_calc = result_df['자산총계'] - result_df['부채총계']
equity_diff = abs(result_df['자본총계'] - equity_calc)
assert (equity_diff < 0.01).all()  # 소수점 오차 허용

# 이상치 탐지 (분기별 급격한 변화)
def detect_outliers(df, column, threshold=3):
    return df[abs(df[column].pct_change()) > threshold]
```

## 업데이트 주기 및 관리

### 권장 실행 주기
- **분기별 정기 수집**: 분기 종료 후 2개월 경과 시점
- **월별 보완 수집**: 정정공시 반영을 위한 추가 수집
- **연말 전체 백업**: 연말 전체 데이터 검증 및 백업

### 분기별 공시 일정
```
Q1 (1-3월) 실적: 5월 중순 이후 수집 권장
Q2 (4-6월) 실적: 8월 중순 이후 수집 권장
Q3 (7-9월) 실적: 11월 중순 이후 수집 권장
Q4 (10-12월) 실적: 3월 중순 이후 수집 권장
```

### 자동화 설정 (옵션)
```bash
# crontab을 이용한 분기별 자동 수집
# 매 분기 말 다음달 20일 오전 9시 실행
0 9 20 2,5,8,11 * cd /path/to/dart && jupyter nbconvert --execute dart_data.ipynb
```

## 프로젝트 연계

### 데이터 활용 모듈
- `preprocessing/preprocessing.ipynb`: 재무 데이터 전처리 및 파생변수 생성
- `Heuristic/Heuristic.ipynb`: DART 재무데이터와 경제지표 결합 분석
- `modeling/`: 재무지표 기반 기업 성과 예측 모델링

### 주요 파생지표
- **재무비율**: ROE, ROA, 부채비율, 유동비율 등
- **성장성 지표**: 매출액 증가율, 영업이익 증가율
- **안정성 지표**: 자기자본비율, 이자보상배수
- **수익성 지표**: 매출액순이익률, 자산회전율


