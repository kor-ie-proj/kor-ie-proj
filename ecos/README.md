# 한국 경제지표 데이터 수집 프로젝트

한국은행 ECOS API를 사용하여 주요 경제지표를 수집하고 통합 DataFrame을 생성

## 📋 수집 데이터

### 단일 파일 지표 (9개)
- **기준금리**: 한국은행 기준금리
- **물가지수**: 소비자물가지수(CPI)
- **심리지수**: 경제심리지수(ESI), 현재생활형편CSI
- **건설업**: BSI 실적/전망
- **부동산**: 주택매매/전세가격지수
- **선행지수**: 경기선행지수
- **통화**: M2 전기대비 증가율

### 개별 파일 지표 (8개)
- **금리**: 국고채 3년/10년, 회사채 AA-/BBB-
- **환율**: 원/달러 15:30 종가
- **생산자물가**: 철강1차제품, 비금속광물

## 🚀 사용법

### 1. 환경 설정
```bash
# .env 파일에 API 키 설정
ECOS_API_KEY=your_api_key_here
```

### 2. 전체 실행
```bash
python run_all.py
```

### 3. 개별 실행
```bash
# 데이터 수집
python ecos_data.py

# DataFrame 생성
python create_dataframe.py
```

## 📁 파일 구조

```
ecos/
├── .env                           # API 키 설정
├── ecos_data.py                  # 데이터 수집 스크립트
├── create_dataframe.py           # DataFrame 생성 스크립트
├── run_all.py                    # 전체 실행 스크립트
├── economic_data/                # 수집된 CSV 파일들
└── economic_data_merged.csv      # 통합 DataFrame
```

## 📊 결과

- **기간**: YYYY년 M월 ~ 현재
- **변수**: 17개 경제지표
- **형태**: YYYYMM 인덱스의 DataFrame
- **파일**: `economic_data_merged.csv`

## 🔗 API 정보

- **출처**: 한국은행 경제통계시스템 (ECOS)
- **URL**: https://ecos.bok.or.kr/
- **호출 간격**: 1초 (서버 부하 방지)