import pandas as pd
import os

def create_economic_dataframe():
    """경제 데이터를 하나의 DataFrame으로 통합"""
    
    data_folder = "economic_data"
    
    # 수입물가지수 제외
    exclude_files = ["import_price_철강1차제품.csv", "import_price_비금속광물.csv"]
    csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv') and f not in exclude_files]
    
    merged_data = {}
    
    # 각 파일 처리
    for file in csv_files:
        df = pd.read_csv(os.path.join(data_folder, file), encoding='utf-8-sig')
        var_name = file.replace('.csv', '')
        
        for _, row in df.iterrows():
            date = str(row['date'])
            if len(date) == 6 and date.isdigit():
                if date not in merged_data:
                    merged_data[date] = {}
                merged_data[date][var_name] = row['value']
    
    # DataFrame 생성
    df_data = []
    for date in sorted(merged_data.keys()):
        row_data = {'date': date}
        row_data.update(merged_data[date])
        df_data.append(row_data)
    
    final_df = pd.DataFrame(df_data)
    columns = ['date'] + sorted([col for col in final_df.columns if col != 'date'])
    final_df = final_df[columns].set_index('date')
    
    return final_df

if __name__ == "__main__":
    df = create_economic_dataframe()
    df.to_csv("economic_data_merged.csv", encoding='utf-8-sig')
    print(f"DataFrame 생성 완료: {df.shape}")
    print("컬럼:", list(df.columns))
