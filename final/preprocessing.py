"""
preprocessing.py
ECOS 경제데이터 전처리 함수들 (실제 데이터 구조에 맞춤)
FastAPI와 MLOps 파이프라인에서 사용
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
from typing import Tuple, List, Dict, Optional, Union
from sklearn.preprocessing import MinMaxScaler, StandardScaler

# 설정
warnings.filterwarnings('ignore')

# 실제 데이터 컬럼명을 영문으로 매핑
COLUMN_MAPPING = {
    'date': 'date',
    '한국은행 기준금리': 'base_rate',
    '총지수': 'cpi',
    '경제심리지수(원계열)': 'esi',
    '현재생활형편CSI': 'ccsi',
    '업황실적BSI 1)': 'construction_bsi_actual',
    '업황전망BSI 1)': 'construction_bsi_forecast',
    '선행지수순환변동치': 'leading_index',
    '국고채(3년)': 'market_rate_treasury_bond_3yr',
    '국고채(10년)': 'market_rate_treasury_bond_10yr',
    '회사채(3년, AA-)': 'market_rate_corporate_bond_3yr_AA',
    '회사채(3년, BBB-)': 'market_rate_corporate_bond_3yr_BBB',
    '원/달러(종가 15:30)': 'exchange_usd_krw_close',
    '비금속광물_ppi': 'ppi_non_metal_mineral',
    '철강1차제품_ppi': 'ppi_steel_primary',
    '철강1차제품': 'import_price_steel_primary',
    '비금속광물': 'import_price_non_metal_mineral',
    '비금속광물_import_price': 'import_price_non_metal_mineral_alt',
    '철강1차제품_import_price': 'import_price_steel_primary_alt',
    'M2(평잔, 계절조정계열)': 'm2_growth'
}

# 타겟 변수 정의 (원래 코드와 동일하게)
TARGET_COLUMNS = [
    'construction_bsi_actual',
    'base_rate',
    'housing_sale_price',  # 원래 코드 유지
    'm2_growth',
    'credit_spread'        # 원래 코드 유지
]

# 수치형 컬럼들 (매핑된 영문명 기준)
NUMERIC_COLUMN_NAMES = [
    'base_rate', 'cpi', 'esi', 'ccsi', 'construction_bsi_actual', 'construction_bsi_forecast',
    'leading_index', 'market_rate_treasury_bond_3yr', 'market_rate_treasury_bond_10yr',
    'market_rate_corporate_bond_3yr_AA', 'market_rate_corporate_bond_3yr_BBB',
    'exchange_usd_krw_close', 'ppi_non_metal_mineral', 'ppi_steel_primary',
    'import_price_steel_primary', 'import_price_non_metal_mineral', 'm2_growth'
]


def load_ecos_data(csv_path: str = 'ecos_data.csv', 
                   db_connection=None) -> Optional[pd.DataFrame]:
    """
    ECOS 데이터 로드 및 기본 전처리
    
    Args:
        csv_path: CSV 파일 경로
        db_connection: 데이터베이스 연결 객체
    
    Returns:
        전처리된 DataFrame 또는 None
    """
    try:
        # 데이터베이스 연결 시도
        if db_connection is not None:
            db = db_connection()
            if db.connect():
                df = db.get_ecos_data()
                if df is not None and not df.empty:
                    return _process_loaded_data(df)
        
        # CSV 파일에서 로드
        df = pd.read_csv(csv_path)
        return _process_loaded_data(df)
        
    except Exception as e:
        print(f"데이터 로드 실패: {e}")
        return None


def _process_loaded_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    로드된 ecos_data를 처리하여 월간 데이터로 변환
    
    Args:
        df: 원본 ecos_data DataFrame
    
    Returns:
        처리된 월간 DataFrame
    """
    # 1. 컬럼명 영문 매핑
    df = map_column_names(df)
    
    # 2. 데이터 타입 변환
    df = convert_data_types(df)
    
    # 3. 월간 데이터 준비
    df = prepare_monthly_data(df)
    
    # 4. 파생변수 생성
    df = create_derived_variables(df)
    
    # 5. 컬럼 순서 정리
    df = reorder_columns(df)
    
    # 6. 결측치 처리
    df = handle_missing_values(df)
    
    return df


def map_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    한글 컬럼명을 영문으로 매핑
    
    Args:
        df: 원본 DataFrame
    
    Returns:
        컬럼명이 매핑된 DataFrame
    """
    df_mapped = df.copy()
    
    # 매핑 사전에 있는 컬럼들만 변경
    rename_dict = {}
    for korean_name, english_name in COLUMN_MAPPING.items():
        if korean_name in df_mapped.columns:
            rename_dict[korean_name] = english_name
    
    df_mapped = df_mapped.rename(columns=rename_dict)
    
    print(f"컬럼 매핑 완료: {len(rename_dict)}개 컬럼")
    return df_mapped


def convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    데이터 타입 변환 (수치형 컬럼들을 numeric으로 변환)
    
    Args:
        df: 원본 DataFrame
    
    Returns:
        타입 변환된 DataFrame
    """
    df_copy = df.copy()
    
    for col in NUMERIC_COLUMN_NAMES:
        if col in df_copy.columns:
            df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
    
    return df_copy


def prepare_monthly_data(df: pd.DataFrame, current_month: str = "2025-09") -> pd.DataFrame:
    """
    월간 데이터 준비 및 날짜 처리
    
    Args:
        df: 원본 DataFrame
        current_month: 제거할 현재 달 (YYYY-MM 형식)
    
    Returns:
        정리된 월간 DataFrame
    """
    df_monthly = df.copy()
    
    # 날짜 컬럼을 YYYY-MM 형식으로 처리
    if df_monthly['date'].dtype in ['object', 'int64']:
        # YYYYMM 형식을 YYYY-MM 문자열로 변환
        df_monthly['date'] = (df_monthly['date'].astype(str).str[:4] + '-' + 
                             df_monthly['date'].astype(str).str[4:6])
    else:
        # datetime 형식인 경우 YYYY-MM 문자열로 변환
        df_monthly['date'] = df_monthly['date'].dt.strftime('%Y-%m')
    
    # 정렬 및 현재 달 데이터 제거
    df_monthly = df_monthly.sort_values('date').reset_index(drop=True)
    df_monthly = df_monthly[df_monthly['date'] != current_month].reset_index(drop=True)
    
    return df_monthly


def create_derived_variables(df: pd.DataFrame) -> pd.DataFrame:
    """
    월간 파생변수 생성
    
    Args:
        df: 월간 DataFrame
    
    Returns:
        파생변수가 추가된 DataFrame
    """
    df_derived = df.copy()
    
    # CPI MoM (Month over Month) 변화율
    if 'cpi' in df_derived.columns:
        df_derived['cpi_mom'] = df_derived['cpi'].pct_change() * 100
    
    # 기준금리 월별 변화폭 (bp, basis points)
    if 'base_rate' in df_derived.columns:
        df_derived['base_rate_mdiff_bp'] = df_derived['base_rate'].diff() * 100
    
    # Term Spread (10Y - 3Y 국고채 금리차)
    if all(col in df_derived.columns for col in ['market_rate_treasury_bond_10yr', 'market_rate_treasury_bond_3yr']):
        df_derived['term_spread'] = (df_derived['market_rate_treasury_bond_10yr'] - 
                                   df_derived['market_rate_treasury_bond_3yr'])
    
    # Credit Spread (BBB - AA 회사채 금리차) - 원래 코드와 동일
    if all(col in df_derived.columns for col in ['market_rate_corporate_bond_3yr_BBB', 'market_rate_corporate_bond_3yr_AA']):
        df_derived['credit_spread'] = (df_derived['market_rate_corporate_bond_3yr_BBB'] - 
                                     df_derived['market_rate_corporate_bond_3yr_AA'])
    
    # Housing Sale Price 파생변수 (실제 데이터에 없으면 더미 생성)
    if 'housing_sale_price' not in df_derived.columns:
        # CPI를 기반으로 주택가격 프록시 생성 (실제 프로젝트에서는 실제 데이터 사용)
        if 'cpi' in df_derived.columns:
            df_derived['housing_sale_price'] = df_derived['cpi'] * 1.2 + np.random.normal(0, 1, len(df_derived))
            print("housing_sale_price를 CPI 기반으로 생성했습니다 (실제 프로젝트에서는 실제 데이터 사용 권장)")
    
    # M2 growth가 실제로는 level 데이터인 경우 성장률로 변환
    if 'm2_growth' in df_derived.columns:
        # 이미 성장률이 아닌 경우 성장률 계산
        if df_derived['m2_growth'].mean() > 10:  # 값이 크면 성장률이 아닌 것으로 판단
            df_derived['m2_level'] = df_derived['m2_growth'].copy()
            df_derived['m2_growth'] = df_derived['m2_level'].pct_change() * 100
    
    # 환율 관련 파생변수
    if 'exchange_usd_krw_close' in df_derived.columns:
        df_derived['exchange_ma3'] = df_derived['exchange_usd_krw_close'].rolling(window=3, min_periods=1).mean()
        df_derived['exchange_mom'] = df_derived['exchange_usd_krw_close'].pct_change() * 100
    
    # 건설업 BSI 관련 파생변수
    if 'construction_bsi_actual' in df_derived.columns:
        df_derived['construction_bsi_ma3'] = df_derived['construction_bsi_actual'].rolling(window=3, min_periods=1).mean()
        df_derived['construction_bsi_mom'] = df_derived['construction_bsi_actual'].diff()
    
    # ESI 관련 파생변수
    if 'esi' in df_derived.columns:
        df_derived['esi_ma3'] = df_derived['esi'].rolling(window=3, min_periods=1).mean()
        df_derived['esi_mom'] = df_derived['esi'].diff()
    
    # M2 관련 파생변수
    if 'm2_growth' in df_derived.columns:
        df_derived['m2_ma3'] = df_derived['m2_growth'].rolling(window=3, min_periods=1).mean()
        df_derived['m2_mom'] = df_derived['m2_growth'].pct_change() * 100
    
    # 첫 번째 행의 NaN 제거 (변화율 계산으로 인한)
    non_null_columns = [col for col in ['cpi_mom', 'base_rate_mdiff_bp', 'construction_bsi_mom'] if col in df_derived.columns]
    if non_null_columns:
        df_derived = df_derived.dropna(subset=[non_null_columns[0]]).reset_index(drop=True)
    
    return df_derived


def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    컬럼 순서 정리 (관련 지표들을 그룹으로 배치)
    
    Args:
        df: DataFrame
    
    Returns:
        컬럼이 정리된 DataFrame
    """
    monthly_derived_vars = ['cpi_mom', 'base_rate_mdiff_bp', 'term_spread', 'credit_spread',
                           'exchange_ma3', 'exchange_mom', 'construction_bsi_ma3', 'construction_bsi_mom',
                           'esi_ma3', 'esi_mom', 'm2_ma3', 'm2_mom']
    
    time_cols = ['date']
    original_cols = [col for col in df.columns 
                    if col not in time_cols + monthly_derived_vars + ['id', 'created_at', 'updated_at']]
    
    # 컬럼 그룹별 정렬
    column_order = time_cols.copy()
    
    # 각 지표와 관련 파생변수를 그룹으로 배치
    indicator_groups = [
        ('base_rate', ['base_rate_mdiff_bp']),
        ('cpi', ['cpi_mom']),
        ('esi', ['esi_ma3', 'esi_mom']),
        ('construction_bsi_actual', ['construction_bsi_ma3', 'construction_bsi_mom']),
        ('exchange_usd_krw_close', ['exchange_mom', 'exchange_ma3']),
        ('market_rate_treasury_bond_3yr', []),
        ('market_rate_treasury_bond_10yr', ['term_spread']),
        ('market_rate_corporate_bond_3yr_AA', []),
        ('market_rate_corporate_bond_3yr_BBB', ['credit_spread']),
        ('m2_growth', ['m2_ma3', 'm2_mom'])
    ]
    
    for indicator, derived_vars in indicator_groups:
        if indicator in original_cols:
            column_order.append(indicator)
            original_cols.remove(indicator)
            for derived_var in derived_vars:
                if derived_var in df.columns:
                    column_order.append(derived_var)
    
    # 나머지 원본 경제지표들 추가
    column_order.extend(sorted(original_cols))
    
    # 실제 존재하는 컬럼만 선택
    final_columns = [col for col in column_order if col in df.columns]
    
    return df[final_columns]


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    결측치 처리 및 보간
    
    Args:
        df: DataFrame
    
    Returns:
        결측치가 처리된 DataFrame
    """
    df_filled = df.copy()
    missing_info = df_filled.isnull().sum()
    missing_info = missing_info[missing_info > 0]
    
    if len(missing_info) > 0:
        # 수치형 컬럼만 선택하여 보간
        numeric_cols = [col for col in df_filled.columns 
                       if col != 'date' and df_filled[col].dtype in ['float64', 'int64']]
        
        # 선형 보간 적용
        for col in missing_info.index:
            if col in numeric_cols:
                df_filled[col] = df_filled[col].interpolate(method='linear')
                df_filled[col] = df_filled[col].fillna(method='ffill').fillna(method='bfill')
        
        # 남은 결측치는 평균값으로 대체
        remaining_missing = df_filled.isnull().sum()
        remaining_missing = remaining_missing[remaining_missing > 0]
        
        for col in remaining_missing.index:
            if col in numeric_cols:
                mean_val = df_filled[col].mean()
                df_filled[col] = df_filled[col].fillna(mean_val)
    
    return df_filled


def prepare_features_and_targets(df: pd.DataFrame, 
                                target_columns: List[str] = None) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    특징과 타겟 변수 준비 (원래 코드 로직 완전 반영)
    
    Args:
        df: 처리된 월간 DataFrame
        target_columns: 타겟 컬럼 리스트
    
    Returns:
        (processed_df, available_targets, diff_targets)
    """
    if target_columns is None:
        target_columns = TARGET_COLUMNS
    
    # 데이터프레임 복사 및 날짜 인덱스 설정
    df_features = df.copy()
    df_features['date'] = pd.to_datetime(df_features['date'])
    df_features = df_features.set_index('date').sort_index()
    
    # 타겟 변수 존재 여부 확인
    available_targets = [col for col in target_columns if col in df_features.columns]
    print(f"Available target columns: {available_targets}")
    
    # 결측치 선형 보간
    df_features = df_features.interpolate(method='linear', limit_direction='both')
    
    # 타겟 변수에 1차 차분 적용 (비정상성 제거) - 원래 코드와 동일
    for col in available_targets:
        df_features[f'{col}_diff'] = df_features[col].diff()
    
    diff_targets = [f'{col}_diff' for col in available_targets]
    
    # 특징 엔지니어링: 차분된 타겟에 대한 특징 생성 - 원래 코드와 동일
    for col in available_targets:
        diff_col = f'{col}_diff'
        
        # 이동평균 (차분값)
        df_features[f'{diff_col}_ma3'] = df_features[diff_col].rolling(window=3, min_periods=1).mean()
        df_features[f'{diff_col}_ma6'] = df_features[diff_col].rolling(window=6, min_periods=1).mean()
        
        # 변화율 (차분값)
        df_features[f'{diff_col}_pct_change'] = df_features[diff_col].pct_change().fillna(0)
        
        # 지연 특징 (차분값) - 원래 코드와 동일
        for lag in [1, 3, 6]:
            df_features[f'{diff_col}_lag{lag}'] = df_features[diff_col].shift(lag)
    
    # 기존 타겟의 지연 특징 추가 (레벨 정보 보존) - 원래 코드와 동일
    for col in available_targets:
        for lag in [1, 3, 6]:
            df_features[f'{col}_lag{lag}'] = df_features[col].shift(lag)
    
    # 결측치 제거
    df_features = df_features.dropna()
    
    return df_features, available_targets, diff_targets


def feature_selection(df: pd.DataFrame, 
                     diff_targets: List[str],
                     available_targets: List[str],
                     correlation_threshold: float = 0.95,
                     top_features_ratio: float = 0.5,
                     min_features: int = 20) -> Tuple[List[str], pd.Series]:
    """
    상관관계 기반 피쳐 선택
    
    Args:
        df: 특징이 준비된 DataFrame
        diff_targets: 차분된 타겟 변수 리스트
        available_targets: 사용 가능한 타겟 변수 리스트
        correlation_threshold: 높은 상관관계 제거 임계값
        top_features_ratio: 상위 피쳐 선택 비율
        min_features: 최소 피쳐 개수
    
    Returns:
        (selected_features, avg_correlation)
    """
    # 전체 피쳐 목록 생성 (타겟 변수 제외)
    all_features = [col for col in df.columns if col not in available_targets and col not in diff_targets]
    
    # 높은 상관관계를 가진 피쳐 제거
    correlation_matrix = df[all_features].corr()
    upper_tri = correlation_matrix.where(np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool))
    highly_corr_features = [column for column in upper_tri.columns 
                           if any(abs(upper_tri[column]) > correlation_threshold)]
    
    selected_features = [col for col in all_features if col not in highly_corr_features]
    
    # 타겟과의 상관관계 기반 피쳐 선택
    target_correlations = []
    for target in diff_targets:
        if target in df.columns:
            corr_with_target = df[selected_features + [target]].corr()[target].abs().sort_values(ascending=False)
            target_correlations.append(corr_with_target[:-1])  # 자기 자신 제외
    
    # 평균 상관관계 계산
    if target_correlations:
        avg_correlation = pd.concat(target_correlations, axis=1).mean(axis=1).sort_values(ascending=False)
    else:
        avg_correlation = pd.Series(dtype=float)
    
    # 상위 상관관계 피쳐 선택
    n_features = max(min_features, int(len(selected_features) * top_features_ratio))
    final_features = avg_correlation.head(n_features).index.tolist()
    
    return final_features, avg_correlation


def get_processed_data(df: pd.DataFrame, 
                      target_columns: List[str] = None) -> Tuple[np.ndarray, np.ndarray, List[str], List[str], pd.Series]:
    """
    처리된 월간 DataFrame에서 X, y 형태로 반환
    
    Args:
        df: 처리된 월간 DataFrame (load_ecos_data 결과)
        target_columns: 타겟 컬럼 리스트
    
    Returns:
        (X, y, features, targets, correlation)
    """
    if target_columns is None:
        target_columns = TARGET_COLUMNS
    
    # 특징과 타겟 준비
    df_processed, available_targets, diff_targets = prepare_features_and_targets(df, target_columns)
    
    # 피쳐 선택
    final_features, avg_correlation = feature_selection(df_processed, diff_targets, available_targets)
    
    # X, y 배열 생성
    X = df_processed[final_features].values
    y = df_processed[diff_targets].values
    
    return X, y, final_features, diff_targets, avg_correlation


def preprocess_ecos_data(csv_path: str = 'ecos_data.csv', 
                        db_connection=None,
                        target_columns: List[str] = None,
                        current_month: str = "2025-09") -> Dict[str, Union[np.ndarray, List[str], pd.Series, pd.DataFrame]]:
    """
    ECOS 데이터 전체 전처리 파이프라인
    
    Args:
        csv_path: CSV 파일 경로
        db_connection: 데이터베이스 연결 객체
        target_columns: 타겟 컬럼 리스트
        current_month: 제거할 현재 달
    
    Returns:
        전처리 결과 딕셔너리
    """
    try:
        # 1. 데이터 로드 및 기본 전처리 (DataFrame 레벨에서 모든 처리 완료)
        processed_df = load_ecos_data(csv_path, db_connection)
        if processed_df is None:
            raise ValueError("데이터 로드 및 처리 실패")
        
        # 2. 모델링용 데이터 준비
        X, y, features, targets, correlation = get_processed_data(processed_df, target_columns)
        
        return {
            'X': X,
            'y': y,
            'features': features,
            'targets': targets,
            'correlation': correlation,
            'processed_df': processed_df,
            'data_shape': X.shape,
            'target_shape': y.shape,
            'date_range': f"{processed_df['date'].min()} ~ {processed_df['date'].max()}"
        }
        
    except Exception as e:
        print(f"전처리 중 오류 발생: {e}")
        return None


def save_processed_data(df: pd.DataFrame, filepath: str = 'ecos_monthly_processed.csv') -> bool:
    """
    전처리된 데이터 저장
    
    Args:
        df: 저장할 DataFrame
        filepath: 저장 경로
    
    Returns:
        저장 성공 여부
    """
    try:
        df.to_csv(filepath, index=False)
        return True
    except Exception as e:
        print(f"데이터 저장 실패: {e}")
        return False


# FastAPI용 메인 함수
def preprocess_for_api(csv_path: str = 'ecos_data.csv') -> Dict:
    """
    FastAPI에서 사용할 전처리 함수
    
    Args:
        csv_path: CSV 파일 경로
    
    Returns:
        API 응답용 딕셔너리
    """
    result = preprocess_ecos_data(csv_path)
    
    if result is None:
        return {"status": "error", "message": "전처리 실패"}
    
    return {
        "status": "success",
        "data_shape": result['data_shape'],
        "target_shape": result['target_shape'],
        "n_features": len(result['features']),
        "n_targets": len(result['targets']),
        "date_range": result['date_range'],
        "features": result['features'][:10],  # 상위 10개 피쳐만 반환
        "targets": result['targets']
    }


if __name__ == "__main__":
    # 테스트 실행
    result = preprocess_ecos_data('ecos_data.csv')
    
    if result:
        print(f"전처리 완료")
        print(f"특징 데이터 형태: {result['data_shape']}")
        print(f"타겟 데이터 형태: {result['target_shape']}")
        print(f"데이터 기간: {result['date_range']}")
        print(f"타겟 변수들: {result['targets']}")
        print(f"선택된 피쳐들: {result['features']}")
        
        # 전처리된 데이터 저장
        save_processed_data(result['processed_df'])
    else:
        print("전처리 실패")