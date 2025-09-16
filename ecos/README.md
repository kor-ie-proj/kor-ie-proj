# 📊 ECOS 경제지표 데이터 수집

한국은행 경제통계시스템(ECOS) API를 활용한 거시경제 지표 자동 수집 모듈

## 📋 개요

건설업 경기 예측을 위한 핵심 거시경제 지표들을 ECOS API를 통해 **2010년 1월부터 월별**로 수집하고 MySQL 데이터베이스에 저장합니다.

### 🔄 최신 업데이트 (2024.09)
- **수집 기간**: 2010년 1월부터 현재까지 (기존 2015년 10월 → 2010년 1월)
- **데이터 처리**: 분기별 → **월별 처리**로 변경
- **날짜 형식**: YYYY-MM 형식으로 통일
- **파생변수**: 분기별 변수 제거, 월별 파생변수 추가

## 🔍 수집 지표

### 금융 지표
- **기준금리**: 한국은행 기준금리
- **시장금리**: 국고채 3년/10년, 회사채 3년 (AA-, BBB-)
- **통화량**: M2 증가율

### 물가 지표  
- **소비자물가지수(CPI)**: 전체 물가 수준
- **생산자물가지수(PPI)**: 비금속광물, 철강1차제품
- **수입물가지수**: 비금속광물, 철강1차제품

### 건설업 특화 지표
- **건설업 BSI 실적**: 건설업체 체감 경기
- **주택매매가격지수**: 전국 주택 가격 동향
- **주택전세가격지수**: 전국 전세 가격 동향

### 기타 경제지표
- **원/달러 환율**: 수입 원자재 비용 영향
- **경기선행지수**: 미래 경기 동향
- **소비자 심리지수(CCSI)**: 소비 심리
- **경제심리지수(ESI)**: 전반적 경제 심리

## 📁 파일 구조

```
ecos/
├── ECOS_data.py          # 메인 수집 스크립트 (2010년부터)
├── ecos-fetch.ipynb      # 수집 테스트 노트북
├── economic_data_merged.csv  # 통합 경제데이터 (월별)
├── economic_data/        # 개별 지표 CSV 파일들
│   ├── base_rate.csv
│   ├── cpi.csv
│   ├── exchange_usd_원_달러종가_15_30.csv
│   ├── construction_bsi_actual.csv
│   └── ... (기타 경제지표 파일들)
└── README.md            # 이 파일
```

## 🚀 사용법

### 1. 환경 설정

#### ECOS API 키 발급
1. [ECOS 사이트](https://ecos.bok.or.kr/) 접속
2. 회원가입 및 로그인
3. API 인증키 발급 신청
4. `.env` 파일에 API 키 설정

```env
ECOS_API_KEY=your_ecos_api_key_here
```

#### 필요 패키지 설치
```bash
pip install requests pandas mysql-connector-python python-dotenv
```

### 2. 데이터 수집 실행
```bash
python ECOS_data.py
```

#### Jupyter Notebook으로 테스트
```bash
jupyter notebook ecos-fetch.ipynb
```

### 3. 실행 결과

- **콘솔 출력**: 수집 진행 상황 및 결과
- **CSV 백업**: `economic_data/` 폴더에 개별 지표 저장
- **통합 파일**: `economic_data_merged.csv` (월별 데이터)
- **MySQL 저장**: `ecos_data` 테이블에 저장

## 🔧 주요 기능

### 자동 데이터 수집
- **API 호출 제한 준수**: 요청 간격 조절
- **에러 핸들링**: 네트워크 오류, API 오류 대응
- **데이터 검증**: 수집된 데이터의 무결성 확인

### 데이터 전처리
- **날짜 형식 통일**: YYYY-MM 형태로 변환 (월별)
- **결측치 처리**: 전월 이월, 선형 보간
- **데이터 타입 변환**: 문자열 → 숫자형
- **파생변수 생성**: 
  - 월별 변화율 (MoM): CPI 월별 변화율
  - 금리차 (Spread): 국고채/회사채 금리차
  - 월별 변동성: 환율 3개월 이동 표준편차

### 데이터베이스 연동
- **증분 업데이트**: 신규 데이터만 추가
- **중복 방지**: 날짜 기준 중복 체크
- **트랜잭션 처리**: 데이터 일관성 보장

## 📊 데이터 구조

### 수집 데이터 형식 (월별)
```csv
date_str,base_rate,cpi,exchange_usd_krw_close,construction_bsi_actual,cpi_mom,term_spread,credit_spread,...
2024-01,3.50,113.2,1345.2,95.3,0.5,0.8,0.3,...
2024-02,3.50,113.8,1332.8,98.1,0.6,0.7,0.2,...
```

### MySQL 테이블 구조 (월별)
```sql
CREATE TABLE ecos_monthly_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_str VARCHAR(7) NOT NULL UNIQUE,  -- YYYY-MM 형식
    base_rate DECIMAL(5,2),
    cpi DECIMAL(8,2),
    cpi_mom DECIMAL(5,2),                 -- CPI 월별 변화율
    exchange_usd_krw_close DECIMAL(8,2),
    exchange_mstd DECIMAL(8,4),           -- 환율 월별 표준편차
    term_spread DECIMAL(5,2),             -- 10Y-3Y 국고채 금리차
    credit_spread DECIMAL(5,2),           -- BBB-AA 회사채 금리차
    base_rate_mdiff_bp DECIMAL(6,2),      -- 기준금리 월별 변화폭(bp)
    construction_bsi_actual DECIMAL(5,1),
    -- ... 기타 경제지표 컬럼들
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 🔍 모니터링

### 수집 상태 확인
```python
from database import DatabaseConnection

db = DatabaseConnection()
db.connect()

# 최신 데이터 확인
latest_data = db.get_latest_ecos_data()
print(f"최신 데이터: {latest_data}")

# 수집 통계
total_count = db.get_ecos_data_count()
print(f"총 데이터 개수: {total_count}")
```

### 로그 모니터링
- **수집 로그**: 콘솔 출력으로 진행 상황 확인
- **에러 로그**: 실패한 API 호출 및 원인 기록
- **성공률**: 전체 지표 대비 수집 성공률

## 🛠️ 설정 옵션

### API 호출 설정
```python
# ECOS_data.py 내부 설정
SLEEP_TIME = 0.1  # API 호출 간격 (초)
RETRY_COUNT = 3   # 실패시 재시도 횟수
TIMEOUT = 30      # API 응답 대기 시간 (초)
```

### 데이터 수집 기간
```python
# 수집 시작/종료 날짜 설정 (2010년 1월부터)
START_DATE = "2010-01"  # 2010년 1월부터
END_DATE = now_ym()     # 현재 년월까지
```

## ⚠️ 주의사항

### 데이터 특성
- **발표 지연**: 일부 지표는 1-2개월 지연 발표
- **수정 발표**: 기발표 지표의 수정 가능성
- **휴일 영향**: 공휴일에는 데이터 없음

### 오류 대응
```python
# 일반적인 오류 해결방법
1. API 키 확인: .env 파일의 ECOS_API_KEY 확인
2. 네트워크 연결: 인터넷 연결 상태 확인  
3. 데이터베이스: MySQL 연결 및 권한 확인
4. 디스크 용량: CSV 저장 공간 확인
```

## 📈 업데이트 주기

### 권장 실행 주기
- **월별 수집**: 매월 초 신규 데이터 업데이트
- **분기별 검증**: 분기별 전체 데이터 검증
- **연별 백업**: 연말 전체 데이터 백업

### 자동화 설정 (옵션)
```bash
# crontab으로 월별 자동 수집 설정
0 9 1 * * /path/to/python /path/to/ECOS_data.py
```

## 📈 데이터 활용

### 전처리 관련 파일
- **preprocessing/preprocessing.ipynb**: 월별 데이터 전처리 및 파생변수 생성
- **modeling/**: 경제지표 예측 모델링

### 주요 파생변수
1. **월별 변화율 (MoM)**:
   - `cpi_mom`: CPI 월별 변화율 (%)
   
2. **금리차 (Spread)**:
   - `term_spread`: 장단기 금리차 (10Y-3Y 국고채)
   - `credit_spread`: 신용위험 프리미엄 (BBB-AA 회사채)
   
3. **변동성 지표**:
   - `exchange_mstd`: 환율 3개월 이동 표준편차
   - `base_rate_mdiff_bp`: 기준금리 월별 변화폭 (bp)


