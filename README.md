# Muxue 慕雪

基于 Django 5.2 + MySQL 的个人站点，包含首页、博客、项目、下载、关于、用户 6 个应用。页面与后台走 Django 模板 + Admin，数据接口走 Django REST Framework。

## 技术栈

- Django 5.2.7 + Django REST Framework
- MySQL 8（`mysqlclient`）
- django-cors-headers、Pillow、markdown
- gunicorn（生产 WSGI）

## 应用一览

每个应用有自己的页面视图和 `api/` 前缀的 JSON 接口。

- `home` `/`、`/home/`：站点首页。
- `blog` `/blog/`：文章列表、详情、按分类拉取、搜索、Markdown 渲染；`admin/import-note/` 支持导入「一个 md + 同目录 img/」的笔记文件夹，`api/article/<id>/upload-images/` 批量上传插图。
- `project` `/project/`：项目列表、项目详情、项目文档详情，`docs/<id>/upload-images/` 上传文档配图，`import-note/` 导入笔记。
- `download` `/download/`：分类展示、`api/category/<name>/files/` 拉列表，`download/<category>/<filename>` 触发下载。
- `about` `/about/`：静态介绍页。
- `user` `/user/`：登录/注册页面 + `api/login|register|logout|user-info|send-verification-code`，验证码走邮箱。开发环境使用 `user.email_backend.CustomEmailBackend`（关闭 SSL 校验），生产走 Django 自带 SMTP 后端。

`DEBUG=True` 时 `MEDIA_URL`（`/media/`）由 Django 直接托管。

## 目录结构

```
muxue/
├── Muxue/            # 项目配置：settings.py / urls.py / wsgi.py
├── home/ blog/ project/ download/ about/ user/
├── static/           # collectstatic 目标（STATIC_ROOT）
├── media/            # 用户上传文件
├── resources/ img/   # 站点素材
├── mysql_data/       # backup_db.sh 输出目录
├── manage.py
├── requirements.txt
└── backup_db.sh
```

## 本地起步

需要 Python 3.10+ 和 MySQL 8。

```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

创建数据库和账号，默认 `settings.py` 用的是 `muxue` / `muxueuser`：

```sql
CREATE DATABASE muxue CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'muxueuser'@'localhost' IDENTIFIED BY '你的密码';
GRANT ALL PRIVILEGES ON muxue.* TO 'muxueuser'@'localhost';
FLUSH PRIVILEGES;
```

然后：

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

站点 http://127.0.0.1:8000/ ，后台 http://127.0.0.1:8000/admin/ 。

## 配置要点

当前 `Muxue/settings.py` 里以下值是硬编码的，正式部署前请务必替换（建议改成从环境变量读取，别提交到仓库）：

- `SECRET_KEY`：仓库里是开发占位串。
- `DATABASES.default.PASSWORD`：MySQL 密码。
- `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD`：163 邮箱账号与授权码。
- `ALLOWED_HOSTS`、`CSRF_TRUSTED_ORIGINS`：加上你的域名。
- `CORS_ORIGIN_ALLOW_ALL = True` 只适合开发，生产改成 `CORS_ALLOWED_ORIGINS` 白名单。

邮件默认走 163 的 SSL：`smtp.163.com:465`，`EMAIL_USE_SSL=True`、`EMAIL_USE_TLS=False`。切 Gmail/QQ/企业邮箱时同步改这几项。

## 生产部署

1. 设 `DEBUG = False`，配好 `ALLOWED_HOSTS` 和新的 `SECRET_KEY`。
2. `python manage.py collectstatic` 收集静态文件。
3. `gunicorn Muxue.wsgi:application` 启动应用，前面挂 Nginx 反代，静态和 `/media/` 交给 Nginx。
4. 数据库迁移：`python manage.py migrate`。

## 数据库备份

`backup_db.sh` 会用 `mysqldump` 导出 `muxue` 库到 `mysql_data/muxue_YYYYMMDD_HHMMSS.sql.gz`，并只保留最近 10 份：

```bash
bash backup_db.sh
```

账号密码在脚本顶部的变量里，改动数据库凭证时记得同步。

## 许可证

MIT License
