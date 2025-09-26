
import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv

# 환경변수 로드 (현재 파일의 디렉토리에서 .env 찾기)
current_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(current_dir, '.env')
load_dotenv(dotenv_path)

class DatabaseConnection:
    """MySQL 데이터베이스 연결 클래스"""
    
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ie_project'),
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
        """ECOS 경제지표 데이터 조회 (시스템 컬럼 제외)"""
        query = """
        SELECT date, base_rate, ccsi, construction_bsi_actual, construction_bsi_forecast,
               cpi, esi, exchange_usd_krw_close, housing_lease_price, housing_sale_price,
               import_price_non_metal_mineral, import_price_steel_primary, leading_index,
               m2_growth, market_rate_treasury_bond_10yr, market_rate_treasury_bond_3yr,
               market_rate_corporate_bond_3yr_AA, market_rate_corporate_bond_3yr_BBB,
               ppi_non_metal_mineral, ppi_steel_primary
        FROM ecos_data 
        ORDER BY date
        """
        return self.execute_query(query)
    
    def get_dart_data(self):
        """DART 재무데이터 조회 (시스템 컬럼 제외)"""
        query = """
        SELECT corp_name, corp_code, year, quarter, report_date,
               total_assets, total_liabilities, total_equity, revenue,
               operating_profit, quarterly_profit
        FROM dart_data 
        ORDER BY corp_name, year, quarter
        """
        return self.execute_query(query)
    
    def get_final_features(self):
        """최종 피쳐 데이터 조회 (시스템 컬럼 제외)"""
        query = """
        SELECT date, construction_bsi_actual_diff, housing_sale_price_diff, m2_growth_diff,
               credit_spread_diff, base_rate_diff, construction_bsi_mom, housing_sale_price_diff_ma3,
               m2_growth_lag1, base_rate_mdiff_bp, credit_spread_diff_ma3, construction_bsi_ma3,
               leading_index, housing_sale_price_diff_lag6, construction_bsi_actual_lag3,
               construction_bsi_actual_diff_ma3, base_rate_diff_ma6, term_spread,
               construction_bsi_actual_diff_ma6, credit_spread_diff_lag1, market_rate_treasury_bond_3yr,
               credit_spread_diff_ma6, base_rate_diff_ma3, base_rate_lag1, esi,
               base_rate_diff_lag3, m2_growth_diff_ma6
        FROM final_features 
        ORDER BY date
        """
        return self.execute_query(query)
    
    def get_model_output(self):
        """모델 예측 결과 조회 (시스템 컬럼 제외)"""
        query = """
        SELECT date, construction_bsi_actual, base_rate, housing_sale_price,
               m2_growth, credit_spread
        FROM model_output 
        ORDER BY date
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
    
    def save_final_features(self, features_df):
        """최종 피쳐를 final_features 테이블에 저장"""
        if not self.connection:
            print("데이터베이스에 연결되지 않았습니다.")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # 기존 데이터 삭제 (같은 날짜)
            for _, row in features_df.iterrows():
                delete_query = "DELETE FROM final_features WHERE date = %s"
                cursor.execute(delete_query, (row['date'],))
            
            # 새 데이터 삽입
            insert_query = """
            INSERT INTO final_features 
            (date, construction_bsi_actual_diff, housing_sale_price_diff, m2_growth_diff,
             credit_spread_diff, base_rate_diff, construction_bsi_mom, housing_sale_price_diff_ma3,
             m2_growth_lag1, base_rate_mdiff_bp, credit_spread_diff_ma3, construction_bsi_ma3,
             leading_index, housing_sale_price_diff_lag6, construction_bsi_actual_lag3,
             construction_bsi_actual_diff_ma3, base_rate_diff_ma6, term_spread,
             construction_bsi_actual_diff_ma6, credit_spread_diff_lag1, market_rate_treasury_bond_3yr,
             credit_spread_diff_ma6, base_rate_diff_ma3, base_rate_lag1, esi,
             base_rate_diff_lag3, m2_growth_diff_ma6)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for _, row in features_df.iterrows():
                values = (
                    row.get('date', ''),
                    row.get('construction_bsi_actual_diff'),
                    row.get('housing_sale_price_diff'),
                    row.get('m2_growth_diff'),
                    row.get('credit_spread_diff'),
                    row.get('base_rate_diff'),
                    row.get('construction_bsi_mom'),
                    row.get('housing_sale_price_diff_ma3'),
                    row.get('m2_growth_lag1'),
                    row.get('base_rate_mdiff_bp'),
                    row.get('credit_spread_diff_ma3'),
                    row.get('construction_bsi_ma3'),
                    row.get('leading_index'),
                    row.get('housing_sale_price_diff_lag6'),
                    row.get('construction_bsi_actual_lag3'),
                    row.get('construction_bsi_actual_diff_ma3'),
                    row.get('base_rate_diff_ma6'),
                    row.get('term_spread'),
                    row.get('construction_bsi_actual_diff_ma6'),
                    row.get('credit_spread_diff_lag1'),
                    row.get('market_rate_treasury_bond_3yr'),
                    row.get('credit_spread_diff_ma6'),
                    row.get('base_rate_diff_ma3'),
                    row.get('base_rate_lag1'),
                    row.get('esi'),
                    row.get('base_rate_diff_lag3'),
                    row.get('m2_growth_diff_ma6')
                )
                cursor.execute(insert_query, values)
            
            self.connection.commit()
            cursor.close()
            print(f"피쳐 데이터 {len(features_df)}건 저장 완료")
            return True
            
        except mysql.connector.Error as e:
            print(f"피쳐 데이터 저장 오류: {e}")
            return False
    
    def save_model_output(self, predictions_df):
        """모델 예측 결과를 model_output 테이블에 저장"""
        if not self.connection:
            print("데이터베이스에 연결되지 않았습니다.")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # 기존 데이터 삭제 (같은 날짜)
            for _, row in predictions_df.iterrows():
                delete_query = "DELETE FROM model_output WHERE date = %s"
                cursor.execute(delete_query, (row['date'],))
            
            # 새 데이터 삽입
            insert_query = """
            INSERT INTO model_output 
            (date, construction_bsi_actual, base_rate, housing_sale_price, m2_growth, credit_spread)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            for _, row in predictions_df.iterrows():
                values = (
                    row.get('date', ''),
                    row.get('construction_bsi_actual'),
                    row.get('base_rate'),
                    row.get('housing_sale_price'),
                    row.get('m2_growth'),
                    row.get('credit_spread')
                )
                cursor.execute(insert_query, values)
            
            self.connection.commit()
            cursor.close()
            print(f"모델 예측 결과 {len(predictions_df)}건 저장 완료")
            return True
            
        except mysql.connector.Error as e:
            print(f"모델 예측 결과 저장 오류: {e}")
            return False
    

