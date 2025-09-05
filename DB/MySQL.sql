-- Active: 1752820234086@@127.0.0.1@3306@ie_project
-- IE 프로젝트 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS IE_project;
USE IE_project;

-- 1. ECOS 경제지표 데이터 테이블
-- 데이터 소스: ECOS_data.py (ECOS API)
CREATE TABLE ecos_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date VARCHAR(6) NOT NULL COMMENT 'YYYYMM 형식',
    base_rate DECIMAL(5, 3) COMMENT '기준금리',
    ccsi DECIMAL(5, 1) COMMENT '소비자동향지수',
    construction_bsi_actual DECIMAL(5, 1) COMMENT '건설업경기실사지수(실적)',
    construction_bsi_forecast DECIMAL(5, 1) COMMENT '건설업경기실사지수(전망)',
    cpi DECIMAL(8, 3) COMMENT '소비자물가지수',
    esi DECIMAL(5, 1) COMMENT '경제심리지수',
    exchange_usd_원_달러종가_15_30 DECIMAL(8, 2) COMMENT '원달러환율',
    housing_lease_price DECIMAL(8, 3) COMMENT '주택전세가격지수',
    housing_sale_price DECIMAL(8, 3) COMMENT '주택매매가격지수',
    import_price_비금속광물 DECIMAL(8, 2) COMMENT '수입물가지수_비금속광물',
    import_price_철강1차제품 DECIMAL(8, 2) COMMENT '수입물가지수_철강1차제품',
    leading_index DECIMAL(8, 1) COMMENT '선행종합지수',
    m2_growth DECIMAL(8, 2) COMMENT '통화유동성_M2증가율',
    market_rate_국고채10년 DECIMAL(8, 3) COMMENT '국고채10년수익률',
    market_rate_국고채3년 DECIMAL(8, 3) COMMENT '국고채3년수익률',
    market_rate_회사채3년_AA_ DECIMAL(8, 3) COMMENT '회사채3년AA',
    market_rate_회사채3년_BBB_ DECIMAL(8, 3) COMMENT '회사채3년BBB',
    ppi_비금속광물 DECIMAL(8, 2) COMMENT '생산자물가지수_비금속광물',
    ppi_철강1차제품 DECIMAL(8, 2) COMMENT '생산자물가지수_철강1차제품',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_date (date)
) COMMENT='ECOS API 경제지표 데이터';

-- 2. DART 건설업 재무데이터 테이블
-- 데이터 소스: 건설10_11년로드_2015~2024_연결_분기재무_정규화.csv (DART API)
CREATE TABLE dart_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    corp_name VARCHAR(50) NOT NULL COMMENT '기업명',
    corp_code VARCHAR(8) NOT NULL COMMENT '기업코드',
    year INT NOT NULL COMMENT '연도',
    quarter VARCHAR(2) NOT NULL COMMENT '분기(Q1,Q2,Q3,Q4)',
    report_date DATE NOT NULL COMMENT '보고서기준일',
    total_assets DECIMAL(20, 2) COMMENT '자산총계',
    total_liabilities DECIMAL(20, 2) COMMENT '부채총계',
    total_equity DECIMAL(20, 2) COMMENT '자본총계',
    revenue DECIMAL(20, 2) COMMENT '매출액',
    operating_profit DECIMAL(20, 2) COMMENT '영업이익',
    quarterly_profit DECIMAL(20, 2) COMMENT '분기순이익',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_corp_period (corp_name, year, quarter),
    INDEX idx_corp_name (corp_name),
    INDEX idx_report_date (report_date)
) COMMENT='DART API 건설업 재무데이터';

-- 3. XGBoost 모델 예측 결과 테이블
-- 데이터 소스: modeling/XGBoost_Predict.ipynb 결과
CREATE TABLE prediction_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    corp_name VARCHAR(50) NOT NULL COMMENT '기업명',
    prediction_quarter VARCHAR(10) NOT NULL COMMENT '예측분기(예: 2025Q1)',
    prediction_date DATE NOT NULL COMMENT '예측기준일',
    predicted_total_assets DECIMAL(20, 2) COMMENT '예측_자산총계',
    predicted_total_liabilities DECIMAL(20, 2) COMMENT '예측_부채총계',
    predicted_total_equity DECIMAL(20, 2) COMMENT '예측_자본총계',
    predicted_revenue DECIMAL(20, 2) COMMENT '예측_매출액',
    predicted_operating_profit DECIMAL(20, 2) COMMENT '예측_영업이익',
    predicted_quarterly_profit DECIMAL(20, 2) COMMENT '예측_분기순이익',
    model_version VARCHAR(20) DEFAULT 'XGBoost_v1.0' COMMENT '모델버전',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_corp_prediction (corp_name, prediction_quarter),
    INDEX idx_prediction_quarter (prediction_quarter)
) COMMENT='XGBoost 모델 예측 결과';


SELECT * FROM ecos_data;

SELECT * FROM dart_data;


USE IE_project;
SELECT date, housing_lease_price, housing_sale_price 
FROM ecos_data 
WHERE housing_lease_price IS NOT NULL 
LIMIT 10;