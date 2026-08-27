import os
import pandas as pd
import datetime as dt
from sqlalchemy import create_engine


def get_data_sqlserver(sql: str):
    connection_string = 'mssql+pyodbc://aro:v93jfe8k@10.1.55.18/Filesync?driver=ODBC+Driver+18+for+SQL+Server&AutoTranslate=yes&TrustServerCertificate=yes'
    engine = create_engine(connection_string)
            
    with engine.connect() as connection:
        df = pd.read_sql_query(sql, connection)
        
    return df

def subtract_milliseconds(time_str, milliseconds):
    try:
        # 解析时间字符
        if '.' not in time_str:
            time_str = time_str + '.000'
        
        time_obj = dt.datetime.strptime(time_str, "%H:%M:%S.%f")
        # 减去毫秒
        delta = dt.timedelta(milliseconds=milliseconds)
        result = time_obj - delta
        
        # 格式化为字符串
        return result.strftime("%H:%M:%S.%f")[:-3]
    
    except ValueError as e:
        raise ValueError(f"无效的时间格式或毫秒数: {e}")