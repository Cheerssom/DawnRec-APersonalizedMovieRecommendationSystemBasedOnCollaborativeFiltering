import pymysql

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "123456",
    "database": "movie_system",
    "charset": "utf8mb4"
}

# 定义每张表的主键和判断重复的逻辑列
tables_to_clean = [
    {"table": "movie", "pk": "movie_id", "unique_cols": "title"},
    {"table": "genre", "pk": "genre_id", "unique_cols": "genre_name"},
    {"table": "user", "pk": "user_id", "unique_cols": "username"},
    {"table": "rating", "pk": "rating_id", "unique_cols": "user_id, movie_id"},
    {"table": "history", "pk": "history_id", "unique_cols": "user_id, movie_id, watch_time"}
]

def clean_all_duplicates():
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        print("🚀 开始清理整个数据库的重复数据...")
        print("-" * 50)
        
        for t in tables_to_clean:
            table = t["table"]
            pk = t["pk"]
            unique_cols = t["unique_cols"]
            
            # 获取清理前的总数
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            total_before = cursor.fetchone()[0]
            
            if total_before == 0:
                print(f"✨ 表 `{table}` 为空，跳过检查。")
                continue
                
            # 执行去重逻辑：按判断重复的列分组，保留每组里最小的 PK
            delete_sql = f"""
            DELETE FROM {table} 
            WHERE {pk} NOT IN (
                SELECT min_id FROM (
                    SELECT MIN({pk}) as min_id 
                    FROM {table} 
                    GROUP BY {unique_cols}
                ) as tmp
            )
            """
            cursor.execute(delete_sql)
            deleted_count = cursor.rowcount
            conn.commit()
            
            # 获取清理后的总数
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            total_after = cursor.fetchone()[0]
            
            if deleted_count > 0:
                print(f"✅ 表 `{table}` 清理完成: 删除了 {deleted_count} 条重复记录 (剩余: {total_after} 条)")
            else:
                print(f"✨ 表 `{table}` 无重复数据 (共 {total_after} 条)")
                
        print("-" * 50)
        print("🎉 所有表的重复数据检查和清理工作已完成！")
        
    except pymysql.MySQLError as e:
        print("❌ 清理失败，错误:", e)
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    clean_all_duplicates()
