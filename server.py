"""Second Me · 日记 API 服务器

启动方式：
    cd "📊dashboard"
    .venv/bin/python server.py

访问：http://localhost:7788
"""

from __future__ import annotations

import json
import re
from datetime import datetime, date
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".")
CORS(app)

# ── 路径配置 ──────────────────────────────────────────────────────────────
VAULT = Path(__file__).parent.parent          # second me/
JOURNAL_DIR = VAULT / "📖00-日志"
JOURNAL_DIR.mkdir(exist_ok=True)


# ── 工具函数 ──────────────────────────────────────────────────────────────

def get_monthly_file(d: date) -> Path:
    return JOURNAL_DIR / f"{d.year:04d}-{d.month:02d}.md"


def day_heading(d: date) -> str:
    return f"## {d.month:02d}-{d.day:02d}"


def build_day_block(d: date, data: dict) -> str:
    """把前端数据组装成 Markdown 段落。"""
    lines: list[str] = []
    heading = day_heading(d)
    lines.append(heading)
    lines.append("")

    # 情绪
    emotion_map = {
        "peaceful": "😌 平静", "happy": "😊 愉悦", "excited": "✨ 兴奋",
        "grateful": "🌸 感激", "tired": "🌿 疲惫", "anxious": "🌊 焦虑",
        "sad": "🌧 低落", "confused": "🌀 迷茫", "focused": "🔥 专注",
        "hopeful": "🌅 期待",
    }
    emotion = data.get("emotion", "")
    if emotion:
        lines.append(f"> 今日心情：{emotion_map.get(emotion, emotion)}")
        lines.append("")

    # 今日任务
    tasks = data.get("tasks", [])
    if tasks:
        lines.append("### 🎯 今日任务")
        lines.append("")
        for t in tasks:
            check = "x" if t.get("done") else " "
            lines.append(f"- [{check}] {t['text']}")
        lines.append("")

    # 今天做了什么
    did = (data.get("did") or "").strip()
    if did:
        lines.append("### 🌙 今天做了什么")
        lines.append("")
        lines.append(did)
        lines.append("")

    # 今天在想什么
    think = (data.get("think") or "").strip()
    if think:
        lines.append("### 💭 今天在想什么")
        lines.append("")
        lines.append(think)
        lines.append("")

    # 沉浸写作
    immersive = (data.get("immersive") or "").strip()
    if immersive:
        lines.append("### ✦ 沉浸写作")
        lines.append("")
        lines.append(immersive)
        lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def upsert_day(monthly_file: Path, d: date, block: str) -> None:
    """在月度文件里插入或替换当天的段落。"""
    heading = day_heading(d)

    if not monthly_file.exists():
        # 新建月度文件
        header = (
            f"# {d.year}年{d.month:02d}月 · 日常记录\n\n"
            "> 格式随意，持续即价值。\n\n---\n\n"
        )
        monthly_file.write_text(header + block, encoding="utf-8")
        return

    content = monthly_file.read_text(encoding="utf-8")

    # 找到当天 heading 的位置
    # 匹配 "## MM-DD" 后，直到下一个 "## " 或文件末尾
    pattern = re.compile(
        rf"^{re.escape(heading)}[ \t]*\n.*?(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )

    if pattern.search(content):
        # 替换已有段落
        new_content = pattern.sub(block, content)
    else:
        # 追加到文件开头（最新的在最前面，与现有格式一致）
        # 找到第一个 ## 之前的位置插入
        first_entry = re.search(r"^## \d{2}-\d{2}", content, re.MULTILINE)
        if first_entry:
            insert_pos = first_entry.start()
            new_content = content[:insert_pos] + block + content[insert_pos:]
        else:
            new_content = content + block

    monthly_file.write_text(new_content, encoding="utf-8")


def load_day(monthly_file: Path, d: date) -> dict:
    """从月度文件解析当天的数据，返回给前端。"""
    if not monthly_file.exists():
        return {}

    content = monthly_file.read_text(encoding="utf-8")
    heading = day_heading(d)

    pattern = re.compile(
        rf"^{re.escape(heading)}[ \t]*\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(content)
    if not m:
        return {}

    block = m.group(1)
    result: dict = {"tasks": [], "did": "", "think": "", "emotion": "", "immersive": ""}

    # 解析情绪
    emo_m = re.search(r"> 今日心情：(.+)", block)
    if emo_m:
        emo_text = emo_m.group(1).strip()
        emotion_rmap = {
            "😌 平静": "peaceful", "😊 愉悦": "happy", "✨ 兴奋": "excited",
            "🌸 感激": "grateful", "🌿 疲惫": "tired", "🌊 焦虑": "anxious",
            "🌧 低落": "sad", "🌀 迷茫": "confused", "🔥 专注": "focused",
            "🌅 期待": "hopeful",
        }
        result["emotion"] = emotion_rmap.get(emo_text, "")

    # 解析任务
    task_section = re.search(r"### 🎯 今日任务\n\n(.*?)(?=###|\Z)", block, re.DOTALL)
    if task_section:
        for line in task_section.group(1).splitlines():
            tm = re.match(r"- \[( |x)\] (.+)", line)
            if tm:
                result["tasks"].append({"done": tm.group(1) == "x", "text": tm.group(2)})

    # 解析各文本段
    def extract_section(label: str) -> str:
        sec = re.search(rf"### {re.escape(label)}\n\n(.*?)(?=###|---|\Z)", block, re.DOTALL)
        return sec.group(1).strip() if sec else ""

    result["did"]       = extract_section("🌙 今天做了什么")
    result["think"]     = extract_section("💭 今天在想什么")
    result["immersive"] = extract_section("✦ 沉浸写作")

    return result


# ── 路由 ─────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return send_from_directory(".", "daily.html")

@app.get("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)


@app.get("/api/load")
def api_load():
    """GET /api/load?date=2026-04-27"""
    date_str = request.args.get("date", str(date.today()))
    try:
        d = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "invalid date"}), 400

    monthly_file = get_monthly_file(d)
    data = load_day(monthly_file, d)
    return jsonify({"ok": True, "data": data})


@app.post("/api/save")
def api_save():
    """POST /api/save  body: { date, tasks, did, think, emotion, immersive }"""
    payload = request.get_json(force=True, silent=True) or {}
    date_str = payload.get("date", str(date.today()))
    try:
        d = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "invalid date"}), 400

    block = build_day_block(d, payload)
    monthly_file = get_monthly_file(d)
    upsert_day(monthly_file, d, block)

    return jsonify({"ok": True, "file": str(monthly_file.relative_to(VAULT))})


if __name__ == "__main__":
    print(f"📓 Vault: {VAULT}")
    print(f"📁 Journal dir: {JOURNAL_DIR}")
    print(f"🌐 Open: http://localhost:7788")
    app.run(port=7788, debug=False)
