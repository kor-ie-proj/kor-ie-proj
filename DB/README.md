# 데이터베이스 스키마 (Database Schema)

한국 건설업계 경기 예측 프로젝트의 MySQL 데이터베이스 구조

## 📋 데이터베이스 개요

- **데이터베이스명**: `IE_project`
- **테이블 수**: 3개
- **데이터 소스**: ECOS API + DART API + XGBoost 모델 예측 결과

## 🗂️ 테이블 구조

### 1. ecos_data - ECOS 경제지표 데이터

**목적**: 한국은행 ECOS API에서 수집한 경제지표 저장

| 컬럼명 | 데이터타입 | 설명 | 예시 |
|--------|------------|------|------|
| id | INT (PK) | 자동증가 기본키 | 1, 2, 3... |
| date | VARCHAR(6) | 연월(YYYYMM) | 202412 |
| base_rate | DECIMAL(5,3) | 기준금리(%) | 3.500 |
| ccsi | DECIMAL(5,1) | 소비자동향지수 | 98.5 |
| construction_bsi_actual | DECIMAL(5,1) | 건설업경기실사지수(실적) | 75.2 |
| cpi | DECIMAL(8,3) | 소비자물가지수 | 104.256 |
| exchange_usd | DECIMAL(8,2) | 원달러환율 | 1350.50 |
| housing_lease_price | DECIMAL(8,3) | 주택전세가격지수 | 85.123 |
| ... | ... | 총 18개 경제지표 | ... |

**데이터 소스**: `../ecos/economic_data_merged.csv`  
**업데이트 주기**: 월별  
**데이터 기간**: 2015년 10월 ~ 현재

### 2. dart_data - DART 건설업 재무데이터

**목적**: 금융감독원 DART API에서 수집한 건설업체 재무제표 저장

| 컬럼명 | 데이터타입 | 설명 | 예시 |
|--------|------------|------|------|
| id | INT (PK) | 자동증가 기본키 | 1, 2, 3... |
| corp_name | VARCHAR(50) | 기업명 | 삼성물산 |
| corp_code | VARCHAR(8) | 기업코드 | 00214601 |
| year | INT | 연도 | 2024 |
| quarter | VARCHAR(2) | 분기 | Q4 |
| report_date | DATE | 보고서기준일 | 2024-12-31 |
| total_assets | DECIMAL(20,2) | 자산총계(원) | 15000000000000.00 |
| total_liabilities | DECIMAL(20,2) | 부채총계(원) | 8000000000000.00 |
| total_equity | DECIMAL(20,2) | 자본총계(원) | 7000000000000.00 |
| revenue | DECIMAL(20,2) | 매출액(원) | 3000000000000.00 |
| operating_profit | DECIMAL(20,2) | 영업이익(원) | 200000000000.00 |
| quarterly_profit | DECIMAL(20,2) | 분기순이익(원) | 150000000000.00 |

**데이터 소스**: `../dart/dart_out/건설10_11년로드_2015~2024_연결_분기재무_정규화.csv`  
**대상 기업**: 10개 건설업체 (삼성물산, 현대건설, GS건설 등)  
**업데이트 주기**: 분기별  
**데이터 기간**: 2015년 4분기 ~ 2024년 4분기

### 3. prediction_results - XGBoost 예측 결과

**목적**: XGBoost 모델로 예측한 다음 분기 재무지표 저장

| 컬럼명 | 데이터타입 | 설명 | 예시 |
|--------|------------|------|------|
| id | INT (PK) | 자동증가 기본키 | 1, 2, 3... |
| corp_name | VARCHAR(50) | 기업명 | 삼성물산 |
| prediction_quarter | VARCHAR(10) | 예측분기 | 2025Q1 |
| prediction_date | DATE | 예측기준일 | 2025-03-31 |
| predicted_total_assets | DECIMAL(20,2) | 예측_자산총계(원) | 16000000000000.00 |
| predicted_total_liabilities | DECIMAL(20,2) | 예측_부채총계(원) | 8500000000000.00 |
| predicted_total_equity | DECIMAL(20,2) | 예측_자본총계(원) | 7500000000000.00 |
| predicted_revenue | DECIMAL(20,2) | 예측_매출액(원) | 3200000000000.00 |
| predicted_operating_profit | DECIMAL(20,2) | 예측_영업이익(원) | 220000000000.00 |
| predicted_quarterly_profit | DECIMAL(20,2) | 예측_분기순이익(원) | 170000000000.00 |
| model_version | VARCHAR(20) | 모델버전 | XGBoost_v1.0 |

**데이터 소스**: `../modeling/XGBoost_Predict.ipynb` 실행 결과  
**예측 대상**: 다음 분기 재무지표 6개  
**업데이트 주기**: 모델 실행시마다

## 🔧 데이터베이스 설정

### 설치 및 실행
```bash
# MySQL 서버 실행
mysql -u root -p

# 데이터베이스 생성
source MySQL.sql
```

### 인덱스 구성
- `ecos_data`: date 컬럼 고유 인덱스
- `dart_data`: corp_name, report_date 인덱스
- `prediction_results`: corp_name, prediction_quarter 복합 인덱스

### 제약 조건
- 각 테이블별 고유키 제약으로 중복 데이터 방지
- 외래키 제약은 설정하지 않음 (데이터 유연성 확보)

## 📊 데이터 플로우

```
1. ECOS API → economic_data_merged.csv → ecos_data 테이블
2. DART API → 건설10_11년로드_2015~2024_연결_분기재무_정규화.csv → dart_data 테이블
3. XGBoost 모델 → quarterly_predictions_timestamp.csv → prediction_results 테이블
```

## 🚀 사용 예시

```sql
-- 최신 경제지표 조회
SELECT * FROM ecos_data ORDER BY date DESC LIMIT 5;

-- 특정 기업 재무데이터 조회
SELECT * FROM dart_data WHERE corp_name = '삼성물산' ORDER BY year DESC, quarter DESC;

-- 최신 예측 결과 조회
SELECT corp_name, predicted_revenue, predicted_operating_profit 
FROM prediction_results 
WHERE prediction_quarter = (SELECT MAX(prediction_quarter) FROM prediction_results);
```
