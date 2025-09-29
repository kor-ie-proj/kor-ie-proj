# 데이터 전처리

ECOS 경제지표와 DART 재무데이터의 독립적 전처리 파이프라인

## 개요

이 모듈은 MySQL 데이터베이스에서 수집된 데이터를 머신러닝 모델에 적합한 형태로 전처리합니다. ECOS 경제지표와 DART 재무데이터를 각각 독립적으로 처리하여 서로 다른 분석 목적에 활용할 수 있도록 구성되어 있습니다.

## 처리 방식

### 독립 처리 구조
- **ECOS 경제지표**: 월별 거시경제 데이터 처리 (2010년 1월부터)
- **DART 재무데이터**: 분기별 기업 재무제표 처리 (2016년 2분기부터)

각 데이터셋은 서로 다른 분석 모델에서 활용되므로 독립적으로 전처리됩니다.

## ECOS 경제지표 전처리

### 처리 과정
1. **데이터 로드**: MySQL `ecos_data` 테이블에서 19개 경제지표 로드
2. **데이터 정제**: 수치형 변환, 현재 달 데이터 제외
3. **파생변수 생성**: 8개 월별 파생변수 생성
4. **결측치 처리**: 선형보간법 및 전후방 채움법 적용
5. **최종 저장**: `ecos_monthly_data.csv` 파일로 저장

### 생성 파생변수
- **CPI MoM**: 소비자물가지수 전월 대비 변화율 (%)
- **기준금리 월별 변화폭**: 전월 대비 변화폭 (bp)
- **Term Spread**: 10년-3년 국고채 금리차 (%p)
- **Credit Spread**: BBB-AA 회사채 금리차 (%p)
- **환율 변화율**: 전월 대비 환율 변화율 (%)
- **환율 3개월 이동평균**: 환율 평활화 지표
- **건설업 BSI 이동평균**: 3개월 이동평균
- **건설업 BSI 변화**: 전월 대비 변화

### 출력 데이터
- **파일명**: `ecos_monthly_data.csv`
- **데이터 범위**: 2010년 2월 ~ 2024년 8월 (현재 달 제외)
- **컬럼 수**: 27개 (날짜 + 원본 19개 + 파생 8개)

## DART 재무데이터 전처리

### 처리 과정
1. **데이터 로드**: MySQL `dart_data` 테이블에서 건설업 10개사 재무데이터 로드
2. **데이터 필터링**: 기업별 상장/분할 시점 고려하여 유효 기간만 선택
3. **파생변수 생성**: 7개 재무비율 및 성장률 지표 생성
4. **결측치 제거**: 성장률 계산 불가능한 초기 데이터 제거
5. **최종 저장**: `dart_final.csv` 파일로 저장

### 생성 파생변수

#### 재무비율 지표
- **부채비율** = (부채총계 / 자본총계) × 100
- **자기자본비율** = (자본총계 / 자산총계) × 100
- **ROA** = (분기순이익 / 자산총계) × 100 (자산수익률)
- **ROE** = (분기순이익 / 자본총계) × 100 (자기자본수익률)

#### 성장률 지표 (전분기 대비)
- **매출액성장률** = 전분기 대비 매출액 변화율 (%)
- **영업이익성장률** = 전분기 대비 영업이익 변화율 (%)
- **순이익성장률** = 전분기 대비 순이익 변화율 (%)

### 출력 데이터
- **파일명**: `dart_final.csv`
- **데이터 범위**: 2016년 2분기 ~ 2024년 2분기
- **기업 수**: 10개 건설업체
- **컬럼 수**: 13개 (기본정보 3개 + 재무지표 6개 + 파생변수 7개)

## 파일 구조

```
preprocessing/
├── preprocessing.ipynb          # 전처리 파이프라인 노트북
├── ecos_monthly_data.csv       # ECOS 월별 경제지표 (최종 출력)
├── dart_final.csv              # DART 분기별 재무데이터 (최종 출력)
├── integrated_data.csv         # 기존 통합 파일 (deprecated)
└── README.md                   # 이 문서
```

## 사용법

### 환경 설정
```bash
# 필요 패키지 설치
pip install pandas numpy matplotlib seaborn scikit-learn mysql-connector-python python-dotenv

# 데이터베이스 환경변수 설정 (.env 파일)
DB_HOST=localhost
DB_USER=root  
DB_PASSWORD=your_password
DB_NAME=IE_project
```

### 전처리 실행
```bash
# Jupyter 노트북 실행
jupyter notebook preprocessing.ipynb

# 전체 파이프라인 실행 (순서대로)
```

## 데이터 품질 관리

### ECOS 경제지표 품질 관리
```python
# 결측치 분석 및 보간
missing_info = ecos_data.isnull().sum()
ecos_data = ecos_data.interpolate(method='linear')
ecos_data = ecos_data.fillna(method='ffill').fillna(method='bfill')
```

### DART 재무데이터 품질 관리
```python
# 재무제표 논리적 일관성 검증
assert (dart_data['자산총계'] >= dart_data['부채총계']).all()
assert (dart_data['자산총계'] == dart_data['부채총계'] + dart_data['자본총계']).all()

# 성장률 계산 불가 케이스 제거
growth_cols = ['매출액성장률', '영업이익성장률', '순이익성장률']
dart_data = dart_data.dropna(subset=growth_cols)
```

## 시각화 및 분석

### ECOS 데이터 시각화
- **시계열 그래프**: 기준금리, CPI, 환율, 건설업BSI 트렌드 분석
- **파생변수 분석**: Term Spread, Credit Spread, 변화율 지표 시각화
- **상관관계 히트맵**: 경제지표 간 상관성 분석

### DART 데이터 분석
- **기업별 재무현황**: 자산, 부채, 자본 구조 분석
- **수익성 지표**: ROA, ROE 기업별 비교
- **성장성 지표**: 매출, 영업이익, 순이익 성장률 추이

## 기술적 특징

### 처리 성능
- **메모리 효율**: 기업별 그룹 처리로 메모리 사용량 최적화
- **병렬 처리**: 독립적 데이터셋 처리로 개발 효율성 확보
- **오류 처리**: 데이터베이스 연결 실패시 CSV 파일 백업 로드

### 확장성
- **모듈화**: ECOS, DART 처리 로직 완전 분리
- **설정 가능**: 파생변수 생성 로직 쉽게 수정 가능
- **호환성**: 다른 분석 모듈과 독립적 연동 가능

## 활용 예시

### ECOS 월별 데이터 활용
```python
# LSTM 경제예측 모델용 데이터
ecos_monthly = pd.read_csv('ecos_monthly_data.csv')
target_features = ['construction_bsi_actual', 'base_rate', 'cpi_mom']

# 시계열 예측용 데이터 준비
X = ecos_monthly[target_features].values
```

### DART 분기별 데이터 활용  
```python
# 휴리스틱 리스크 평가 모델용 데이터
dart_final = pd.read_csv('dart_final.csv')
risk_features = ['부채비율', 'ROA', 'ROE', '매출액성장률']

# 기업별 리스크 스코어 계산
for corp in dart_final['corp_name'].unique():
    corp_data = dart_final[dart_final['corp_name'] == corp]
    risk_score = calculate_risk(corp_data[risk_features])
```

## 문제 해결

### 일반적인 오류
```python
# 1. 데이터베이스 연결 오류
# → .env 파일의 DB 설정 확인
# → MySQL 서비스 실행 상태 확인

# 2. 결측치 과다 발생
# → 원본 데이터 수집 상태 점검  
# → API 키 유효성 확인

# 3. 파생변수 계산 오류
# → 분모 0 값 확인 (ROE, ROA 계산시)
# → 성장률 계산을 위한 이전 기간 데이터 존재 확인
```
