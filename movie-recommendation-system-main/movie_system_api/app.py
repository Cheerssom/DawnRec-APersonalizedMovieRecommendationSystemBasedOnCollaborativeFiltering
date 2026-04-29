from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from flask_cors import CORS
import requests
import json
from models import movie as movie_model
from models import user as user_model
from models import rating as rating_model
from models import history as history_model
try:
    from models import recommendation as recommendation_model
except ImportError:
    import sys
    sys.path.append('models')
    import recommendation as recommendation_model
import hashlib
import pymysql
import os
from dotenv import load_dotenv
from db_config import get_connection

# 加载 .env 文件中的环境变量
load_dotenv()

from datetime import timedelta
app = Flask(__name__)
app.secret_key = "secret_key_123"  # session 必需
app.permanent_session_lifetime = timedelta(days=7)  # 设置会话有效期为7天
CORS(app)

@app.before_request
def make_session_permanent():
    session.permanent = True

import functools
import time
from flask import g

# 密码加密函数
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# 添加缓存装饰器
def cache_response(timeout=300):  # 5分钟缓存
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(kwargs)}"

            # 检查缓存
            cache = getattr(g, '_cache', {})
            if cache_key in cache:
                cached_data, timestamp = cache[cache_key]
                if time.time() - timestamp < timeout:
                    return cached_data

            # 执行函数
            result = func(*args, **kwargs)

            # 缓存结果
            if not hasattr(g, '_cache'):
                g._cache = {}
            g._cache[cache_key] = (result, time.time())

            return result

        return wrapper

    return decorator

# =======================
# 页面路由
# =======================
@app.route("/")
def login_page():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=['GET'])
def register_page():
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login_page"))
    return render_template("dashboard/index.html")


@app.route("/movies")
def movies_page():
    if not session.get("user_id"):
        return redirect(url_for("login_page"))
    return render_template("dashboard/movies.html")


@app.route("/users")
def users_page():
    if not session.get("user_id"):
        return redirect(url_for("login_page"))
    return render_template("dashboard/users.html")


@app.route("/ratings")
def ratings_page():
    if not session.get("user_id"):
        return redirect(url_for("login_page"))
    return render_template("dashboard/ratings.html")


@app.route("/history")
def history_page():
    if not session.get("user_id"):
        return redirect(url_for("login_page"))
    return render_template("dashboard/history.html")


# =======================
# 登录注册 API
# =======================
@app.route("/api/login", methods=["POST"])
def login():
    try:
        # 检查请求内容类型
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            # 如果是从表单提交，使用form数据
            data = request.form

        username = data.get("username")
        password = data.get("password")

        print(f"登录尝试 - 用户名: {username}")

        if not username or not password:
            return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400

        user = user_model.get_user_by_username(username)
        if user and user.get("password_hash") == hash_password(password):
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            print(f"登录成功 - 用户ID: {user['user_id']}")
            return jsonify({"success": True, "message": "登录成功"})
        else:
            print("登录失败 - 用户名或密码错误")
            return jsonify({"success": False, "message": "用户名或密码错误"}), 401
    except Exception as e:
        print(f"登录异常: {str(e)}")
        return jsonify({"success": False, "message": f"登录失败: {str(e)}"}), 500


@app.route("/api/register", methods=["POST"])
def register():
    try:
        print("收到注册请求")

        # 检查请求内容类型
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            # 如果是从表单提交，使用form数据
            data = request.form.to_dict()

        print(f"注册数据: {data}")

        username = data.get("username")
        password = data.get("password")
        nickname = data.get("nickname")
        age = data.get("age")
        gender = data.get("gender")

        if not username or not password:
            return jsonify({"success": False, "message": "用户名和密码不能为空"}), 400

        if len(username) < 3:
            return jsonify({"success": False, "message": "用户名至少需要3个字符"}), 400

        if len(password) < 6:
            return jsonify({"success": False, "message": "密码至少需要6个字符"}), 400

        # 检查用户名是否已存在
        existing_user = user_model.get_user_by_username(username)
        if existing_user:
            return jsonify({"success": False, "message": "用户名已存在"}), 400

        # 处理年龄字段
        if age:
            try:
                age = int(age)
            except ValueError:
                age = None

        # 添加用户
        user_id = user_model.add_user(
            username=username,
            password_hash=hash_password(password),
            nickname=nickname,
            age=age,
            gender=gender
        )

        if user_id:
            session["user_id"] = user_id
            session["username"] = username
            print(f"注册成功 - 用户ID: {user_id}")
            return jsonify({"success": True, "message": "注册成功"})
        else:
            print("注册失败 - 数据库插入失败")
            return jsonify({"success": False, "message": "注册失败"}), 500

    except Exception as e:
        print(f"注册异常: {str(e)}")
        return jsonify({"success": False, "message": f"注册失败: {str(e)}"}), 500


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("您已成功退出登录", "success")
    return redirect(url_for("login_page"))

# =======================
# AI Assistant API
# =======================
@app.route("/api/ai/chat", methods=["POST"])
def ai_chat():
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        data = request.json
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({"error": "消息不能为空"}), 400

        # DeepSeek API 配置
        api_key = os.environ.get("DEEPSEEK_API_KEY", "your_default_api_key_here")
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # 获取用户的观影偏好和历史记录
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取用户最高评分的电影（最多5部）
        cursor.execute("""
            SELECT m.title, m.director, r.score 
            FROM rating r 
            JOIN movie m ON r.movie_id = m.movie_id 
            WHERE r.user_id = %s AND r.score >= 4 
            ORDER BY r.score DESC, r.rating_time DESC 
            LIMIT 5
        """, (session.get("user_id"),))
        top_ratings = cursor.fetchall()
        
        # 获取用户最近观看的电影（最多5部）
        cursor.execute("""
            SELECT m.title, m.director
            FROM history h
            JOIN movie m ON h.movie_id = m.movie_id
            WHERE h.user_id = %s
            ORDER BY h.watch_time DESC
            LIMIT 5
        """, (session.get("user_id"),))
        recent_history = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 组装用户画像
        user_profile = ""
        if top_ratings:
            user_profile += "用户打高分(>=4分)的电影有：\n"
            for r in top_ratings:
                user_profile += f"- 《{r['title']}》(评分: {r['score']})\n"
        if recent_history:
            user_profile += "用户最近看过的电影有：\n"
            for h in recent_history:
                user_profile += f"- 《{h['title']}》\n"
                
        if not user_profile:
            user_profile = "用户目前还没有观影历史或评分记录。"

        # 构建发送给大模型的 Prompt
        system_prompt = f"""你是一个基于Flask+MySQL开发的电影推荐系统专属AI助手。
请用热情、专业的语气回答用户的电影相关问题。
你可以调用 search_movies 工具来查询数据库中的真实电影。
你的主要职责是：
1. 帮用户找电影，推荐电影时尽量给出推荐理由。如果是查询请求，必须使用工具查询真实数据库中的电影再推荐，不要凭空编造不存在系统里的电影。
2. 回答关于电影的常识、演员、导演等问题。
3. 语气保持活泼，使用一些 emoji。
4. 如果用户的问题完全与电影无关，请委婉地将话题引导回电影推荐上。
5. 【重要】生成专属推荐语：在推荐电影时，请结合下方提供的【当前用户观影画像】，生成非常个性化的推荐理由。
6. 【核心】模糊剧情搜索策略：当用户输入模糊的剧情描述时，**千万不要**直接把描述作为 keyword 搜索！你必须先用你的知识推断出具体的电影名称（因为数据库以英文片名为主，请优先转成英文原名），然后把推断出的具体电影名作为 keyword 调用 search_movies 检查是否在数据库中。如果数据库没有，请向用户说明。

【当前用户观影画像】
{user_profile}"""

        # 定义可用的工具
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_movies",
                    "description": "搜索系统数据库中的电影。如果是剧情描述，请务必先推断出具体电影名称（最好是英文名）再作为关键词传入。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {
                                "type": "string",
                                "description": "具体的电影名称（建议英文原名）或导演名。绝不能是一长串的剧情描述！"
                            },
                            "year": {
                                "type": "integer",
                                "description": "电影上映年份，比如 2024, 1994"
                            },
                            "genre": {
                                "type": "string",
                                "description": "电影类型，比如 '科幻', '喜剧', '动作'"
                            }
                        }
                    }
                }
            }
        ]

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "tools": tools,
            "temperature": 0.7,
            "max_tokens": 1500
        }

        # 第一次请求大模型
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            error_msg = response.json().get('error', {}).get('message', '未知错误')
            return jsonify({"error": f"AI服务响应失败: {error_msg}"}), 500

        result = response.json()
        message = result['choices'][0]['message']

        # 检查大模型是否想调用工具
        if message.get("tool_calls"):
            messages.append(message)  # 把大模型的回复（包含 tool_calls）加到上下文

            for tool_call in message["tool_calls"]:
                if tool_call["function"]["name"] == "search_movies":
                    args = json.loads(tool_call["function"]["arguments"])
                    
                    # 获取本地所有电影并使用 Python 过滤
                    all_movies = movie_model.get_all_movies()
                    filtered = all_movies
                    
                    kw = args.get("keyword")
                    if kw:
                        kw = kw.lower()
                        filtered = [m for m in filtered if kw in m.get("title", "").lower() or kw in m.get("director", "").lower() or kw in m.get("description", "").lower()]
                    
                    yr = args.get("year")
                    if yr:
                        filtered = [m for m in filtered if m.get("release_year") == yr]
                        
                    gn = args.get("genre")
                    if gn:
                        gn = gn.lower()
                        filtered = [m for m in filtered if any(gn in g.lower() for g in m.get("genres", []))]
                    
                    # 为了防止返回内容过大，最多返回10条
                    filtered = filtered[:10]
                    
                    # 简化字段，节省 token
                    simplified_movies = []
                    for m in filtered:
                        simplified_movies.append({
                            "title": m.get("title"),
                            "year": m.get("release_year"),
                            "director": m.get("director"),
                            "genres": m.get("genres"),
                            "score": m.get("avg_score"),
                            "description": m.get("description")
                        })
                        
                    tool_result_str = json.dumps(simplified_movies, ensure_ascii=False)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result_str
                    })

            # 将工具执行结果发送回大模型
            second_payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1500
            }
            second_response = requests.post(url, headers=headers, json=second_payload, timeout=30)
            if second_response.status_code != 200:
                error_msg = second_response.json().get('error', {}).get('message', '未知错误')
                return jsonify({"error": f"AI工具调用响应失败: {error_msg}"}), 500
            
            final_reply = second_response.json()['choices'][0]['message']['content']
            return jsonify({"reply": final_reply})
        
        else:
            # 如果没有调用工具，直接返回大模型的回复
            return jsonify({"reply": message["content"]})

    except requests.exceptions.Timeout:
        return jsonify({"error": "AI服务请求超时，请稍后再试"}), 504
    except Exception as e:
        print(f"AI聊天服务错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "内部服务器错误"}), 500

# =======================
# Dashboard API
# =======================
@app.route("/api/dashboard/stats")
def dashboard_stats():
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        print("开始获取仪表盘统计数据...")

        # 添加数据库连接检查
        try:
            test_conn = get_connection()
            if test_conn is None:
                return jsonify({"error": "数据库连接失败"}), 500
            test_conn.close()
        except Exception as e:
            print(f"数据库连接测试失败: {str(e)}")
            return jsonify({"error": "数据库连接失败"}), 500

        # 原有的统计代码...
        total_movies = movie_model.get_movies_count()
        total_users = user_model.get_users_count()
        total_ratings = rating_model.get_ratings_count()
        total_history = history_model.get_history_count()

        return jsonify({
            "total_movies": total_movies,
            "total_users": total_users,
            "total_ratings": total_ratings,
            "total_history": total_history
        })
    except Exception as e:
        print(f"获取仪表盘统计数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# =======================
# Movie API
# =======================

@app.route("/api/movies", methods=["GET"])
def get_movies():
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '')
        year = request.args.get('year', '')
        genre = request.args.get('genre', '')

        print(f"获取电影列表 - 页码: {page}, 搜索: {search}, 年份: {year}, 类型: {genre}")

        # 使用新的搜索方法
        movies, total = movie_model.search_movies(
            search_term=search if search else None,
            year=year if year else None,
            genre_id=genre if genre else None,
            page=page,
            limit=limit
        )

        print(f"查询结果: 找到 {len(movies)} 个电影, 总数: {total}")

        return jsonify({
            "movies": movies,
            "total": total,
            "page": page,
            "limit": limit
        })
    except Exception as e:
        print(f"获取电影列表错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/movies/top")
def get_top_movies():
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        limit = request.args.get('limit', 5, type=int)
        movies = movie_model.get_all_movies()
        # 按评分排序取前N个
        sorted_movies = sorted(movies, key=lambda x: x.get('avg_score', 0), reverse=True)
        return jsonify({"movies": sorted_movies[:limit]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/movies/<int:movie_id>", methods=["GET"])
def get_movie(movie_id):
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        movie = movie_model.get_movie_by_id(movie_id)
        if movie:
            return jsonify(movie)
        return jsonify({"error": "Movie not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/movies", methods=["POST"])
def add_movie():
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        data = request.json
        print(f"添加电影数据: {data}")

        # 验证必需字段
        if not data.get('title'):
            return jsonify({"error": "电影名称不能为空"}), 400

        # 处理类型数据
        genre_ids = data.get('genre_ids', [])
        if isinstance(genre_ids, str):
            genre_ids = [int(id) for id in genre_ids.split(',')] if genre_ids else []

        movie_id = movie_model.add_movie(
            title=data.get('title'),
            release_year=data.get('release_year'),
            language=data.get('language'),
            duration=data.get('duration'),
            director=data.get('director'),
            description=data.get('description'),
            genre_ids=genre_ids
        )

        if movie_id:
            return jsonify({"message": "电影添加成功", "movie_id": movie_id}), 201
        else:
            return jsonify({"error": "添加电影失败"}), 500
    except Exception as e:
        print(f"添加电影异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/movies/<int:movie_id>", methods=["PUT"])
def update_movie(movie_id):
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        data = request.json
        print(f"更新电影数据: {data}")

        # 处理类型数据
        genre_ids = data.get('genre_ids', [])
        if isinstance(genre_ids, str):
            genre_ids = [int(id) for id in genre_ids.split(',')] if genre_ids else []

        rows = movie_model.update_movie(
            movie_id,
            title=data.get('title'),
            release_year=data.get('release_year'),
            language=data.get('language'),
            duration=data.get('duration'),
            director=data.get('director'),
            description=data.get('description'),
            genre_ids=genre_ids
        )

        if rows:
            return jsonify({"message": "电影更新成功"})
        return jsonify({"error": "电影未找到"}), 404
    except Exception as e:
        print(f"更新电影异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/movies/<int:movie_id>", methods=["DELETE"])
def delete_movie(movie_id):
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        rows = movie_model.delete_movie(movie_id)
        if rows:
            return jsonify({"message": "电影删除成功"})
        return jsonify({"error": "电影未找到"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =======================
# User API
# =======================
@app.route("/api/users", methods=["GET"])
def get_users_list():
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '')
        gender = request.args.get('gender', '')
        favorite_genre = request.args.get('favorite_genre', '')

        print(f"获取用户列表 - 页码: {page}, 搜索: {search}, 性别: {gender}, 偏好类型: {favorite_genre}")

        # 使用新的搜索方法
        users, total = user_model.search_users(
            search_term=search if search else None,
            gender=gender if gender else None,
            favorite_genre=favorite_genre if favorite_genre else None,
            page=page,
            limit=limit
        )

        print(f"查询结果: 找到 {len(users)} 个用户, 总数: {total}")

        # 添加调试信息，显示前几个用户的数据
        if users:
            print("前几个用户数据:")
            for i, user in enumerate(users[:3]):
                print(f"用户 {i + 1}: {user}")

        return jsonify({
            "users": users,
            "total": total,
            "page": page,
            "limit": limit
        })
    except Exception as e:
        print(f"获取用户列表错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/recent")
def get_recent_users_list():
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        limit = request.args.get('limit', 5, type=int)
        users = user_model.get_all_users()
        # 按注册时间排序取最新用户
        sorted_users = sorted(users, key=lambda x: x.get('register_date', ''), reverse=True)
        return jsonify({"users": sorted_users[:limit]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>", methods=["GET"])
def get_single_user(user_id):
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        user = user_model.get_user_by_id(user_id)
        if user:
            return jsonify(user)
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users", methods=["POST"])
def add_new_user():
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        data = request.json
        print(f"添加用户数据: {data}")

        # 验证必需字段
        if not data.get('username') or not data.get('password'):
            return jsonify({"error": "用户名和密码不能为空"}), 400

        # 检查用户名是否已存在
        existing_user = user_model.get_user_by_username(data['username'])
        if existing_user:
            return jsonify({"error": "用户名已存在"}), 400

        # 密码加密
        data['password_hash'] = hash_password(data['password'])
        del data['password']

        # 处理可选字段
        user_data = {
            'username': data['username'],
            'password_hash': data['password_hash'],
            'nickname': data.get('nickname'),
            'age': data.get('age'),
            'gender': data.get('gender'),
            'favorite_genre_id': data.get('favorite_genre_id')
        }

        user_id = user_model.add_user(**user_data)
        if user_id:
            return jsonify({"message": "用户添加成功", "user_id": user_id}), 201
        else:
            return jsonify({"error": "添加用户失败"}), 500
    except Exception as e:
        print(f"添加用户异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>", methods=["PUT"])
def update_existing_user(user_id):
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        data = request.json
        print(f"更新用户数据: {data}")

        # 密码加密
        if 'password' in data and data['password']:
            data['password_hash'] = hash_password(data['password'])
            del data['password']

        # 构建更新数据
        update_data = {}
        for key in ['username', 'password_hash', 'nickname', 'age', 'gender', 'favorite_genre_id']:
            if key in data:
                update_data[key] = data[key]

        rows = user_model.update_user(user_id, **update_data)
        if rows:
            return jsonify({"message": "用户更新成功"})
        return jsonify({"error": "用户未找到"}), 404
    except Exception as e:
        print(f"更新用户异常: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_existing_user(user_id):
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        rows = user_model.delete_user(user_id)
        if rows:
            return jsonify({"message": "用户删除成功"})
        return jsonify({"error": "用户未找到"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =======================
# Rating API
# =======================
@app.route("/api/ratings", methods=["GET", "POST"])
def api_ratings():
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    if request.method == "POST":
        try:
            data = request.json
            user_id = session.get("user_id")
            movie_id = data.get('movie_id')
            score = data.get('score')

            if not movie_id or not score:
                return jsonify({"success": False, "message": "缺少必要的参数"}), 400

            # 检查是否已经评分过
            existing_rating = rating_model.get_user_movie_rating(user_id, movie_id) if hasattr(rating_model, 'get_user_movie_rating') else None
            
            if existing_rating:
                # 如果已评分，可以选择更新或者拒绝
                rating_model.update_rating(existing_rating['rating_id'], score)
                return jsonify({"success": True, "message": "评分已更新"})
            else:
                rating_id = rating_model.add_rating(user_id, movie_id, score)
                if rating_id:
                    return jsonify({"success": True, "message": "评分成功"})
                return jsonify({"success": False, "message": "评分失败"}), 500
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    # GET 请求处理
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '')
        score = request.args.get('score', '')
        date = request.args.get('date', '')

        # 使用新的搜索方法
        ratings, total = rating_model.search_ratings(
            search_term=search if search else None,
            score=int(score) if score else None,
            date=date if date else None,
            page=page,
            limit=limit
        )

        return jsonify({
            "ratings": ratings,
            "total": total,
            "page": page,
            "limit": limit
        })
    except Exception as e:
        print(f"获取评分列表错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


# 添加获取单个评分的路由
@app.route("/api/ratings/<int:rating_id>", methods=["GET"])
def get_rating(rating_id):
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        rating = rating_model.get_rating_by_id(rating_id)
        if rating:
            return jsonify(rating)
        return jsonify({"error": "评分记录未找到"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 添加更新评分的路由
@app.route("/api/ratings/<int:rating_id>", methods=["PUT"])
def update_rating(rating_id):
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        data = request.json
        score = data.get('score')

        if not score or not (1 <= score <= 5):
            return jsonify({"error": "评分必须在1-5之间"}), 400

        rows = rating_model.update_rating(rating_id, score)
        if rows:
            return jsonify({"message": "评分更新成功"})
        return jsonify({"error": "评分记录未找到"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 添加删除评分的路由
@app.route("/api/ratings/<int:rating_id>", methods=["DELETE"])
def delete_rating(rating_id):
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        rows = rating_model.delete_rating(rating_id)
        if rows:
            return jsonify({"message": "评分删除成功"})
        return jsonify({"error": "评分记录未找到"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500



# =======================
# History API
# =======================
@app.route("/api/history", methods=["GET", "POST"])
def api_history():
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    if request.method == "POST":
        try:
            data = request.json
            user_id = session.get("user_id")
            movie_id = data.get('movie_id')
            duration_watched = data.get('duration_watched', 0)
            completed = data.get('completed', False)

            if not movie_id:
                return jsonify({"success": False, "message": "缺少必要的参数"}), 400

            history_id = history_model.add_history(user_id, movie_id, duration_watched, completed)
            if history_id:
                return jsonify({"success": True, "message": "添加到想看列表成功"})
            return jsonify({"success": False, "message": "添加失败"}), 500
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    # GET 请求处理
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '')
        completed = request.args.get('completed', '')
        date = request.args.get('date', '')

        # 处理 completed 参数
        completed_param = None
        if completed.lower() == 'true':
            completed_param = True
        elif completed.lower() == 'false':
            completed_param = False

        # 使用新的搜索方法
        history, total = history_model.search_history(
            search_term=search if search else None,
            completed=completed_param,
            date=date if date else None,
            page=page,
            limit=limit
        )

        return jsonify({
            "history": history,
            "total": total,
            "page": page,
            "limit": limit
        })
    except Exception as e:
        print(f"获取历史记录列表错误: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/history/<int:history_id>", methods=["GET"])
def get_single_history(history_id):
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        history = history_model.get_history_by_id(history_id)
        if history:
            return jsonify(history)
        return jsonify({"error": "历史记录未找到"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/history/<int:history_id>", methods=["PUT"])
def update_history(history_id):
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        data = request.json
        duration_watched = data.get('duration_watched')
        completed = data.get('completed')

        rows = history_model.update_history(history_id, duration_watched, completed)
        if rows:
            return jsonify({"message": "历史记录更新成功"})
        return jsonify({"error": "历史记录未找到"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/history/<int:history_id>", methods=["DELETE"])
def delete_history(history_id):
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        rows = history_model.delete_history(history_id)
        if rows:
            return jsonify({"message": "历史记录删除成功"})
        return jsonify({"error": "历史记录未找到"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =======================
# Genre API (添加这个新的API路由)
# =======================
@app.route("/api/genres", methods=["GET"])
def get_genres():
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        # 这里需要根据您的数据库结构实现获取类型列表
        # 假设有一个 genre 表
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM genre ORDER BY genre_name;")
        genres = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({"genres": genres})
    except Exception as e:
        print(f"获取类型列表错误: {str(e)}")
        # 返回一个默认的类型列表作为fallback
        default_genres = [
            {"genre_id": 1, "genre_name": "动作"},
            {"genre_id": 2, "genre_name": "喜剧"},
            {"genre_id": 3, "genre_name": "剧情"},
            {"genre_id": 4, "genre_name": "科幻"},
            {"genre_id": 5, "genre_name": "恐怖"}
        ]
        return jsonify({"genres": default_genres})


# =======================
# Dashboard Chart Data API (添加这个API路由)
# =======================
@app.route("/api/dashboard/chart-data")
def dashboard_chart_data():
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        from collections import defaultdict
        import datetime

        # 生成最近6个月的标签
        today = datetime.date.today()
        labels = []
        for i in range(5, -1, -1):
            d = today - datetime.timedelta(days=30*i)
            labels.append(d.strftime("%Y-%m"))
            
        # 统计用户注册数
        users = user_model.get_all_users() or []
        user_counts = {label: 0 for label in labels}
        for u in users:
            date_str = str(u.get("register_date", ""))
            if len(date_str) >= 7:
                month = date_str[:7]
                if month in user_counts:
                    user_counts[month] += 1
                    
        # 统计播放记录数（作为活跃度代替电影添加数）
        history = history_model.get_all_history() or []
        history_counts = {label: 0 for label in labels}
        for h in history:
            date_str = str(h.get("watch_time", ""))
            if len(date_str) >= 7:
                month = date_str[:7]
                if month in history_counts:
                    history_counts[month] += 1

        chart_data = {
            "labels": labels,
            "users": [user_counts[l] for l in labels],
            "movies": [history_counts[l] for l in labels] # 这里为了图表有数据，用播放量代替电影数
        }
        return jsonify(chart_data)
    except Exception as e:
        print(f"获取图表数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# =======================
# Dashboard Recent Activities API
# =======================
@app.route("/api/dashboard/recent-activities")
def dashboard_recent_activities():
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        activities = []
        
        # 1. 获取最新注册用户
        users = user_model.get_all_users() or []
        for u in users:
            if u.get("register_date"):
                activities.append({
                    "type": "user",
                    "title": f"新用户 {u.get('nickname') or u.get('username')} 注册",
                    "time": str(u.get("register_date"))
                })
                
        # 2. 获取最新评分
        ratings = rating_model.get_all_ratings() or []
        for r in ratings:
            if r.get("rating_time"):
                activities.append({
                    "type": "rating",
                    "title": f"用户 {r.get('nickname') or r.get('username')} 给《{r.get('movie_title')}》打了 {r.get('score')} 分",
                    "time": str(r.get("rating_time"))
                })
                
        # 3. 获取最新播放记录
        history = history_model.get_all_history() or []
        for h in history:
            if h.get("watch_time"):
                activities.append({
                    "type": "history",
                    "title": f"用户 {h.get('nickname') or h.get('username')} 观看了《{h.get('movie_title')}》",
                    "time": str(h.get("watch_time"))
                })

        # 按时间倒序排序并取前 10 条
        activities.sort(key=lambda x: x["time"], reverse=True)
        recent_activities = activities[:10]

        return jsonify({"activities": recent_activities})
    except Exception as e:
        print(f"获取最近活动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# =======================
# Recommendation API
# =======================
@app.route("/recommendations")
def recommendations_page():
    if not session.get("user_id"):
        return redirect(url_for("login_page"))
    return render_template("recommendations.html", username=session.get('username'))

# 优化推荐API - 添加缓存和异步
@app.route("/api/recommendations", methods=["GET"])
@cache_response(timeout=300)  # 缓存5分钟
def get_recommendations():
    """获取个性化推荐"""
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        user_id = session.get("user_id")
        limit = request.args.get('limit', 10, type=int)
        method = request.args.get('method', 'hybrid')

        # 获取推荐
        recommendations = recommendation_model.get_recommendations_for_user(
            user_id=user_id,
            limit=limit,
            method=method
        )

        return jsonify({
            "recommendations": recommendations,
            "total": len(recommendations),
            "method": method
        })

    except Exception as e:
        print(f"获取推荐失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/recommendations/popular", methods=["GET"])
def get_popular_recommendations():
    """获取热门推荐"""
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        limit = request.args.get('limit', 10, type=int)

        popular_movies = recommendation_model.get_popular_movies(limit=limit)

        return jsonify({
            "movies": popular_movies,
            "total": len(popular_movies),
            "type": "popular"
        })

    except Exception as e:
        print(f"获取热门推荐失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/recommendations/similar/<int:movie_id>", methods=["GET"])
def get_similar_movies(movie_id):
    """获取相似电影"""
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        limit = request.args.get('limit', 10, type=int)

        similar_movies = recommendation_model.get_similar_movies(
            movie_id=movie_id,
            limit=limit
        )

        return jsonify({
            "similar_movies": similar_movies,
            "total": len(similar_movies),
            "original_movie_id": movie_id
        })

    except Exception as e:
        print(f"获取相似电影失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/recommendations/train", methods=["POST"])
def train_recommendation_model():
    """训练推荐模型（管理员权限）"""
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    # 这里可以添加管理员权限检查
    try:
        from models.recommendation_model import recommender

        success = recommender.train_hybrid_model()

        if success:
            return jsonify({
                "message": "推荐模型训练成功",
                "status": "success"
            })
        else:
            return jsonify({
                "error": "模型训练失败",
                "status": "error"
            }), 500

    except Exception as e:
        print(f"训练模型失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/recommendations/stats", methods=["GET"])
def get_recommendation_stats():
    """获取推荐系统统计信息"""
    if not session.get("user_id"):
        return jsonify({"error": "未授权"}), 401

    try:
        from models.recommendation_model import recommender

        stats = recommendation_model.get_recommendation_stats()

        return jsonify(stats)

    except Exception as e:
        print(f"获取推荐统计失败: {str(e)}")
        return jsonify({"error": str(e)}), 500



# =======================
# 运行服务器
# =======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)