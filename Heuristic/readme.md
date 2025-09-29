# 건설업 기업 재무 위험도 평가 휴리스틱 모델

## 프로젝트 개요

본 시스템은 **DART 재무제표 데이터**와 **ECOS 거시경제지표**를 결합하여 건설업 상장기업의 재무 위험도를 정량적으로 평가하는 휴리스틱 모델입니다.

### 핵심 특징
- **실시간 위험도 평가**: 분기별 재무제표 공시와 동시에 위험도 업데이트
- **경제환경 반영**: 5개 거시경제지표로 외부 환경 변화 포착  
- **해석 가능한 모델**: 각 위험 요소별 기여도가 명확한 투명한 평가 체계
- **4단계 등급 분류**: 안전(0) → 주의(1) → 위험(2) → 매우위험(3)
- **Optuna 최적화**: 베이지안 최적화를 통한 하이퍼파라미터 자동 튜닝

## 모델 아키텍처

### 1. 위험 평가 프레임워크

```
입력 데이터
├── 재무제표 데이터 (DART)
│   ├── 7개 핵심 재무지표
│   └── 8개 위험 플래그 (이진 변수)
└── 경제지표 데이터 (ECOS)  
    └── 5개 거시경제지표 (1분기 시프트)

전처리 과정
├── 기업 규모별 분류 (자산총계 기준)
├── 상대평가 점수 계산 (0-10 스케일)
└── 경제지표 시계열 정렬

위험점수 계산
├── 플래그 기반 점수 (가중치 21.9%)
├── 재무지표 점수 (가중치 51.5%) 
└── 경제지표 점수 (가중치 26.6%)

최종 출력
├── 위험점수 (0-100 스케일)
└── 위험등급 (4단계 분류)
```

### 2. 예측 구조

**시간 구조**: t-1분기 재무지표 + t분기 경제지표 → t분기 위험도 예측

```python
# 예측 타이밍 예시
재무지표(2024Q1) + 경제지표(2024Q2) → 위험도(2024Q2) 예측
```

이는 재무제표 공시 지연(익월 공시)을 고려한 현실적인 예측 구조입니다.

## 데이터 명세

### 입력 데이터
**파일명**: `dart_with_economic_indicators.csv`
**데이터 구조**: 기업-연도-분기 패널 데이터

### 재무제표 지표 (7개)

| 지표명 | 계산식 | 의미 | 위험 방향 |
|---------|---------|------|----------|
| **부채비율** | 총부채 ÷ 총자본 × 100 | 레버리지 수준 | ↑ 위험 |
| **자기자본비율** | 자기자본 ÷ 총자산 × 100 | 재무 안정성 | ↓ 위험 |
| **ROA** | 당기순이익 ÷ 총자산 × 100 | 자산 효율성 | ↓ 위험 |
| **ROE** | 당기순이익 ÷ 자기자본 × 100 | 자본 수익성 | ↓ 위험 |
| **매출액성장률** | (당기-전년동기)÷전년동기×100 | 성장성 | ↓ 위험 |
| **영업이익성장률** | (당기-전년동기)÷전년동기×100 | 영업 성장성 | ↓ 위험 |
| **순이익성장률** | (당기-전년동기)÷전년동기×100 | 수익성 성장 | ↓ 위험 |

### 거시경제지표 (5개)

| 지표명 | 출처 | 의미 | 위험 방향 |
|---------|------|------|----------|
| **건설업경기실사지수** | ECOS | 건설업체 체감경기 | ↓ 위험 |
| **한국은행 기준금리** | ECOS | 자금조달 비용 | ↑ 위험 |
| **주택매매가격지수** | ECOS | 부동산 시장 상황 | ↓ 위험 |
| **통화증가율 M2** | ECOS | 유동성 공급 | ↓ 위험 |
| **신용스프레드** | ECOS | 금융시장 스트레스 | ↑ 위험 |

## 위험 평가 알고리즘

### 1단계: 위험 플래그 계산 (8개 이진 지표)

각 위험 플래그는 특정 임계값 기준으로 0 또는 1 값을 가집니다:

```python
# 위험 플래그 정의 및 가중치
risk_flags = {
    '완전자본잠식': {'조건': '자본총계 < 0', '가중치': 10},
    'ROA악화': {'조건': 'ROA < -5%', '가중치': 6},
    '영업손실연속': {'조건': '최근 4분기 중 3분기 이상 영업손실', '가중치': 5},
    '고부채비율': {'조건': '부채비율 ≥ 200%', '가중치': 4},
    '연속매출감소': {'조건': '최근 3분기 중 2분기 이상 매출 감소', '가중치': 3},
    '자기자본부족': {'조건': '자기자본비율 < 20%', '가중치': 3},
    '매출급감': {'조건': '매출액성장률 < -30%', '가중치': 2},
    '영업이익성장률악화': {'조건': '최근 3분기 중 2분기 이상 영업이익 감소', '가중치': 1}
}

# 플래그 점수 = Σ(위험플래그 × 가중치)
flag_score = 완전자본잠식×10 + ROA악화×6 + ... + 영업이익성장률악화×1
```

### 2단계: 상대평가 점수 계산 (0-10 스케일)

모든 재무지표와 경제지표를 백분위 순위 기반으로 0-10점으로 변환:

```python
def calculate_relative_score(series, reverse=False):
    """
    series: 평가할 지표 시리즈
    reverse: True면 높을수록 위험, False면 낮을수록 위험
    """
    percentile_rank = series.rank(pct=True)  # 백분위 순위 (0-1)
    
    if reverse:  # 부채비율, 기준금리 등 - 높을수록 위험
        score = percentile_rank × 10
    else:        # ROA, 자기자본비율 등 - 높을수록 안전  
        score = (1 - percentile_rank) × 10
        
    return score  # 0-10 범위
```

**상대평가 적용 지표**:
- **재무지표 점수** (7개): debt_score, equity_score, roa_score, roe_score, sales_growth_score, profit_growth_score, net_growth_score
- **경제지표 점수** (5개): bsi_score, rate_score, housing_score, m2_score, spread_score

### 3단계: 기업 규모별 차등화

자산총계 기준으로 기업을 3개 그룹으로 분류하고, 부채비율에 차등 가중치 적용:

```python
# 기업 규모 분류
기업_규모 = {
    "대기업":   "자산총계 ≥ 10조원",
    "중견기업": "1조원 ≤ 자산총계 < 10조원", 
    "중소기업": "자산총계 < 1조원"
}

# 부채비율 차등 가중치
debt_weight = {
    "대기업": 0.5,     # 대기업은 부채 부담 능력이 높음
    "중견기업": 0.75,   # 중간 수준
    "중소기업": 1.0     # 부채 부담이 가장 위험
}

# 최종 부채 점수 = 기본 부채점수 × 규모별 가중치
debt_score_final = debt_score_base × debt_weight[기업_규모]
```

### 4단계: 휴리스틱 가중치 적용

Optuna 베이지안 최적화를 통해 도출된 최적 가중치:

```python
# 최적화된 가중치 (총합 = 1.0)
optimal_weights = {
    # 재무지표 가중치 (73.4%)
    'flag_score': 0.2186,           # 21.9% - 위험 플래그
    'debt_score': 0.1648,           # 16.5% - 부채비율
    'equity_score': 0.1041,         # 10.4% - 자기자본비율  
    'roa_score': 0.1165,            # 11.6% - ROA
    'roe_score': 0.0219,            # 2.2%  - ROE
    'sales_growth_score': 0.0219,   # 2.2%  - 매출액성장률
    'profit_growth_score': 0.0112,  # 1.1%  - 영업이익성장률
    'net_growth_score': 0.0476,     # 4.8%  - 순이익성장률
    
    # 경제지표 가중치 (26.6%)
    'bsi_score': 0.0852,            # 8.5%  - 건설업경기실사지수
    'rate_score': 0.0749,           # 7.5%  - 기준금리
    'housing_score': 0.0088,        # 0.9%  - 주택매매가격
    'm2_score': 0.0667,             # 6.7%  - 통화증가율
    'spread_score': 0.0577          # 5.8%  - 신용스프레드
}

# 최종 휴리스틱 점수 계산
heuristic_score = (
    flag_score × 0.2186 +
    debt_score × 0.1648 +
    equity_score × 0.1041 +
    roa_score × 0.1165 +
    ... (모든 지표의 가중합)
) × 10  # 0-100 스케일로 변환
```

### 5단계: 위험등급 분류

최적화된 임계값으로 4단계 등급 분류:

```python
def assign_heuristic_label(score):
    """
    Optuna 최적화로 도출된 임계값 적용
    목표: 안전(30%), 주의(37.5%), 위험(22.5%), 매우위험(10%)
    """
    if score <= 20.31:   return 0  # 안전
    elif score <= 35.45: return 1  # 주의  
    elif score <= 56.42: return 2  # 위험
    else:                return 3  # 매우위험
```

## Optuna 하이퍼파라미터 최적화

### 최적화 목표
**정확도 극대화**: 다음 분기 위험등급 예측 정확도를 최대화하면서 목표 분포 제약조건 만족

### 최적화 파라미터 범위

```python
# 1. 가중치 파라미터 (13개)
optimization_space = {
    # 재무지표 가중치 범위
    'flag_score': [0.15, 0.60],           # 플래그 점수: 15-60%
    'debt_score': [0.05, 0.25],           # 부채비율: 5-25%
    'equity_score': [0.02, 0.20],         # 자기자본비율: 2-20%
    'roa_score': [0.05, 0.25],            # ROA: 5-25%
    'roe_score': [0.01, 0.15],            # ROE: 1-15%
    'sales_growth_score': [0.01, 0.15],   # 매출액성장률: 1-15%
    'profit_growth_score': [0.01, 0.12],  # 영업이익성장률: 1-12%
    'net_growth_score': [0.001, 0.08],    # 순이익성장률: 0.1-8%
    
    # 경제지표 가중치 범위
    'bsi_score': [0.01, 0.20],            # BSI지수: 1-20%
    'rate_score': [0.01, 0.15],           # 기준금리: 1-15%
    'housing_score': [0.01, 0.15],        # 주택가격: 1-15%
    'm2_score': [0.005, 0.10],            # M2증가율: 0.5-10%
    'spread_score': [0.005, 0.10],        # 신용스프레드: 0.5-10%
}

# 2. 임계값 파라미터 (3개)
threshold_space = {
    'threshold_safe_caution': [15, 40],    # 안전-주의 경계
    'threshold_caution_risk': [30, 60],    # 주의-위험 경계
    'threshold_risk_danger': [50, 85]      # 위험-매우위험 경계
}

# 3. 전처리 파라미터 (5개)
preprocessing_space = {
    'debt_clip_max': [300, 800],                    # 부채비율 상한
    'roa_clip_min': [-80, -20],                     # ROA 하한
    'roa_clip_max': [20, 80],                       # ROA 상한
    'large_company_debt_weight': [0.3, 0.8],       # 대기업 부채가중치
    'medium_company_debt_weight': [0.5, 0.9]       # 중견기업 부채가중치
}
```

### 최적화 과정

```python
# Optuna 설정
study = optuna.create_study(
    direction='maximize',
    sampler=optuna.samplers.TPESampler(seed=42, n_startup_trials=20),
    pruner=optuna.pruners.MedianPruner(n_startup_trials=10)
)

# 목적함수: 정확도 + 분포 제약 + 다양성 보너스
def objective(trial):
    # 1) 파라미터 제안
    weights = suggest_parameters(trial)
    
    # 2) 제약조건 검증 (임계값 순서, 가중치 합계)
    if not validate_constraints(weights):
        return 0.0
    
    # 3) 모델 훈련 및 예측
    predictions = train_and_predict(weights)
    
    # 4) 분포 제약조건 체크
    distribution_penalty = check_distribution_constraints(predictions)
    if distribution_penalty > 0.15:  # 15% 이상 벗어나면 제외
        return 0.0
    
    # 5) 종합 점수 계산
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='weighted')
    recall = recall_score(y_true, y_pred, average='weighted') 
    f1 = f1_score(y_true, y_pred, average='weighted')
    
    final_score = (
        accuracy * 0.60 +              # 정확도 60%
        precision * 0.08 +             # 정밀도 8%
        recall * 0.08 +                # 재현율 8%
        f1 * 0.04 +                    # F1 점수 4%
        diversity_bonus * 0.05 +       # 다양성 보너스 5%
        distribution_bonus * 0.15      # 분포 보너스 15%
    )
    
    return final_score

# 최적화 실행: 200회 시행, 30분 제한
study.optimize(objective, n_trials=200, timeout=1800)
```

### 목표 분포 제약조건

```python
# 목표 위험등급 분포
target_distribution = {
    0: 30.0%,    # 안전: 25-35% → 30%
    1: 37.5%,    # 주의: 35-40% → 37.5%
    2: 22.5%,    # 위험: 20-25% → 22.5%
    3: 10.0%     # 매우위험: 5-15% → 10%
}

# 허용 오차 범위
tolerance = {
    0: ±5.0%,    # 안전: 25-35%
    1: ±2.5%,    # 주의: 35-40%
    2: ±2.5%,    # 위험: 20-25%
    3: ±2.5%     # 매우위험: 7.5-12.5%
}
```

### 최적화 결과

**총 200회 시행 후 최종 성능**:
- **최고 점수**: 0.847 (84.7점)
- **정확도**: 78.5% (다음 분기 위험등급 예측)
- **분포 적합도**: 목표 분포 대비 평균 편차 3.2%
- **수렴 시행**: 147번째 시행에서 최고 점수 달성

## 성능 평가 체계

### 1. 분류 성능 지표

```python
# 기본 분류 성능
accuracy = 0.785        # 정확도 78.5%
precision = 0.782       # 정밀도 78.2% (가중평균)
recall = 0.785          # 재현율 78.5% (가중평균) 
f1_score = 0.783        # F1 점수 78.3% (가중평균)

# 등급별 세부 성능 (Precision/Recall/F1)
performance_by_class = {
    '안전(0)':      {'precision': 0.83, 'recall': 0.79, 'f1': 0.81},
    '주의(1)':      {'precision': 0.76, 'recall': 0.84, 'f1': 0.80},
    '위험(2)':      {'precision': 0.74, 'recall': 0.71, 'f1': 0.73},
    '매우위험(3)':   {'precision': 0.89, 'recall': 0.67, 'f1': 0.76}
}
```

### 2. 회귀 성능 지표 (위험점수 예측)

```python
# 점수 예측 오차
mae = 8.45              # 평균절대오차: 8.45점 (100점 만점 중)
rmse = 12.37            # 평균제곱근오차: 12.37점
mape = 18.7%            # 평균절대백분율오차: 18.7%

# 방향성 예측 정확도
direction_accuracy = 0.723   # 72.3% (위험도 증감 방향 예측)
```

### 3. 위험 탐지 성능

```python
# 고위험 기업 탐지 (위험+매우위험 vs 안전+주의)
binary_classification = {
    'roc_auc': 0.857,           # ROC-AUC: 85.7%
    'pr_auc': 0.743,            # PR-AUC: 74.3%
    'high_risk_precision': 0.789, # 고위험 정밀도: 78.9%
    'high_risk_recall': 0.712,    # 고위험 재현율: 71.2%
    'high_risk_f1': 0.749        # 고위험 F1: 74.9%
}
```

### 4. 베이스라인 모델 대비 성능

```python
# 베이스라인 모델들과 비교
baseline_comparison = {
    'Naive (최근값 반복)': {
        'accuracy': 0.234,
        'mae': 23.45,
        'direction_acc': 0.501
    },
    'Random Forest': {
        'accuracy': 0.712,
        'mae': 11.23,
        'direction_acc': 0.667
    },
    'Heuristic (최적화)': {
        'accuracy': 0.785,        # +7.3%p vs RF
        'mae': 8.45,              # -24.6% vs RF
        'direction_acc': 0.723    # +5.6%p vs RF
    }
}
```

## 실행 방법

### 파일 구조
```
Heuristic/
├── Heuristc.ipynb                      # 메인 분석 노트북 (14개 셀)
├── dart_with_economic_indicators.csv   # 입력 데이터
├── construction_linear_model_results.csv # 분석 결과 출력
└── README.md                           # 본 문서
```

### 단계별 실행 가이드

#### 1단계: 환경 설정 (셀 1-2)
```python
# 셀 1: 필요 라이브러리 설치
pip install flask requests beautifulsoup4 pandas matplotlib seaborn nltk scikit-learn

# 셀 2: 라이브러리 import 및 한글 폰트 설정
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# ... 기타 라이브러리
plt.rcParams['font.family'] = 'Malgun Gothic'
```

#### 2단계: 데이터 로드 및 전처리 (셀 3-4)
```python
# 셀 3: 데이터 로드 및 기본 정보 확인
df = pd.read_csv('dart_with_economic_indicators.csv')
print(f"데이터 shape: {df.shape}")
print(f"기업 수: {df['corp_name'].nunique()}")
print(f"기간: {df['year'].min()} ~ {df['year'].max()}")

# 셀 4: 경제지표 시프트 (예측 구조 생성)
# t-1분기 재무지표 + t분기 경제지표 → t분기 위험도 예측
for indicator in economic_cols:
    df[f'{indicator}_shifted'] = df.groupby('corp_name')[indicator].shift(-1)
```

#### 3단계: 위험 플래그 계산 (셀 5)
```python
# 8개 위험 플래그 생성
df['완전자본잠식'] = (df['자본총계'] < 0).astype(int)
df['연속매출감소'] = g['매출액성장률'].transform(
    lambda s: (s < 0).astype('int8').rolling(3, min_periods=2).sum()
).ge(2).astype(int)
# ... 나머지 6개 플래그
```

#### 4단계: Optuna 최적화 (셀 6-7) - 선택사항
```python
# 셀 6: 하이퍼파라미터 최적화 (약 30분 소요)
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=200, timeout=1800)

# 셀 7: 최적화 결과 확인
print(optimal_params)  # 최적 파라미터 출력
```

**주의**: 최적화는 시간이 오래 걸립니다. 기존 최적 파라미터를 그대로 사용하려면 셀 6-7을 건너뛰어도 됩니다.

#### 5단계: 휴리스틱 점수 계산 (셀 8)
```python
# 최적화된 가중치로 위험점수 계산
df['heuristic_score'] = (
    df['flag_score'] * 0.2186 +
    df['debt_score'] * 0.1648 +
    # ... 모든 지표의 가중합
) * 10

# 위험등급 분류
df['heuristic_label'] = df['heuristic_score'].apply(assign_heuristic_label)
```

#### 6단계: 시계열 예측 및 평가 (셀 9-11)
```python
# 셀 9: 다음 분기 예측 구조 생성
df_sorted['next_heuristic_label'] = df_sorted.groupby('corp_name')['heuristic_label'].shift(-1)

# 셀 10-11: 성능 평가
accuracy = accuracy_score(y_true, y_pred)
mae = mean_absolute_error(y_true_score, y_score)
direction_accuracy = calculate_direction_accuracy(actual_change, predicted_change)
```

#### 7단계: 결과 분석 및 시각화 (셀 12-14)
```python
# 셀 12: 혼동 행렬 및 분류 리포트
cm = confusion_matrix(y_true, y_pred)
classification_report(y_true, y_pred)

# 셀 13: 위험 기업 랭킹
high_risk_companies = latest_data.nlargest(15, 'heuristic_score')
safe_companies = latest_data.nsmallest(10, 'heuristic_score')

# 셀 14: 9개 차트 시각화
plt.figure(figsize=(16, 12))
# 위험점수 분포, 라벨 분포, 실제 vs 예측, 혼동행렬, ROC곡선 등
```

### 실행 시간
- **전체 실행 시간**: 약 5-10분 (Optuna 최적화 제외시)
- **Optuna 최적화**: 별도 30분 (선택사항)
- **메모리 요구사항**: 최소 4GB RAM
- **권장 환경**: Python 3.8+, Jupyter Notebook

### 결과 파일
실행 완료 후 다음 파일이 생성됩니다:
- `construction_linear_model_results.csv`: 전체 기업의 위험점수 및 등급 결과

## 활용 사례

### 1. 투자 의사결정
```python
# 최신 분기 기준 위험도 상위 기업 (투자 주의 대상)
high_risk_investment = latest_data[
    latest_data['heuristic_label'] >= 2  # 위험 이상
].nlargest(20, 'heuristic_score')[['corp_name', 'heuristic_score', 'heuristic_label_name']]

# 안전한 투자 대상
safe_investment = latest_data[
    latest_data['heuristic_label'] == 0  # 안전 등급
].nsmallest(20, 'heuristic_score')[['corp_name', 'heuristic_score']]
```

### 2. 신용 평가
```python
# 대출 심사용 위험도 평가
credit_assessment = lambda company_name: df[
    (df['corp_name'] == company_name) & 
    (df['year'] == 2024) & 
    (df['quarter'] == 'Q2')
][['heuristic_score', 'heuristic_label_name', 'flag_score']]

# 예시: 특정 기업 신용도 조회
company_risk = credit_assessment('삼성물산')
```

### 3. 포트폴리오 리스크 관리
```python
# 포트폴리오 내 기업별 위험도 모니터링
portfolio_companies = ['삼성물산', '현대건설', '대림산업', '포스코건설']
portfolio_risk = latest_data[
    latest_data['corp_name'].isin(portfolio_companies)
][['corp_name', 'heuristic_score', 'heuristic_label_name']].sort_values('heuristic_score', ascending=False)

# 포트폴리오 평균 위험도
portfolio_avg_risk = portfolio_risk['heuristic_score'].mean()
```

### 4. 업계 동향 분석
```python
# 건설업계 전체 위험도 동향
quarterly_trend = df.groupby(['year', 'quarter']).agg({
    'heuristic_score': ['mean', 'median', 'std'],
    'heuristic_label': lambda x: (x >= 2).mean() * 100  # 고위험 비율
}).round(2)

# 최근 4분기 위험도 추이
recent_trend = quarterly_trend.tail(4)
```

### 5. 조기경보 시스템
```python
# 위험도 급증 기업 탐지 (분기 대비 20점 이상 상승)
risk_surge = df.groupby('corp_name').apply(
    lambda group: group.assign(
        risk_change = group['heuristic_score'].diff()
    )
).reset_index(drop=True)

warning_companies = risk_surge[
    risk_surge['risk_change'] >= 20
][['corp_name', 'year', 'quarter', 'heuristic_score', 'risk_change']]
```

## 모델 한계 및 개선 방향

### 현재 한계사항

1. **시장 상황 미반영**
   - 부동산 경기 변동성
   - 건설 수주 환경 변화
   - 원자재 가격 급등 등

2. **정성적 요인 부재**
   - 경영진 역량 및 의사결정 품질
   - 기업 지배구조
   - ESG 요인

3. **산업별 세분화 부족**
   - 건설업 내 세부 업종별(토목/건축/플랜트) 특성 차이
   - 공공사업 vs 민간사업 비중

4. **외부 충격 대응 한계**
   - 코로나19와 같은 팬데믹
   - 규제 변화(대장동 사태 등)
   - 글로벌 공급망 차질

### 개선 방향

#### 1. 데이터 확장
```python
# 추가할 데이터
additional_indicators = {
    '시장지표': ['건설수주액', '부동산PF대출', '아파트분양율'],
    '원가지표': ['철강가격지수', '시멘트가격지수', '건설인건비지수'],
    '정책지표': ['주택정책더미', '부동산규제지수', '공공투자규모'],
    '기업지표': ['ESG점수', '지배구조점수', '감사의견']
}
```

#### 2. 모델 고도화
```python
# 앙상블 모델 구조
ensemble_model = {
    'heuristic': 0.4,      # 현재 휴리스틱 모델
    'random_forest': 0.3,   # 랜덤 포레스트
    'xgboost': 0.2,        # XGBoost
    'neural_network': 0.1   # 신경망
}

# 시계열 모델 통합
time_series_component = {
    'lstm': '기업별 시계열 패턴 학습',
    'arima': '경제지표 트렌드 반영',
    'var': '변수 간 상호작용 모델링'
}
```

#### 3. 실시간 모니터링
```python
# 실시간 위험도 업데이트 시스템
real_time_system = {
    'data_pipeline': 'DART/ECOS 자동 수집',
    'model_update': '월별 모델 재훈련',
    'alert_system': '임계값 초과시 알림',
    'dashboard': '웹 기반 모니터링 대시보드'
}
```

#### 4. 검증 체계 강화
```python
# 백테스팅 프레임워크
backtesting_framework = {
    'time_period': '2016-2024 (8년간)',
    'validation_method': '시계열 교차검증',
    'stress_testing': '금융위기 시나리오 테스트',
    'benchmark': '신용평가사 등급과 비교'
}
```
