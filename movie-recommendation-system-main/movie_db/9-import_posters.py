import pymysql
import requests
import time
import re
from urllib.parse import quote

def fetch_poster_from_bing(title):
    """
    通过必应图片搜索获取电影海报
    """
    # 构造搜索关键词，加上"电影海报"以提高准确率
    search_term = quote(f"{title} 电影海报")
    url = f"https://cn.bing.com/images/search?q={search_term}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            # 必应图片的原始 URL 存储在 murl&quot;:&quot;...&quot; 结构中
            match = re.search(r'murl&quot;:&quot;(.*?)&quot;', response.text)
            if match:
                # 必应的 URL 有时可能会有额外的转义，直接使用 match 的结果即可
                return match.group(1)
    except Exception as e:
        print(f"    获取 {title} 海报时出错: {e}")
        
    return None

def main():
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="123456",
            database="movie_system",
            charset="utf8mb4"
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        print("✅ 数据库连接成功！")
        
        # 获取所有电影
        cursor.execute("SELECT movie_id, title FROM movie")
        movies = cursor.fetchall()
        
        print(f"🎬 找到 {len(movies)} 部电影，开始通过必应搜索真实海报...")
        
        update_sql = "UPDATE movie SET poster_url = %s WHERE movie_id = %s"
        success_count = 0
        fail_count = 0
        
        for movie in movies:
            movie_id = movie['movie_id']
            title = movie['title']
            
            # 去除可能包含的年份后缀或特殊字符以提高搜索准确率
            search_title = title.split('（')[0].split('(')[0].strip()
            
            print(f"  正在搜索: {search_title} ...", end="", flush=True)
            
            poster_url = fetch_poster_from_bing(search_title)
            
            if poster_url:
                cursor.execute(update_sql, (poster_url, movie_id))
                conn.commit()
                print(f" [成功]")
                success_count += 1
            else:
                print(" [失败] 未找到海报")
                fail_count += 1
                
            # 休眠一下，防止请求过快被封IP
            time.sleep(0.5)
            
        print(f"\n🎉 导入完成！成功更新 {success_count} 部电影海报，失败 {fail_count} 部。")

    except pymysql.MySQLError as e:
        print("❌ 数据库操作失败！错误信息：", e)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
