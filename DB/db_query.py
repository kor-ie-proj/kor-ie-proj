import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

class DatabaseConnection:
    """MySQL 데이터베이스 연결 클래스"""
    
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'IE_project'),
            'charset': 'utf8mb4'
        }
        self.connection = None
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            print("MySQL 데이터베이스 연결 성공")
            return True
        except mysql.connector.Error as e:
            print(f"MySQL 연결 오류: {e}")
            return False
    
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection:
            self.connection.close()
            print("MySQL 연결 해제")
    
    def execute_query(self, query):
        """쿼리 실행"""
        if not self.connection:
            print("데이터베이스에 연결되지 않았습니다.")
            return None
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            cursor.close()
            return pd.DataFrame(result, columns=columns)
        except mysql.connector.Error as e:
            print(f"쿼리 실행 오류: {e}")
            return None
    
    def get_ecos_data(self):
        """ECOS 경제지표 데이터 조회"""
        query = """
        SELECT * FROM ecos_data 
        ORDER BY date
        """
        return self.execute_query(query)
    
    def get_dart_data(self):
        """DART 재무데이터 조회"""
        query = """
        SELECT * FROM dart_data 
        ORDER BY corp_name, year, quarter
        """
        return self.execute_query(query)
    
    def insert_prediction_results(self, predictions_df):
        """예측 결과 데이터 삽입"""
        if not self.connection:
            print("데이터베이스에 연결되지 않았습니다.")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # 기존 데이터 삭제 (같은 예측 분기)
            delete_query = """
            DELETE FROM prediction_results 
            WHERE prediction_quarter = %s
            """
            
            if 'prediction_quarter' in predictions_df.columns:
                quarter = predictions_df['prediction_quarter'].iloc[0]
                cursor.execute(delete_query, (quarter,))
            
            # 새 데이터 삽입
            insert_query = """
            INSERT INTO prediction_results 
            (corp_name, prediction_quarter, prediction_date, 
             predicted_total_assets, predicted_total_liabilities, predicted_total_equity,
             predicted_revenue, predicted_operating_profit, predicted_quarterly_profit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for _, row in predictions_df.iterrows():
                values = (
                    row.get('corp_name', ''),
                    row.get('prediction_quarter', ''),
                    row.get('prediction_date', ''),
                    row.get('predicted_total_assets', 0),
                    row.get('predicted_total_liabilities', 0),
                    row.get('predicted_total_equity', 0),
                    row.get('predicted_revenue', 0),
                    row.get('predicted_operating_profit', 0),
                    row.get('predicted_quarterly_profit', 0)
                )
                cursor.execute(insert_query, values)
            
            self.connection.commit()
            cursor.close()
            print(f"예측 결과 {len(predictions_df)}건 저장 완료")
            return True
        
            
        except mysql.connector.Error as e:
            print(f"데이터 삽입 오류: {e}")
            return False
