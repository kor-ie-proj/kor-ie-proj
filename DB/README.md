# 데이터베이스 설정

MySQL 데이터베이스 스키마 및 연결 관리 모듈

## 개요

프로젝트에서 사용하는 MySQL 데이터베이스의 스키마 정의, 연결 관리, 데이터 접근 인터페이스를 제공합니다.

## 데이터베이스 구조

### 테이블 설계

#### 1. ecos_data (경제지표 데이터)
```sql
CREATE TABLE ecos_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    base_rate DECIMAL(5,2),                           -- 기준금리
    cpi DECIMAL(8,2),                                 -- 소비자물가지수
    exchange_usd_원_달러종가_15_30 DECIMAL(8,2),      -- 원달러환율
    construction_bsi_actual DECIMAL(5,1),             -- 건설업BSI실적
    housing_sale_price DECIMAL(8,2),                  -- 주택매매가격지수
    housing_lease_price DECIMAL(8,2),                 -- 주택전세가격지수
    leading_index DECIMAL(8,2),                       -- 경기선행지수
    ccsi DECIMAL(8,2),                               -- 소비자심리지수
    esi DECIMAL(8,2),                                -- 경제심리지수
    m2_growth DECIMAL(8,4),                          -- M2증가율
    market_rate_국고채3년 DECIMAL(5,2),               -- 국고채3년
    market_rate_국고채10년 DECIMAL(5,2),              -- 국고채10년
    market_rate_회사채3년_AA_ DECIMAL(5,2),           -- 회사채3년AA-
    market_rate_회사채3년_BBB_ DECIMAL(5,2),          -- 회사채3년BBB-
    ppi_비금속광물 DECIMAL(8,2),                     -- PPI비금속광물
    ppi_철강1차제품 DECIMAL(8,2),                    -- PPI철강1차제품
    import_price_비금속광물 DECIMAL(8,2),             -- 수입물가비금속광물
    import_price_철강1차제품 DECIMAL(8,2),            -- 수입물가철강1차제품
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_date (date)
);
```

#### 2. dart_data (재무데이터)
```sql
CREATE TABLE dart_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    corp_name VARCHAR(100) NOT NULL,                  -- 기업명
    corp_code VARCHAR(20) NOT NULL,                   -- 기업코드
    year INT NOT NULL,                                -- 연도
    quarter VARCHAR(10) NOT NULL,                     -- 분기
    report_date DATE,                                 -- 보고서일자
    total_assets DECIMAL(20,2),                       -- 자산총계(억원)
    total_liabilities DECIMAL(20,2),                  -- 부채총계(억원)
    total_equity DECIMAL(20,2),                       -- 자본총계(억원)
    revenue DECIMAL(20,2),                           -- 매출액(억원)
    operating_profit DECIMAL(20,2),                  -- 영업이익(억원)
    quarterly_profit DECIMAL(20,2),                  -- 분기순이익(억원)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_corp_year_quarter (corp_code, year, quarter),
    INDEX idx_corp_name (corp_name),
    INDEX idx_year (year),
    UNIQUE KEY unique_corp_year_quarter (corp_code, year, quarter)
);
```

#### 3. prediction_results (예측결과)
```sql
CREATE TABLE prediction_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    corp_name VARCHAR(100) NOT NULL,                  -- 기업명
    prediction_date DATE NOT NULL,                    -- 예측일자
    target_quarter VARCHAR(10) NOT NULL,              -- 예측대상분기
    predicted_revenue DECIMAL(20,2),                  -- 예측매출액
    predicted_operating_profit DECIMAL(20,2),         -- 예측영업이익
    predicted_quarterly_profit DECIMAL(20,2),         -- 예측순이익
    predicted_total_assets DECIMAL(20,2),             -- 예측자산총계
    predicted_total_liabilities DECIMAL(20,2),        -- 예측부채총계
    predicted_total_equity DECIMAL(20,2),             -- 예측자본총계
    confidence_score DECIMAL(5,3),                    -- 신뢰도점수
    model_version VARCHAR(50),                        -- 모델버전
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_corp_target (corp_name, target_quarter),
    INDEX idx_prediction_date (prediction_date)
);
```

## 파일 구조

```
DB/
├── ddl.sql               # 데이터베이스 스키마 정의
├── db_query.py           # 데이터베이스 연결 및 조회 클래스
├── generate_dump.py      # 데이터베이스 덤프 생성 스크립트
├── dump_20250922_154919.sql  # 백업 덤프 파일
├── .env                  # 환경변수 (DB 비밀번호 등)
└── README.md             # 이 파일
```

## 설정 방법

### 1. MySQL 설치 및 설정

#### Windows
```bash
# MySQL 다운로드 및 설치
# https://dev.mysql.com/downloads/mysql/

# MySQL 서비스 시작
net start mysql80
```

#### Linux/Mac
```bash
# Ubuntu
sudo apt update
sudo apt install mysql-server

# macOS (Homebrew)
brew install mysql
brew services start mysql
```

### 2. 데이터베이스 생성

```sql
-- MySQL에 root로 접속
mysql -u root -p

-- 데이터베이스 생성
CREATE DATABASE IE_project;
USE IE_project;

-- 스키마 적용
SOURCE ddl.sql;

-- 사용자 생성 및 권한 부여 (옵션)
CREATE USER 'ie_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON IE_project.* TO 'ie_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 환경변수 설정

`.env` 파일 생성:
```env
# 데이터베이스 연결 정보
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=IE_project

# API 키
DART_API_KEY=your_dart_api_key
ECOS_API_KEY=your_ecos_api_key
```

## DatabaseConnection 클래스

### 주요 메서드

#### 연결 관리
```python
from db_query import DatabaseConnection

# 데이터베이스 연결
db = DatabaseConnection()
db.connect()

# 연결 종료
db.disconnect()
```

#### 데이터 조회
```python
# ECOS 데이터 조회
ecos_data = db.get_ecos_data()
ecos_data = db.get_ecos_data(start_date='2020-01-01', end_date='2024-12-31')

# DART 데이터 조회  
dart_data = db.get_dart_data()
dart_data = db.get_dart_data(corp_name='삼성물산')

# 특정 기업의 특정 기간 데이터
corp_data = db.get_dart_data(
    corp_name='현대건설', 
    start_year=2020, 
    end_year=2024
)
```

#### 데이터 저장
```python
# ECOS 데이터 저장
success = db.save_ecos_data(ecos_df)

# DART 데이터 저장 (증분)
success = db.save_dart_data_incremental(dart_df)

# 예측 결과 저장
success = db.save_prediction_results(prediction_df)
```

#### 유틸리티 메서드
```python
# 테이블 존재 확인
exists = db.table_exists('dart_data')

# 데이터 개수 확인
count = db.get_record_count('ecos_data')

# 최신 데이터 확인
latest = db.get_latest_data('dart_data', 'report_date')

# 테이블 초기화
db.truncate_table('prediction_results')
```

## 백업 및 복구

### 백업 생성
```bash
# 자동 백업 스크립트 실행
python generate_dump.py

# 수동 백업
mysqldump -u root -p IE_project > backup_YYYYMMDD.sql
```

### 복구
```bash
# 백업 파일로부터 복구
mysql -u root -p IE_project < dump_20250922_154919.sql
```

## 연결 테스트

### 기본 연결 확인
```python
from db_query import DatabaseConnection

try:
    db = DatabaseConnection()
    db.connect()
    print("데이터베이스 연결 성공")
    
    # 테이블 목록 확인
    tables = db.execute_query("SHOW TABLES")
    print(f"테이블 개수: {len(tables)}")
    
    db.disconnect()
except Exception as e:
    print(f"연결 실패: {e}")
```
