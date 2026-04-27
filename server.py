"""Second Me · 日记 API 服务器

启动方式：
    cd "📊dashboard"
    .venv/bin/python server.py

访问：http://localhost:7788

数据保存到：second me/📖00-日志/daily/YYYY-MM-DD.md
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".")
CORS(app)

# ── 路径配置 ──────────────────────────────────────────────────────────────
VAULT      = Path(__file__).parent.parent        # second me/
DAILY_DIR  = VAULT / "📖00-日志" / "daily"
DAILY_DIR.mkdir(parents=True, exist_ok=True)


# ── 工具函数 ──────────────────────────────────────────────────────────────

EMOTION_MAP = {
    "peaceful": "😌 平静", "happy": "😊 愉悦", "excited": "✨ 兴奋",
    "grateful": "🌸 感激", "tired": "🌿 疲惫", "anxious": "🌊 焦虑",
    "sad": "🌧 低落",  "confused": "🌀 迷茫", "focused": "🔥 专注",
    "hopeful": "🌅 期待",
}
EMOTION_RMAP = {v: k for k, v in EMOTION_MAP.items()}


def daily_file(d: date) -> Path:
    return DAILY_DIR / f"{d.isoformat()}.md"


def build_file(d: date, data: dict) -> str:
    """把前端数据组装成独立的每日 Markdown 文件。"""
    weekdays = ["周一","周二","周三","周四","周五","周六","周日"]
    week = weekdays[d.weekday()]
    lines: list[str] = []

    lines.append(f"# {d.year}年{d.month:02d}月{d.day:02d}日 · {week}")
    lines.append("")
    lines.append(f"tags: daily-record")
    lines.append("")

    # 情绪
    emotion = data.get("emotion", "")
    if emotion:
        lines.append(f"> 今日心情：{EMOTION_MAP.get(emotion, emotion)}")
        lines.append("")

    # 今日任务
    tasks = data.get("tasks", [])
    if tasks:
        lines.append("## 🎯 今日任务")
        lines.append("")
        for t in tasks:
            check = "x" if t.get("done") else " "
            lines.append(f"- [{check}] {t['text']}")
        lines.append("")

    # 今天做了什么
    did = (data.get("did") or "").strip()
    if did:
        lines.append("## 🌙 今天做了什么")
        lines.append("")
        lines.append(did)
        lines.append("")

    # 今天在想什么
    think = (data.get("think") or "").strip()
    if think:
        lines.append("## 💭 今天在想什么")
        lines.append("")
        lines.append(think)
        lines.append("")

    # 沉浸写作
    immersive = (data.get("immersive") or "").strip()
    if immersive:
        lines.append("## ✦ 沉浸写作")
        lines.append("")
        lines.append(immersive)
        lines.append("")

    return "\n".join(lines)


def parse_file(d: date) -> dict:
    """从每日文件解析数据，返回给前端。"""
    f = daily_file(d)
    if not f.exists():
        return {}

    content = f.read_text(encoding="utf-8")
    result: dict = {"tasks": [], "did": "", "think": "", "emotion": "", "immersive": ""}

    # 情绪
    emo_m = re.search(r"> 今日心情：(.+)", content)
    if emo_m:
        result["emotion"] = EMOTION_RMAP.get(emo_m.group(1).strip(), "")

    # 任务
    task_sec = re.search(r"## 🎯 今日任务\n\n(.*?)(?=^##|\Z)", content, re.DOTALL | re.MULTILINE)
    if task_sec:
        for line in task_sec.group(1).splitlines():
            tm = re.match(r"- \[( |x)\] (.+)", line)
            if tm:
                result["tasks"].append({"done": tm.group(1) == "x", "text": tm.group(2)})

    def extract(label: str) -> str:
        sec = re.search(rf"## {re.escape(label)}\n\n(.*?)(?=^##|^tags:|\Z)", content, re.DOTALL | re.MULTILINE)
        return sec.group(1).strip() if sec else ""

    result["did"]       = extract("🌙 今天做了什么")
    result["think"]     = extract("💭 今天在想什么")
    result["immersive"] = extract("✦ 沉浸写作")

    return result


# ── 路由 ─────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return send_from_directory(".", "daily.html")

@app.get("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)


@app.get("/api/list")
def api_list():
    """GET /api/list  → 所有有记录的日期（ISO 格式，降序）"""
    import re as _re
    dates = sorted(
        [f.stem for f in DAILY_DIR.glob("*.md")
         if _re.match(r"\d{4}-\d{2}-\d{2}", f.stem)],
        reverse=True,
    )
    return jsonify({"ok": True, "dates": dates})


@app.get("/api/load")
def api_load():
    """GET /api/load?date=2026-04-27"""
    date_str = request.args.get("date", str(date.today()))
    try:
        d = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "invalid date"}), 400

    return jsonify({"ok": True, "data": parse_file(d)})


@app.post("/api/save")
def api_save():
    """POST /api/save  body: { date, tasks, did, think, emotion, immersive }"""
    payload = request.get_json(force=True, silent=True) or {}
    date_str = payload.get("date", str(date.today()))
    try:
        d = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "invalid date"}), 400

    f = daily_file(d)
    f.write_text(build_file(d, payload), encoding="utf-8")

    rel = str(f.relative_to(VAULT))
    return jsonify({"ok": True, "file": rel})


if __name__ == "__main__":
    print(f"📓 Vault:     {VAULT}")
    print(f"📁 Daily dir: {DAILY_DIR}")
    print(f"🌐 Open:      http://localhost:7788")
    app.run(port=7788, debug=False)
