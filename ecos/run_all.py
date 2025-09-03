import subprocess
import sys
import os

def run_script(script_name, description):
    """스크립트 실행"""
    print(f"\n {description}")
    print("=" * 50)
    
    if not os.path.exists(script_name):
        print(f" 파일을 찾을 수 없습니다: {script_name}")
        return False
        
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            print(" 성공!")
            if result.stdout:
                print(result.stdout[-500:])  # 마지막 500자만 출력
            return True
        else:
            print(" 실패!")
            if result.stderr:
                print(result.stderr[-500:])  # 마지막 500자만 출력
            return False
    except Exception as e:
        print(f" 오류: {e}")
        return False

if __name__ == "__main__":
    print("한국 경제지표 데이터 수집 및 통합")
    
    # 1. 데이터 수집
    success1 = run_script("ECOS_data.py", "ECOS 데이터 수집")
    
    # 2. DataFrame 생성 (데이터 수집이 성공한 경우에만)
    if success1 or os.path.exists("economic_data"):
        success2 = run_script("Create_dataframe.py", "DataFrame 통합")
        
        if success2:
            print("\n 모든 작업 완료!")
            print(" 생성된 파일: economic_data_merged.csv")
        else:
            print("\n DataFrame 생성 실패")
    else:
        print("\n데이터 수집 실패로 인해 DataFrame 생성을 건너뜁니다")
