# 데이터 전처리 (Data Preprocessing)

한국 건설업계 경기 예측을 위한 ECOS 경제지표 및 DART 재무데이터 전처리 과정

## 📁 파일 구조
```
preprocessing/
├── preprocessing.ipynb    # 메인 전처리 노트북
├── integrated_data.csv    # 최종 통합 데이터셋
└── README.md             # 이 파일
```

## 🔄 데이터 플로우

```
1. Database → 직접 로드 → 전처리 → integrated_data.csv
   ├── ecos_data 테이블 → 직접 쿼리 → 전처리
   ├── dart_data 테이블 → 직접 쿼리 → 전처리  
   └── 두 데이터 결합 → integrated_data.csv (모델링용)

2. 모델링 → 예측 결과 → Database 저장
   └── XGBoost 결과 → prediction_results 테이블
```

## 📊 최종 데이터셋

### integrated_data.csv
- **크기**: 1,110 × 34개 컬럼
- **기업**: 10개 건설업체
- **기간**: 2015년 10월 ~ 2024년 12월 (111개월)
- **구성**:
  - 기본 정보: corp_name, date (2개)
  - 재무지표: 자산총계, 부채총계, 자본총계, 매출액, 영업이익, 분기순이익 (6개)
  - 파생 재무지표: 부채비율, 자기자본비율, ROA, ROE, 매출액성장률, 영업이익성장률, 순이익성장률 (7개)
  - 경제지표: 기준금리, CPI, 환율, 건설업경기지수 등 (19개)

## 🔧 전처리 과정

### 1. 데이터베이스에서 직접 로드

#### 1.1 ECOS 경제데이터 로드
```python
# MySQL에서 ECOS 데이터 직접 조회
db = DatabaseConnection()
ecos_data = db.get_ecos_data()
```
- **소스**: `ecos_data` 테이블
- **기간**: 2015년 10월 ~ 현재
- **지표**: 19개 경제지표
- **장점**: 실시간 최신 데이터, CSV 파일 관리 불필요

#### 1.2 DART 재무데이터 로드
```python
# MySQL에서 DART 데이터 직접 조회
dart_data = db.get_dart_data()
```
- **소스**: `dart_data` 테이블  
- **기업**: 10개 건설업체
- **기간**: 2015년 4분기 ~ 2024년 4분기
- **장점**: 최신 재무데이터 자동 반영

### 2. 데이터 정제 및 변환

#### 2.1 ECOS 데이터 전처리
- **날짜 변환**: VARCHAR(6) → datetime
- **결측치 처리**: 선형보간법 적용
- **이상치 제거**: IQR 방법 사용
- **표준화**: StandardScaler 적용

#### 2.2 DART 데이터 전처리
- **분기→월별 변환**: 각 분기를 3개월로 확장
- **파생변수 생성**: 
  - 부채비율 = 부채총계 / 자산총계 × 100
  - 자기자본비율 = 자본총계 / 자산총계 × 100  
  - ROA = 분기순이익 / 자산총계 × 100
  - ROE = 분기순이익 / 자본총계 × 100
  - 성장률 = (현재값 - 이전값) / 이전값 × 100
- **결측치 처리**: 업종 평균값으로 대체
- **표준화**: StandardScaler 적용

### 3. 데이터 통합

#### 3.1 시계열 정렬
- 기준: 월별 데이터 (YYYY-MM)
- 방법: 날짜 기준 left join

#### 3.2 최종 검증
- 데이터 일관성 체크
- 결측치 비율 확인 (< 5%)
- 이상치 탐지 및 처리

## 📈 데이터 품질 지표

### 완성도
- **ECOS 데이터**: 98.5% (결측치 1.5%)
- **DART 데이터**: 96.8% (결측치 3.2%)
- **통합 데이터**: 97.2% (결측치 2.8%)

### 일관성
- 모든 기업 동일한 기간 커버
- 월별 데이터 연속성 확보
- 재무지표 논리적 일관성 검증

## 🔗 데이터베이스 연동

### 환경 설정
```bash
# .env 파일에 데이터베이스 정보 설정
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=IE_project
```

### 연결 방법
```python
from utils.database import DatabaseConnection
db = DatabaseConnection()
if db.connect():
    ecos_data = db.get_ecos_data()
    dart_data = db.get_dart_data()
```

### 백업 시스템
- 데이터베이스 연결 실패 시 자동으로 CSV 파일에서 로드
- 이중 보안으로 안정적인 데이터 처리 보장

## 🚀 실행 방법

### 1. 환경 설정
```bash
# 필요 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에서 데이터베이스 정보 수정
```

### 2. 전처리 실행
```bash
# Jupyter Notebook에서 실행
jupyter notebook preprocessing.ipynb

# 또는 모든 셀 실행
```

### 3. 결과 확인
- `integrated_data.csv` 파일 생성 확인
- 데이터 품질 지표 검토
- 시각화 결과 확인
