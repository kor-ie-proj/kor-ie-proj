# 📊 ECOS 경제지표 데이터 수집

한국은행 경제통계시스템(ECOS) API를 활용한 거시경제 지표 자동 수집 모듈

## 📋 개요

건설업 경기 예측을 위한 핵심 거시경제 지표들을 ECOS API를 통해 수집하고 MySQL 데이터베이스에 저장합니다.

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
├── ecos_data.py           # 메인 수집 스크립트
├── create_dataframe.py    # 데이터프레임 생성
├── run_all.py            # 전체 실행 스크립트
├── ecos-fetch.ipynb      # 수집 테스트 노트북
├── economic_data_merged.csv  # 통합 경제데이터
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

#### 자동 수집 (권장)
```bash
python ecos_data.py
```

#### 개별 실행
```bash
# 1. 개별 지표 수집
python run_all.py

# 2. 데이터프레임 생성
python create_dataframe.py
```

#### Jupyter Notebook으로 테스트
```bash
jupyter notebook ecos-fetch.ipynb
```

### 3. 실행 결과

- **콘솔 출력**: 수집 진행 상황 및 결과
- **CSV 백업**: `economic_data/` 폴더에 개별 지표 저장
- **통합 파일**: `economic_data_merged.csv`
- **MySQL 저장**: `ecos_data` 테이블에 저장

## 🔧 주요 기능

### 자동 데이터 수집
- **API 호출 제한 준수**: 요청 간격 조절
- **에러 핸들링**: 네트워크 오류, API 오류 대응
- **데이터 검증**: 수집된 데이터의 무결성 확인

### 데이터 전처리
- **날짜 형식 통일**: YYYY-MM-DD 형태로 변환
- **결측치 처리**: 전월 이월, 선형 보간
- **데이터 타입 변환**: 문자열 → 숫자형

### 데이터베이스 연동
- **증분 업데이트**: 신규 데이터만 추가
- **중복 방지**: 날짜 기준 중복 체크
- **트랜잭션 처리**: 데이터 일관성 보장

## 📊 데이터 구조

### 수집 데이터 형식
```csv
date,base_rate,cpi,exchange_usd_원_달러종가_15_30,construction_bsi_actual,...
2024-01-31,3.50,113.2,1345.2,95.3,...
2024-02-29,3.50,113.8,1332.8,98.1,...
```

### MySQL 테이블 구조
```sql
CREATE TABLE ecos_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    base_rate DECIMAL(5,2),
    cpi DECIMAL(8,2),
    exchange_usd_원_달러종가_15_30 DECIMAL(8,2),
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
# ecos_data.py 내부 설정
SLEEP_TIME = 0.1  # API 호출 간격 (초)
RETRY_COUNT = 3   # 실패시 재시도 횟수
TIMEOUT = 30      # API 응답 대기 시간 (초)
```

### 데이터 수집 기간
```python
# 수집 시작/종료 날짜 설정
START_DATE = "2015-01-01"
END_DATE = "2024-12-31"
```

## ⚠️ 주의사항

### API 사용 제한
- **일일 호출 한도**: 10,000건
- **분당 호출 한도**: 100건
- **동시 접속**: 최대 5개 세션

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
0 9 1 * * /path/to/python /path/to/ecos_data.py
```

---

📊 **ECOS 데이터 수집이 완료되면 [DART 재무데이터 수집](../dart/README.md)을 진행하세요.**
