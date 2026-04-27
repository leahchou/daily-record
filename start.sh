#!/bin/bash
# Second Me · 日记服务器启动脚本
# 用法：双击运行，或 bash start.sh

DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$DIR/.venv/bin/python"

echo "📓 启动 Second Me 日记服务..."
echo "🌐 浏览器打开：http://localhost:7788"
echo "📁 数据保存到：second me/📖00-日志/"
echo ""
echo "按 Ctrl+C 停止服务"
echo "---"

"$PYTHON" "$DIR/server.py"
