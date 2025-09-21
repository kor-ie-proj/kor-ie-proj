"""
test_preprocessing.py
전처리 함수 테스트 및 실험용 스크립트
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
print("✅ preprocessing.py 테스트 완료")

import pandas as pd
import numpy as np
import sys
import os

# preprocessing.py 임포트
try:
    from preprocessing import preprocess_ecos_data, load_ecos_data, preprocess_for_api
    print("✅ preprocessing.py 모듈 임포트 성공")
except ImportError as e:
    print(f"❌ preprocessing.py 모듈 임포트 실패: {e}")
    sys.exit(1)

def test_file_exists(filepath='ecos_data.csv'):
    """파일 존재 여부 확인"""
    if os.path.exists(filepath):
        print(f"✅ {filepath} 파일 존재 확인")
        return True
    else:
        print(f"❌ {filepath} 파일이 없습니다")
        return False

def test_basic_load(filepath='ecos_data.csv'):
    """기본 데이터 로드 테스트"""
    print("\n=== 기본 데이터 로드 테스트 ===")
    
    try:
        # 원본 데이터 로드
        df = pd.read_csv(filepath)
        print(f"✅ 원본 데이터 로드 성공: {df.shape}")
        print(f"   컬럼 수: {len(df.columns)}")
        print(f"   행 수: {len(df)}")
        
        # 기본 정보 출력
        print(f"   컬럼 목록 (처음 10개): {list(df.columns[:10])}")
        if 'date' in df.columns:
            print(f"   날짜 범위: {df['date'].min()} ~ {df['date'].max()}")
        
        return df
    except Exception as e:
        print(f"❌ 원본 데이터 로드 실패: {e}")
        return None

def test_preprocessing_functions(filepath='ecos_data.csv'):
    """전처리 함수들 개별 테스트"""
    print("\n=== 전처리 함수 개별 테스트 ===")
    
    try:
        # load_ecos_data 함수 테스트
        print("1. load_ecos_data() 테스트...")
        processed_df = load_ecos_data(filepath)
        
        if processed_df is not None:
            print(f"✅ load_ecos_data() 성공: {processed_df.shape}")
            print(f"   처리된 컬럼 수: {len(processed_df.columns)}")
            print(f"   처리된 행 수: {len(processed_df)}")
            
            # 날짜 컬럼 확인
            if 'date' in processed_df.columns:
                print(f"   처리된 날짜 범위: {processed_df['date'].min()} ~ {processed_df['date'].max()}")
            
            # 결측치 확인
            missing_count = processed_df.isnull().sum().sum()
            print(f"   결측치 개수: {missing_count}")
            
            # 파생변수 확인
            derived_vars = [col for col in processed_df.columns if any(x in col for x in ['_mom', '_ma3', '_diff', '_spread'])]
            print(f"   파생변수 개수: {len(derived_vars)}")
            if len(derived_vars) > 0:
                print(f"   파생변수 예시: {derived_vars[:5]}")
            
            return processed_df
        else:
            print("❌ load_ecos_data() 실패")
            return None
            
    except Exception as e:
        print(f"❌ 전처리 함수 테스트 실패: {e}")
        return None

def test_full_pipeline(filepath='ecos_data.csv'):
    """전체 파이프라인 테스트"""
    print("\n=== 전체 파이프라인 테스트 ===")
    
    try:
        # 전체 전처리 파이프라인 실행
        print("preprocess_ecos_data() 실행...")
        result = preprocess_ecos_data(filepath)
        
        if result is not None:
            print("✅ 전체 파이프라인 성공!")
            print(f"   X 데이터 형태: {result['data_shape']}")
            print(f"   y 데이터 형태: {result['target_shape']}")
            print(f"   선택된 피쳐 수: {len(result['features'])}")
            print(f"   타겟 변수 수: {len(result['targets'])}")
            print(f"   데이터 기간: {result['date_range']}")
            
            print(f"\n   타겟 변수들: {result['targets']}")
            print(f"   상위 5개 피쳐: {result['features'][:5]}")
            
            # 상관관계 정보
            if len(result['correlation']) > 0:
                print(f"   최고 상관관계: {result['correlation'].iloc[0]:.3f}")
            
            return result
        else:
            print("❌ 전체 파이프라인 실패")
            return None
            
    except Exception as e:
        print(f"❌ 전체 파이프라인 테스트 실패: {e}")
        return None

def test_api_function(filepath='ecos_data.csv'):
    """API 함수 테스트"""
    print("\n=== API 함수 테스트 ===")
    
    try:
        result = preprocess_for_api(filepath)
        
        if result['status'] == 'success':
            print("✅ API 함수 성공!")
            print(f"   상태: {result['status']}")
            print(f"   데이터 형태: {result['data_shape']}")
            print(f"   타겟 형태: {result['target_shape']}")
            print(f"   피쳐 수: {result['n_features']}")
            print(f"   타겟 수: {result['n_targets']}")
            print(f"   데이터 기간: {result['date_range']}")
            return result
        else:
            print(f"❌ API 함수 실패: {result['message']}")
            return None
            
    except Exception as e:
        print(f"❌ API 함수 테스트 실패: {e}")
        return None

def run_all_tests(filepath='ecos_data.csv'):
    """모든 테스트 실행"""
    print("=" * 60)
    print("ECOS 데이터 전처리 함수 테스트 시작")
    print("=" * 60)
    
    # 1. 파일 존재 확인
    if not test_file_exists(filepath):
        return False
    
    # 2. 기본 로드 테스트
    original_df = test_basic_load(filepath)
    if original_df is None:
        return False
    
    # 3. 전처리 함수 테스트
    processed_df = test_preprocessing_functions(filepath)
    if processed_df is None:
        return False
    
    # 4. 전체 파이프라인 테스트
    pipeline_result = test_full_pipeline(filepath)
    if pipeline_result is None:
        return False
    
    # 5. API 함수 테스트
    api_result = test_api_function(filepath)
    if api_result is None:
        return False
    
    print("\n" + "=" * 60)
    print("✅ 모든 테스트 통과!")
    print("   전처리 함수들이 정상적으로 작동합니다.")
    print("   FastAPI에서 사용할 준비가 완료되었습니다.")
    print("=" * 60)
    
    return True

def check_dependencies():
    """필요한 라이브러리 확인"""
    print("=== 의존성 라이브러리 확인 ===")
    
    required_libs = ['pandas', 'numpy', 'matplotlib', 'sklearn']
    missing_libs = []
    
    for lib in required_libs:
        try:
            __import__(lib)
            print(f"✅ {lib}")
        except ImportError:
            print(f"❌ {lib} - 설치 필요")
            missing_libs.append(lib)
    
    if missing_libs:
        print(f"\n설치 명령어: pip install {' '.join(missing_libs)}")
        return False
    
    print("✅ 모든 의존성 라이브러리 확인 완료")
    return True

if __name__ == "__main__":
    # 의존성 확인
    if not check_dependencies():
        print("필요한 라이브러리를 먼저 설치해주세요.")
        sys.exit(1)
    
    # 파일 경로 설정
    csv_file = 'ecos_data.csv'
    
    # 명령행 인자가 있으면 사용
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    
    print(f"사용할 파일: {csv_file}")
    
    # 전체 테스트 실행
    success = run_all_tests(csv_file)
    
    if success:
        print("\n🎉 테스트 완료! 전처리 시스템이 정상 작동합니다.")
    else:
        print("\n❌ 테스트 실패. 문제를 확인해주세요.")
        sys.exit(1)