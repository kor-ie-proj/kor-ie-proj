# ECOS 경제지표 데이터 수집

한국은행 경제통계시스템(ECOS) API를 활용한 거시경제 지표 자동 수집 모듈

## 프로젝트 개요

건설업 경기 예측을 위한 핵심 거시경제 지표를 ECOS API를 통해 2010년 1월부터 현재까지 월별로 수집하여 MySQL 데이터베이스 및 CSV 파일로 저장하는 시스템입니다.

### 주요 특징
- 수집 기간: 2010년 1월부터 현재까지 (15년간 월별 데이터)
- 데이터 형식: 월별 시계열 데이터
- 저장 방식: MySQL 데이터베이스 + CSV 백업
- API 최적화: 1년 단위 분할 요청으로 안정성 확보

## 수집 지표 목록

### 1. 금융/통화 지표
- 기준금리 (722Y001)
- 국고채 금리 3년/10년 (721Y001)
- 회사채 금리 3년 AA-/BBB- (721Y001)
- M2 통화량 증가율 (101Y003)

### 2. 물가 지표
- 소비자물가지수 CPI (901Y009)
- 생산자물가지수 PPI - 비금속광물/철강1차제품 (404Y014)
- 수입물가지수 - 비금속광물/철강1차제품 (401Y015)

### 3. 건설/부동산 지표
- 건설업 BSI 실적/전망 (512Y007, 512Y008)
- 주택매매가격지수 (901Y062)
- 주택전세가격지수 (901Y063)

### 4. 경기/심리 지표
- 경기선행지수 (901Y067)
- 경제심리지수 ESI (513Y001)
- 소비자신뢰지수 CCSI (511Y002)
- 원/달러 환율 (731Y006)

## 파일 구조

```
ecos/
├── ECOS_data.py                 # 메인 수집 스크립트
├── economic_data_merged.csv     # 통합 경제 데이터
├── economic_data/               # 개별 지표 CSV 파일
│   ├── base_rate.csv           # 기준금리
│   ├── cpi.csv                 # 소비자물가지수
│   ├── construction_bsi_actual.csv  # 건설업 실적 BSI
│   ├── housing_sale_price.csv  # 주택매매가격지수
│   ├── market_rate_*.csv       # 각종 시장금리
│   └── ...                     # 기타 경제지표 파일들
└── README.md                   # 문서
```

## 설치 및 실행

### 1. 환경 설정

#### 필수 패키지 설치
```bash
pip install requests pandas mysql-connector-python python-dotenv
```

#### ECOS API 키 설정
1. [ECOS 사이트](https://ecos.bok.or.kr/) 접속 후 회원가입
2. API 인증키 발급 신청
3. 프로젝트 루트에 `.env` 파일 생성

```env
ECOS_API_KEY=your_ecos_api_key_here
```

### 2. 데이터 수집 실행

```bash
cd ecos
python ECOS_data.py
```

### 3. 실행 결과

- **콘솔 출력**: 수집 진행 상황 및 결과 로그
- **MySQL 저장**: `ecos_data` 테이블에 정규화된 데이터 저장
- **CSV 백업**: `economic_data/` 폴더에 개별 지표별 파일 저장
- **통합 파일**: `economic_data_merged.csv` 파일로 모든 지표 통합

## 시스템 구조

### 데이터 처리 흐름
1. **API 호출**: ECOS API에서 1년 단위로 데이터 수집
2. **데이터 정제**: 중복 제거, 날짜 형식 통일, 타입 변환
3. **이중 저장**:
   - MySQL 데이터베이스: 정규화된 구조로 저장
   - CSV 파일: 백업 및 분석용 원본 데이터

### 핵심 기능

#### API 호출 최적화
- 1년 단위 분할 요청으로 대용량 데이터 안정적 수집
- 재시도 로직 (최대 3회)
- 서버 부하 방지를 위한 요청 간격 조절 (2초)

#### 데이터 품질 관리
- 중복 데이터 자동 제거
- 결측치 처리
- 데이터 타입 검증 및 변환

#### 데이터베이스 연동
- 배치 삽입으로 성능 최적화
- 트랜잭션 처리로 데이터 일관성 보장
- 기존 데이터 완전 교체 방식

## 데이터베이스 스키마

### ecos_data 테이블 구조
```sql
CREATE TABLE ecos_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    base_rate DECIMAL(5,2),
    ccsi DECIMAL(8,2),
    construction_bsi_actual DECIMAL(5,1),
    construction_bsi_forecast DECIMAL(5,1),
    cpi DECIMAL(8,2),
    esi DECIMAL(8,2),
    exchange_usd_krw_close DECIMAL(8,2),
    housing_lease_price DECIMAL(8,2),
    housing_sale_price DECIMAL(8,2),
    import_price_non_metal_mineral DECIMAL(8,2),
    import_price_steel_primary DECIMAL(8,2),
    leading_index DECIMAL(8,2),
    m2_growth DECIMAL(8,4),
    market_rate_treasury_bond_10yr DECIMAL(5,2),
    market_rate_treasury_bond_3yr DECIMAL(5,2),
    market_rate_corporate_bond_3yr_AA DECIMAL(5,2),
    market_rate_corporate_bond_3yr_BBB DECIMAL(5,2),
    ppi_non_metal_mineral DECIMAL(8,2),
    ppi_steel_primary DECIMAL(8,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### CSV 파일 형식
```csv
date,value,unit,stat_name,item_name
202401,3.50,%,한국은행 기준금리,기준금리
202402,3.50,%,한국은행 기준금리,기준금리
```

## 설정 및 관리

### 수집 설정 변경
```python
# ECOS_data.py 내부 주요 설정값
start, end = "201001", now_ym()  # 수집 기간 설정
SLEEP_TIME = 2                   # API 호출 간격 (초)
RETRY_COUNT = 3                  # 실패시 재시도 횟수
BATCH_SIZE = 10                  # DB 배치 삽입 크기
```

### 데이터 검증 및 모니터링
```python
from db_query import DatabaseConnection

# 최신 데이터 확인
db = DatabaseConnection()
db.connect()
latest_data = db.get_ecos_data()
print(f"최신 데이터: {latest_data.tail()}")
print(f"총 데이터 개수: {len(latest_data)}")
```

### 자동화 설정
```bash
# crontab을 이용한 월별 자동 수집 (매월 5일 오전 9시)
0 9 5 * * cd /path/to/project/ecos && python ECOS_data.py
```

## 오류 해결

### 일반적인 문제 및 해결방법

1. **API 키 오류**
   - `.env` 파일의 `ECOS_API_KEY` 확인
   - ECOS 사이트에서 API 키 상태 확인

2. **네트워크 연결 오류**
   - 인터넷 연결 상태 확인
   - 방화벽 설정 확인

3. **데이터베이스 연결 오류**
   - MySQL 서버 상태 확인
   - 데이터베이스 접속 권한 확인
   - `db_query.py` 설정 확인

4. **디스크 용량 부족**
   - CSV 파일 저장 공간 확인
   - 오래된 백업 파일 정리

### 데이터 무결성 확인
```python
# 누락된 날짜 확인
import pandas as pd
df = pd.read_csv('economic_data_merged.csv')
date_range = pd.date_range(start='2010-01', end=pd.Timestamp.now(), freq='M')
missing_dates = date_range.difference(pd.to_datetime(df['date']))
print(f"누락된 날짜: {missing_dates}")
```

## 프로젝트 연계

### 데이터 활용 모듈
- `preprocessing/preprocessing.ipynb`: 수집 데이터 전처리 및 파생변수 생성
- `modeling/LSTM_predict_final.ipynb`: 경제지표 기반 예측 모델링
- `Heuristic/Heuristic.ipynb`: 휴리스틱 분석 모델

### 주요 파생변수
- 월별 변화율 (Month-over-Month): CPI, PPI 등의 전월 대비 변화율
- 금리 스프레드: 장단기 금리차, 신용 스프레드
- 이동평균: 주요 지표의 3개월, 6개월 이동평균
- 변동성 지표: 환율, 금리의 월별 변동성

