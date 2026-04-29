# 🎬 电影推荐系统 (Movie Recommendation System)

基于 Flask 和 MySQL 构建的电影推荐系统，包含用户管理、电影展示、评分、历史记录以及基于协同过滤和内容相似度的混合推荐功能。

## 🛠️ 环境要求

* Python 3.8+
* MySQL 5.7+

## 🚀 快速启动指南

### 1. 准备数据库

1. 确保你的电脑上已安装并启动了 MySQL 服务。
2. 在 MySQL 中创建一个名为 `movie_system` 的空数据库（字符集推荐使用 `utf8mb4`）：
   ```sql
   CREATE DATABASE movie_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. **配置数据库账号密码**：
   默认的数据库连接信息为用户名 `root`，密码 `123456`。如果你的本地环境不同，请修改以下文件中的数据库连接配置：
   * `movie_system_api/db_config.py`
   * `movie_db/` 目录下的所有 `1` 到 `9` 开头的 Python 初始化脚本。

### 2. 安装 Python 依赖

在项目根目录下打开终端，安装所需的 Python 第三方库：

```bash
pip install flask flask-cors pymysql pandas numpy scikit-learn scipy schedule faker python-dotenv
```
*(注：`faker` 库用于生成测试用的随机假数据)*

### 3. 初始化数据库与测试数据

进入数据库脚本目录并依次执行脚本，这会自动建表并插入电影、用户、评分等测试数据：

```bash
cd movie-recommendation-system-main\movie_db
python 2-create_tables.py
python 3-create_data_movie.py
python 4-create_data_genre_movie.py
python 5-create_data_user.py
python 6-create_data_rating.py
python 7-create_data_history.py
python 8-create_advanced_features.py
python 9-import_posters.py
python 10-clean_duplicates.py
```
*(注：生成的用户注册、评分和观看历史数据已默认配置为生成在 2026 年 4 月 26 日前后的近期时间。10-clean_duplicates.py 用于清理多次运行数据生成脚本可能产生的重复电影数据。)*

### 4. 启动 Web 后端服务

进入 API 目录并启动 Flask 服务：

```bash
cd ../movie_system_api
python app.py
```
* 启动成功后，默认可以在电脑浏览器访问 [http://127.0.0.1:5000](http://127.0.0.1:5000)。
* 项目已配置为 `host="0.0.0.0"`，因此你也支持在同一局域网（Wi-Fi）下的手机或其他电脑上，通过输入本机的局域网 IP（如 `http://192.168.x.x:5000`）来访问系统。

### 5. 训练推荐模型（关键）

为了让系统的“个性化推荐”功能有数据支撑，需要另外**新开一个终端窗口**，进入 `movie_system_api` 目录，运行模型训练脚本：

```bash
cd movie-recommendation-system-main\movie_system_api
python train_recommendation_model.py
```
运行后按提示输入 `1` 选择立即训练。模型会读取刚才生成的假数据，训练完成后，网页端的推荐页面就会展示计算好的推荐电影了。

## 💡 其他说明

* **关于测试用户**：系统中目前都是由 Faker 生成的假用户。你可以自己点击页面上的“注册”按钮创建一个真实账号，然后自己给几部电影打分，再重新运行一次 `train_recommendation_model.py`，看看系统给你的个性化推荐！
