# 데이터 전처리

ECOS 경제지표와 DART 재무데이터의 통합 전처리 파이프라인

## 개요

MySQL 데이터베이스에서 ECOS 경제지표와 DART 재무데이터를 로드하여, 머신러닝 모델에 적합한 형태로 전처리하고 통합 데이터셋을 생성합니다.

## 전처리 파이프라인

### 1단계: 데이터 로드 및 기본 전처리
- MySQL에서 ECOS/DART 데이터 로드
- 데이터 타입 변환 (object → numeric)
- 불필요한 컬럼 제거 (id, created_at, updated_at)

### 2단계: ECOS 경제지표 전처리
- 날짜 컬럼을 월말일로 통일
- 현재 달 제외하고 직전 달까지만 사용
- 결측치 처리 (forward fill → backward fill)
- StandardScaler를 이용한 정규화

### 3단계: DART 재무데이터 전처리
- 분기별 데이터를 월별 데이터로 확장 (스텝보간법)
- 불필요한 컬럼 제거 (corp_code, report_date, year, quarter)
- 시계열 보간을 통한 결측치 처리
- 파생변수 생성 (재무비율, 성장률 지표)
- StandardScaler를 이용한 정규화

### 4단계: 데이터 통합
- 날짜(date) 기준으로 ECOS-DART 데이터 병합
- 공통 날짜 범위로 필터링
- 최종 통합 데이터셋 생성 및 저장

## 파생변수 생성

### 재무비율 지표
- **부채비율** = (부채총계 / 자산총계) × 100
- **자기자본비율** = (자본총계 / 자산총계) × 100
- **ROA** = (당기순이익 / 자산총계) × 100
- **ROE** = (당기순이익 / 자본총계) × 100

### 성장률 지표 (전년 동기 대비)
- **매출액성장률** = ((현재 매출액 - 전년 동기 매출액) / 전년 동기 매출액) × 100
- **영업이익성장률** = ((현재 영업이익 - 전년 동기 영업이익) / 전년 동기 영업이익) × 100
- **순이익성장률** = ((현재 순이익 - 전년 동기 순이익) / 전년 동기 순이익) × 100

## 파일 구조

```
preprocessing/
├── preprocessing.ipynb    # 전처리 파이프라인 노트북
├── integrated_data.csv   # 최종 통합 데이터셋
├── fix_index.py          # 인덱스 수정 유틸리티 (사용 중단)
├── restore_corpname.py   # 기업명 복원 유틸리티 (사용 중단)
└── README.md            # 이 파일
```

## 사용법

### 1. 환경 설정

#### 사전 요구사항
- ECOS 데이터가 MySQL에 저장되어 있어야 함
- DART 데이터가 MySQL에 저장되어 있어야 함
- 필요 패키지 설치

```bash
pip install pandas numpy matplotlib seaborn scikit-learn mysql-connector-python
```

### 2. 전처리 실행

#### Jupyter Notebook 실행
```bash
jupyter notebook preprocessing.ipynb
```

#### 셀별 실행 순서
1. **패키지 설치 및 Import** (셀 1-3)
2. **ECOS 데이터 전처리** (셀 4-8)
3. **DART 데이터 전처리** (셀 9-15)
4. **데이터 통합** (셀 16-17)
5. **최종 저장** (셀 18)

### 3. 실행 결과

- **integrated_data.csv**: 최종 통합 데이터셋
- **시각화**: 경제지표 시계열 그래프, 상관관계 히트맵
- **통계 정보**: 데이터 분포, 결측치 현황, 파생변수 통계

## 데이터 변환 과정

### ECOS 데이터 변환
```
원본: 월별 경제지표 (2015.01 ~ 2024.08)
↓
날짜 통일: YYYY-MM-DD (월말일) 형태로 변환
↓
기간 조정: 현재 달 제외, 직전 달까지만 사용
↓
결측치 처리: forward fill → backward fill
↓
정규화: StandardScaler 적용 (평균 0, 표준편차 1)
```

### DART 데이터 변환
```
원본: 분기별 재무데이터 (2015.Q4 ~ 2025.Q2)
↓
월별 확장: 분기를 3개월로 확장 (스텝보간법)
예) 2024.Q1 → 2024.01, 2024.02, 2024.03
↓
컬럼 정리: corp_code, report_date, year, quarter 제거
↓
결측치 처리: 기업별 시계열 선형보간
↓
파생변수 생성: 재무비율 7개 지표 추가
↓
정규화: StandardScaler 적용
```

## 📈 통합 데이터 구조

### 최종 데이터셋 형태
```csv
corp_name,date,자산총계,부채총계,자본총계,매출액,영업이익,분기순이익,부채비율,자기자본비율,ROA,ROE,매출액성장률,영업이익성장률,순이익성장률,base_rate,cpi,exchange_usd_원_달러종가_15_30,...
삼성물산,2024-01-31,1.23,-0.45,0.78,0.92,-0.12,0.34,0.67,-0.23,0.11,0.45,0.89,-0.34,0.56,-1.2,0.8,0.3,...
```

### 컬럼 구성 (총 N개)
- **기본 정보** (2개): corp_name, date
- **기본 재무지표** (6개): 자산총계, 부채총계, 자본총계, 매출액, 영업이익, 분기순이익
- **파생 재무지표** (7개): 부채비율, 자기자본비율, ROA, ROE, 매출액성장률, 영업이익성장률, 순이익성장률
- **경제지표** (19개): base_rate, cpi, exchange_usd 등 ECOS 수집 지표들

## 데이터 품질 관리

### 결측치 처리 전략

#### ECOS 데이터
```python
# 시계열 순서대로 정렬 후 처리
ecos_data = ecos_data.sort_values('date')

# 1차: Forward fill (이전 값으로 채움)
ecos_data = ecos_data.fillna(method='ffill')

# 2차: Backward fill (다음 값으로 채움)
ecos_data = ecos_data.fillna(method='bfill')
```

#### DART 데이터
```python
# 기업별로 시계열 보간 수행
for corp_name in dart_data['corp_name'].unique():
    corp_data = dart_data[dart_data['corp_name'] == corp_name]
    corp_data = corp_data.sort_values('date')
    
    # 선형 보간
    corp_data[numeric_cols] = corp_data[numeric_cols].interpolate(method='linear')
    
    # 여전히 결측치가 있다면 forward/backward fill
    corp_data[numeric_cols] = corp_data[numeric_cols].fillna(method='ffill').fillna(method='bfill')
```

### 데이터 검증

#### 논리적 일관성 확인
```python
# 재무제표 기본 등식 확인
assert (result_df['자산총계'] == result_df['부채총계'] + result_df['자본총계']).all()

# 비율 지표 범위 확인
assert (result_df['부채비율'] >= 0).all()
assert (result_df['자기자본비율'] >= 0).all()
assert (result_df['자기자본비율'] <= 100).all()
```

#### 이상치 탐지
```python
# IQR 방법으로 이상치 탐지
for col in numeric_columns:
    Q1 = data[col].quantile(0.25)
    Q3 = data[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = data[(data[col] < lower_bound) | (data[col] > upper_bound)]
    print(f"{col}: {len(outliers)}개 이상치 발견")
```

## 시각화 및 EDA

### 경제지표 시계열 분석
- 기준금리, 소비자물가지수, 원달러환율, 건설업BSI 시계열 그래프
- 경제지표 간 상관관계 히트맵
- 건설업 BSI와 높은 상관관계를 가진 지표 식별

### 재무지표 분포 분석
- 스케일링 전후 데이터 분포 비교 (박스플롯)
- 기업별 재무지표 성과 비교
- 파생변수의 기업별/시기별 변화 추이

### 통합 데이터 검증
- 기업별 데이터 개수 및 기간 확인
- 최종 결측치 현황 리포트
- 데이터 완성도 통계

## 주의사항

### 스케일링 주의점
- **StandardScaler**: 평균 0, 표준편차 1로 정규화
- **데이터 누수 방지**: 전체 데이터로 스케일링 후 분할 (시계열 특성상 허용)
- **역변환**: 예측 결과 해석시 스케일링 역변환 필요

### 시계열 데이터 특성
- **시계열 순서**: 날짜 순서대로 정렬 필수
- **미래 정보 사용 금지**: 과거 데이터만을 이용한 보간
- **계절성**: 분기별 패턴을 고려한 분석 필요

### 파생변수 제약
- **성장률 지표**: 전년 동기 데이터 필요로 초기 12개월은 결측값
- **ROE 계산**: 자본총계가 음수인 경우 계산 불가
- **분모가 0**: 각종 비율 지표 계산시 분모 0 처리 필요

## 커스터마이징

### 추가 파생변수 생성
```python
# 유동비율 = 유동자산 / 유동부채
data['유동비율'] = data['유동자산'] / data['유동부채'] * 100

# 매출액 영업이익률 = 영업이익 / 매출액
data['영업이익률'] = data['영업이익'] / data['매출액'] * 100

# 총자산회전율 = 매출액 / 자산총계
data['총자산회전율'] = data['매출액'] / data['자산총계']
```

### 다른 스케일링 방법
```python
from sklearn.preprocessing import MinMaxScaler, RobustScaler

# MinMaxScaler (0~1 범위로 정규화)
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(numeric_data)

# RobustScaler (중앙값과 IQR 이용, 이상치에 강건)
scaler = RobustScaler()
scaled_data = scaler.fit_transform(numeric_data)
```

### 다른 결측치 처리 방법
```python
# KNN Imputation
from sklearn.impute import KNNImputer
imputer = KNNImputer(n_neighbors=5)
filled_data = imputer.fit_transform(data_with_missing)

# 다항식 보간
data_interpolated = data.interpolate(method='polynomial', order=2)

# 스플라인 보간
data_interpolated = data.interpolate(method='spline', order=3)
```

## 성능 모니터링

### 데이터 품질 지표
- **완성도**: 전체 데이터 대비 결측치 비율
- **일관성**: 재무제표 등식 만족도
- **정확성**: 이상치 비율 및 범위 검증

### 처리 시간 모니터링
```python
import time

# 각 단계별 처리 시간 측정
start_time = time.time()
# 데이터 처리 코드
end_time = time.time()
print(f"처리 시간: {end_time - start_time:.2f}초")
```
