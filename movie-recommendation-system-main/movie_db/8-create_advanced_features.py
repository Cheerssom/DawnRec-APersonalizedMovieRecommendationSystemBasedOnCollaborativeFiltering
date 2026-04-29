import pymysql

# 数据库连接
try:
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="123456",
        database="movie_system",
        charset="utf8mb4"
    )
    cursor = conn.cursor()
    print("✅ 数据库连接成功！")
except pymysql.MySQLError as e:
    print("❌ 数据库连接失败！错误信息：", e)
    exit(1)

commands = []

# 1. 数据库中有图片类型数据或存储文件类型数据 (ALTER TABLE)
commands.append({
    "desc": "添加电影海报图片字段",
    "sql": "ALTER TABLE movie ADD COLUMN poster_url VARCHAR(500) COMMENT '电影海报图片链接';"
})
commands.append({
    "desc": "添加用户头像图片字段",
    "sql": "ALTER TABLE user ADD COLUMN avatar_url VARCHAR(500) COMMENT '用户头像文件路径';"
})

# 2. 数据库表上建立合适的索引
commands.append({
    "desc": "在电影表的上映年份建立索引",
    "sql": "CREATE INDEX idx_movie_release_year ON movie(release_year);"
})
commands.append({
    "desc": "在用户表的注册时间建立索引",
    "sql": "CREATE INDEX idx_user_register_date ON user(register_date);"
})

# 3. 创建视图查询信息
commands.append({
    "desc": "删除旧视图",
    "sql": "DROP VIEW IF EXISTS v_movie_details;"
})
commands.append({
    "desc": "创建视图：电影详细信息视图",
    "sql": """
    CREATE VIEW v_movie_details AS
    SELECT m.movie_id, m.title, m.release_year, m.language, m.duration, m.director, m.avg_score, m.rating_count, m.poster_url,
           GROUP_CONCAT(g.genre_name SEPARATOR ', ') AS genres
    FROM movie m
    LEFT JOIN movie_genre mg ON m.movie_id = mg.movie_id
    LEFT JOIN genre g ON mg.genre_id = g.genre_id
    GROUP BY m.movie_id;
    """
})

# 4. 创建存储过程统计数据表中的信息或其他功能
commands.append({
    "desc": "删除旧存储过程",
    "sql": "DROP PROCEDURE IF EXISTS sp_get_user_stats;"
})
commands.append({
    "desc": "创建存储过程：获取用户统计信息",
    "sql": """
    CREATE PROCEDURE sp_get_user_stats(IN p_user_id INT, OUT p_total_ratings INT, OUT p_total_history INT)
    BEGIN
        SELECT COUNT(*) INTO p_total_ratings FROM rating WHERE user_id = p_user_id;
        SELECT COUNT(*) INTO p_total_history FROM history WHERE user_id = p_user_id;
    END;
    """
})

# 5. 创建触发器，实现表中状态自动修改
commands.append({
    "desc": "删除旧触发器（插入评分后）",
    "sql": "DROP TRIGGER IF EXISTS trg_after_rating_insert;"
})
commands.append({
    "desc": "创建触发器：插入评分后自动更新电影平均分和评分人数",
    "sql": """
    CREATE TRIGGER trg_after_rating_insert
    AFTER INSERT ON rating
    FOR EACH ROW
    BEGIN
        UPDATE movie 
        SET rating_count = rating_count + 1,
            avg_score = ((avg_score * (rating_count - 1)) + NEW.score) / rating_count
        WHERE movie_id = NEW.movie_id;
    END;
    """
})

commands.append({
    "desc": "删除旧触发器（更新评分后）",
    "sql": "DROP TRIGGER IF EXISTS trg_after_rating_update;"
})
commands.append({
    "desc": "创建触发器：更新评分后自动更新电影平均分",
    "sql": """
    CREATE TRIGGER trg_after_rating_update
    AFTER UPDATE ON rating
    FOR EACH ROW
    BEGIN
        IF OLD.score != NEW.score THEN
            UPDATE movie 
            SET avg_score = ((avg_score * rating_count) - OLD.score + NEW.score) / rating_count
            WHERE movie_id = NEW.movie_id;
        END IF;
    END;
    """
})


for cmd in commands:
    try:
        cursor.execute(cmd["sql"])
        print(f"✅ 成功: {cmd['desc']}")
    except pymysql.MySQLError as e:
        # Ignore duplicate column/index errors to make script idempotent
        if e.args[0] in (1060, 1061): 
            print(f"⚠️ 已存在: {cmd['desc']}")
        else:
            print(f"❌ 失败: {cmd['desc']} - 错误信息: {e}")

# 提交事务并关闭连接
conn.commit()
cursor.close()
conn.close()
print("🎉 高级数据库特性创建完成！")
