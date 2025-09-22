import mysql.connector
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

def test_mysql_connection():
    """MySQL 연결 테스트"""
    try:
        # 먼저 데이터베이스 없이 연결 시도
        config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'charset': 'utf8mb4'
        }
        
        print("MySQL 서버 연결 시도...")
        connection = mysql.connector.connect(**config)
        print("✓ MySQL 서버 연결 성공!")
        
        cursor = connection.cursor()
        
        # 데이터베이스 생성
        cursor.execute("CREATE DATABASE IF NOT EXISTS IE_project")
        print("✓ 데이터베이스 IE_project 생성/확인 완료")
        
        # 데이터베이스 선택
        cursor.execute("USE IE_project")
        print("✓ 데이터베이스 IE_project 선택 완료")
        
        # 테이블 목록 확인
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✓ 현재 테이블 수: {len(tables)}")
        
        cursor.close()
        connection.close()
        
        # 이제 데이터베이스 포함한 연결 시도
        config['database'] = 'IE_project'
        connection = mysql.connector.connect(**config)
        print("✓ IE_project 데이터베이스로 연결 성공!")
        
        connection.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"✗ MySQL 연결 오류: {e}")
        return False
    except Exception as e:
        print(f"✗ 예상치 못한 오류: {e}")
        return False

if __name__ == "__main__":
    success = test_mysql_connection()
    if success:
        print("\n🎉 MySQL 연결 테스트 성공!")
    else:
        print("\n❌ MySQL 연결 테스트 실패!")