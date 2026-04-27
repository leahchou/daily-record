# Daily Record · 个人每日记录

> 一个极简的每日记录页面，数据保存为 Markdown 文件，直接在 Obsidian 中查看。

## 功能

- 🎯 今日任务（勾选 / 进度条）
- 🌙 今天做了什么
- 💭 今天在想什么 + 情绪 emoji
- ✦ 沉浸写作（全屏专注写作模式）
- 📤 一键导出 Markdown

## 启动

```bash
# 安装依赖（首次）
python3 -m venv .venv
.venv/bin/pip install flask flask-cors

# 启动服务
bash start.sh
# 浏览器访问 http://localhost:7788
```

## 数据存储

数据保存到 `VAULT_PATH/📖00-日志/YYYY-MM.md`（在 `server.py` 中配置路径）。
