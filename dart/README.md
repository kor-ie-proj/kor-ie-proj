# DART 재무데이터 수집

전자공시시스템(DART) API를 활용한 건설업 기업 재무제표 자동 수집 모듈

## 개요

건설업 10개 주요 기업의 분기별 재무제표를 DART API를 통해 수집하고 MySQL 데이터베이스에 저장합니다.

## 대상 기업 (10개사)

| 기업명 | 주식코드 | 특징 |
|--------|----------|------|
| 삼성물산 | 028260 | 대형 종합건설 |
| 효성중공업 | 298040 | 플랜트 전문 |
| 현대건설 | 000720 | 대형 종합건설 |
| HJ중공업 | 097230 | 중공업 건설 |
| DL이앤씨 | 375500 | 종합건설 |
| GS건설 | 006360 | 대형 종합건설 |
| 대우건설 | 047040 | 종합건설 |
| HDC현대산업개발 | 294870 | 도시개발 |
| 아이에스동서 | 010780 | 중견 건설 |
| 태영건설 | 009410 | 중견 건설 |

## 수집 데이터

### 재무상태표
- **자산총계**: 기업의 전체 자산 규모
- **부채총계**: 기업의 전체 부채 규모  
- **자본총계**: 기업의 순자산 (자산-부채)

### 손익계산서
- **매출액**: 분기별 매출액 (누적 → 분기 변환)
- **영업이익**: 분기별 영업이익 (누적 → 분기 변환)
- **분기순이익**: 분기별 당기순이익 (누적 → 분기 변환)

### 데이터 특징
- **기간**: 2015년 4분기 ~ 2025년 2분기
- **주기**: 분기별 (Q1, Q2, Q3, Q4)
- **형태**: 연결재무제표 우선, 별도재무제표 보완
- **단위**: 억원 (정규화 적용)

## 파일 구조

```
dart/
├── dart_data.ipynb           # 메인 수집 노트북
├── dart_out/                # 수집 결과 저장 폴더
│   ├── 건설10_11년로드_2015~2025_연결_분기재무_정규화.csv
│   ├── 건설10_11년로드_2015~2025_연결_분기재무_정규화.xlsx
│   └── 수기입력_dart_결측치.csv  # 결측치 보완 데이터
└── README.md                # 이 파일
```

## 사용법

### 1. 환경 설정

#### DART API 키 발급
1. [DART 사이트](https://opendart.fss.or.kr/) 접속
2. 회원가입 및 로그인
3. API 인증키 발급 신청
4. `.env` 파일에 API 키 설정

```env
DART_API_KEY=your_dart_api_key_here
```

#### 필요 패키지 설치
```bash
pip install dart-fss pandas tqdm tenacity openpyxl
```

### 2. 데이터 수집 실행

#### Jupyter Notebook 실행
```bash
jupyter notebook dart_data.ipynb
```

#### 셀별 실행 순서
1. **패키지 설치 및 Import** (셀 1-2)
2. **DART API 설정 및 데이터 수집** (셀 3)
3. **수기입력 데이터 병합** (셀 4)
4. **데이터 정규화 및 파일 저장** (셀 5)
5. **데이터베이스 저장** (셀 6-7)

### 3. 실행 결과

- **CSV/Excel 파일**: `dart_out/` 폴더에 저장
- **MySQL 저장**: `dart_data` 테이블에 저장
- **콘솔 출력**: 수집 진행상황 및 결과 통계

## 주요 기능

### 지능형 데이터 수집
- **앵커링 시스템**: 주식코드 기반 정확한 기업 식별
- **연결재무제표 우선**: CFS → OFS 순서로 수집
- **라인리지 폴백**: 합병/분할 기업의 과거 데이터 보완

### 데이터 품질 관리
- **누적값 → 분기값 변환**: 손익계산서 정확한 분기 실적 계산
- **결측치 보완**: 수기입력 데이터로 API 누락분 보완
- **데이터 검증**: 수집된 데이터의 논리적 일관성 검증

### 자동 전처리
- **정규화**: 원 단위 → 억원 단위 변환
- **중복 제거**: 동일 기업-연도-분기 데이터 중복 방지
- **형식 통일**: 날짜, 숫자 형식 표준화

## 데이터 구조

### 수집 데이터 형식
```csv
corp_name,corp_code,year,quarter,report_date,자산총계,부채총계,자본총계,매출액,영업이익,분기순이익
삼성물산,00126434,2024,Q1,2024-03-31,125430.50,67890.25,57540.25,18750.30,1250.75,980.45
```

### MySQL 테이블 구조
```sql
CREATE TABLE dart_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    corp_name VARCHAR(100) NOT NULL,
    corp_code VARCHAR(20) NOT NULL,
    year INT NOT NULL,
    quarter VARCHAR(10) NOT NULL,
    report_date DATE,
    total_assets DECIMAL(20,2),      -- 자산총계 (억원)
    total_liabilities DECIMAL(20,2), -- 부채총계 (억원)
    total_equity DECIMAL(20,2),      -- 자본총계 (억원)
    revenue DECIMAL(20,2),           -- 매출액 (억원)
    operating_profit DECIMAL(20,2),  -- 영업이익 (억원)
    quarterly_profit DECIMAL(20,2),  -- 분기순이익 (억원)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_corp_year_quarter (corp_code, year, quarter)
);
```

## 수집 로직

### 1. 기업 식별 및 앵커링
```python
# 주식코드 기반 정확한 corp_code 매핑
PRIMARY_STOCK_ANCHOR = {
    "삼성물산": "028260",    # 합병 후 신주
    "태영건설": "009410"
}

# 과거 기업명 매핑 (라인리지)
LINEAGE_RULES = {
    "DL이앤씨": ("대림산업", 2020),         # 2020년까지 대림산업 데이터
    "HDC현대산업개발": ("현대산업개발", 2017) # 2017년까지 현대산업개발 데이터
}
```

### 2. 재무제표 수집 전략
```python
# 연결재무제표(CFS) 우선, 별도재무제표(OFS) 보완
def _probe_fs_div_for_year(corp_code, year):
    # 연도별로 CFS 가용성 확인
    # CFS 있으면 CFS, 없으면 OFS 사용
```

### 3. 누적값 → 분기값 변환
```python
# 손익계산서: 누적값을 분기값으로 변환
Q2_매출액 = H1_매출액 - Q1_매출액
Q3_매출액 = 3Q_매출액 - H1_매출액  
Q4_매출액 = Annual_매출액 - 3Q_매출액

# 재무상태표: 분기말 잔액 그대로 사용
```

## 모니터링

### 수집 상태 확인
```python
# 노트북 내 확인 함수
check_database_results()

# 출력 내용:
# - 총 저장된 레코드 수
# - 기업별 레코드 수
# - 연도별 레코드 수  
# - 최근 데이터 샘플
```

### 데이터 품질 검증
```python
# 결측치 현황
missing_info = result_df.isnull().sum()

# 기업별 데이터 완성도
corp_data_count = result_df['corp_name'].value_counts()

# 연도별 데이터 분포
year_distribution = result_df.groupby(['year', 'quarter']).size()
```

## 주의사항

### 데이터 특성
- **보고 지연**: 분기 종료 후 45일 이내 공시
- **정정 공시**: 기발표 재무제표 수정 가능
- **비교 불가**: 회계기준 변경에 따른 비교 제약

### 결측치 원인
- **신규 상장**: 2015년 이후 상장 기업
- **감사 지연**: 감사보고서 제출 지연
- **영업 중단**: 일시적 영업 중단 기간
- **합병/분할**: 기업 구조조정

## 업데이트 주기

### 권장 실행 주기
- **분기별 수집**: 분기 종료 후 2개월 경과 시점
- **월별 확인**: 정정공시 반영을 위한 월별 확인
- **연말 백업**: 연말 전체 데이터 백업

### 실행 시점
```
Q1 (1-3월) 데이터: 5월 중순 수집
Q2 (4-6월) 데이터: 8월 중순 수집  
Q3 (7-9월) 데이터: 11월 중순 수집
Q4 (10-12월) 데이터: 3월 중순 수집
```

## 문제 해결

### 일반적인 오류
```python
# 1. API 키 오류
RuntimeError: DART_API_KEY 환경변수가 설정되지 않았습니다.
→ .env 파일의 DART_API_KEY 확인

# 2. 네트워크 오류  
requests.exceptions.ConnectionError
→ 인터넷 연결 및 방화벽 확인

# 3. 데이터베이스 연결 오류
pymysql.err.OperationalError
→ MySQL 서비스 실행 및 연결 정보 확인

# 4. 메모리 오류
MemoryError
→ 수집 기간 단축 또는 배치 크기 조정
```

### 데이터 검증
```python
# 논리적 일관성 확인
assert (result_df['자산총계'] >= result_df['부채총계']).all()
assert (result_df['자산총계'] == result_df['부채총계'] + result_df['자본총계']).all()

# 이상치 탐지
Q1 = result_df['매출액'].quantile(0.25)
Q3 = result_df['매출액'].quantile(0.75)
IQR = Q3 - Q1
outliers = result_df[(result_df['매출액'] < Q1-1.5*IQR) | 
                    (result_df['매출액'] > Q3+1.5*IQR)]
```


