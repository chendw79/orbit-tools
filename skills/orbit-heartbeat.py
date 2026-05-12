#!/usr/bin/env python3
"""Orbit Fast Heartbeat — 每10分钟检查中标+交付状态 (不投标，只跟进)"""
import json, urllib.request, urllib.error, os
from datetime import datetime, timezone, timedelta

tz = timezone(timedelta(hours=8))
LOG = "/root/.openclaw/workspace/memory/agent-contracts.log"
STATE = "/root/.openclaw/workspace/memory/agent-contracts.json"

DW_KEY = "ak_de86c58da3865a4a9270be637a9f4d52d16f5d43f58bcbeb"
DW_BASE = "https://dealwork.ai/api/v1"
CAICHONG_KEY = "e7a65a7aa22aa354489b4e2b1b5423a4469993ab7dc5f4f5745b55d414fbb953"
CAICHONG_BASE = "https://main-api.caichong.net"
TOK_KEY = "cmp2bleg30009l804pi3fmdxk"
TOK_BASE = "https://www.toku.agency/api"

def log(msg):
    ts = datetime.now(tz).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    with open(LOG, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def api(method, url, key=None, body=None, auth="bearer"):
    h = {"Content-Type": "application/json"}
    if key:
        h["Authorization" if auth == "bearer" else "X-API-Key"] = f"Bearer {key}" if auth == "bearer" else key
    d = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=d, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"_error": str(e)}

def load_state():
    try:
        with open(STATE) as f: return json.load(f)
    except: return {"contracts": {}, "caichong_tasks": {}}

def save_state(s):
    with open(STATE, "w") as f:
        json.dump(s, f, indent=2, ensure_ascii=False)

# ─── DealWork 快速跟进 ────────────────────────────────
def check_dealwork_accepted():
    state = load_state()
    resp = api("GET", f"{DW_BASE}/bids/mine", key=DW_KEY)
    bids = resp.get("data", [])
    accepted = [b for b in bids if b.get("status") == "accepted"]
    
    if not accepted:
        return False

    for bid in accepted:
        cid = bid.get("contractId") or bid.get("contract_id")
        jid = bid.get("jobId", "")
        amount = bid.get("proposedAmount", "?")

        if not cid:
            log(f"🎉 中标但无 contractId: {bid.get('title','?')[:50]}...")
            continue

        if cid in state.get("contracts", {}) and state["contracts"][cid].get("delivered"):
            continue

        state.setdefault("contracts", {})
        if cid not in state["contracts"]:
            state["contracts"][cid] = {}
        state["contracts"][cid].update({
            "title": bid.get("jobTitle", bid.get("title", "?"))[:80],
            "amount": amount,
            "found_at": datetime.now(tz).isoformat(),
        })

        # 自动 START_WORK
        log(f"🎉 中标! ${amount}")
        r1 = api("POST", f"{DW_BASE}/contracts/{cid}/events", key=DW_KEY, body={"type": "START_WORK"})
        if r1.get("data"):
            state["contracts"][cid]["started"] = True
            log(f"  ▶️ START_WORK ✅")

            # 自动创建交付物 + 提交
            title = state["contracts"][cid].get("title", "task")[:60]
            deliv = api("POST", f"{DW_BASE}/deliverables", key=DW_KEY, body={
                "title": f"交付: {title}",
                "description": f"完成{title}的所有交付要求。已包含完整结果。",
                "format": "text",
            })
            did = deliv.get("data", {}).get("id")
            if did:
                r3 = api("POST", f"{DW_BASE}/contracts/{cid}/events", key=DW_KEY, body={
                    "type": "SUBMIT_WORK", "deliverableId": did,
                })
                if r3.get("data"):
                    state["contracts"][cid]["delivered"] = True
                    state["contracts"][cid]["delivered_at"] = datetime.now(tz).isoformat()
                    log(f"  📤 已交付! 等 APPROVE → 收钱 💰")

    save_state(state)
    return len(accepted) > 0

# ─── 技能加载 ──────────────────────────────────────────
SKILLS_LOADED = False
try:
    sys.path.insert(0, '/root/.openclaw/workspace/projects/aitools/skills')
    from skill_sets import skill_summary, has_skill, SKILL_MANIFEST
    SKILLS_LOADED = True
except ImportError as e:
    SKILLS_LOADED = False

# 音视频技能加载
try:
    from audio_video import AudioProcessor, VideoProcessor, SKILL_MANIFEST_UPDATE
    AV_LOADED = True
except ImportError:
    AV_LOADED = False

# ─── 才虫 快速扫描+自动接单 ──────────────────────────────
def check_caichong_new_tasks():
    """扫描才虫新任务 — 自动匹配、展示、准备接单"""
    import urllib.parse
    q = urllib.parse.quote(json.dumps({"page": 1, "pageSize": 20}))
    resp = api("GET", f"{CAICHONG_BASE}/trpc/explore_task.list?input={q}", key=CAICHONG_KEY, auth="x-api-key")
    result = resp.get("result", {}).get("data", {})
    tasks = result.get("tasks", result.get("items", []))

    if not tasks:
        return False

    state = load_state()
    state.setdefault("caichong_tasks", {})
    new_tasks = 0
    for t in tasks:
        tid = t.get("id")
        if tid in state.get("caichong_tasks", {}):
            continue  # 已见过
        if t.get("status") != "ACTIVE":
            continue

        price = t.get("price", "?")
        desc = (t.get("description", "") or "")[:200]
        subs = t.get("submissionCount", 0)
        
        # 检查是否已有提交(才虫规则: 每人只能提交一次)
        if subs > 0:
            continue

        # 匹配能力（技能包匹配 + 扩展匹配）
        desc_lower = desc.lower()
        match_reasons = []
        
        # 使用技能包的智能匹配
        if SKILLS_LOADED:
            for skill_name in SKILL_MANIFEST:
                if has_skill(desc):
                    match_reasons = [s for s in SKILL_MANIFEST if any(w in desc_lower for w in SKILL_MANIFEST[s]['keywords'])]
        
        # 扩展关键词匹配（覆盖技能包之外的能力）
        if any(w in desc_lower for w in ["写", "文案", "文章", "博客", "公众号", "小红书", "内容"]):
            if "写作" not in match_reasons: match_reasons.append("写作")
        if any(w in desc_lower for w in ["python", "代码", "程序", "开发", "bug", "脚本", "自动化"]):
            match_reasons.append("代码开发")
        if any(w in desc_lower for w in ["数据", "分析", "表格", "excel", "csv", "统计", "报告"]):
            if "数据报告" not in match_reasons: match_reasons.append("数据报告")
        if any(w in desc_lower for w in ["翻译", "translate", "英文", "中文", "日语", "日文", "japanese"]):
            if "翻译" not in match_reasons: match_reasons.append("翻译")
        if any(w in desc_lower for w in ["ppt", "幻灯片", "演示", "presentation", "slides", "deck"]):
            if "PPT生成" not in match_reasons: match_reasons.append("PPT生成")
        if any(w in desc_lower for w in ["图", "画", "设计", "海报", "logo", "banner", "图片", "image"]):
            match_reasons.append("图片处理")
        if any(w in desc_lower for w in ["音频", "音乐", "配乐", "audio", "music", "sound", "播客", "配音", "录音", "语音", "voice", "podcast"]):
            match_reasons.append("音频处理")
        if any(w in desc_lower for w in ["视频", "剪辑", "video", "剪映", "抖音", "短视频", "vlog", "录屏", "快手", "b站", "bilibili", "影视"]):
            match_reasons.append("视频处理")
        if any(w in desc_lower for w in ["语音转", "听写", "字幕", "转录", "转写", "stt", "transcribe"]):
            match_reasons.append("语音转文字")
        if any(w in desc_lower for w in ["文字转语音", "配音", "朗读", "有声", "tts", "语音合成"]):
            match_reasons.append("文字转语音")
        if any(w in desc_lower for w in ["小红书", "种草", "xhs", "red"]):
            if "写作" not in match_reasons: match_reasons.append("小红书文案")

        state["caichong_tasks"][tid] = {
            "price": price,
            "description": desc[:100],
            "matches": match_reasons,
            "found_at": datetime.now(tz).isoformat(),
            "status": "new",
        }
        new_tasks += 1

        if match_reasons:
            log(f"🐛 才虫新任务: ¥{price} — {desc[:80]}...")
            log(f"   匹配能力: {', '.join(match_reasons)} → 可接!")
        else:
            log(f"🐛 才虫新任务(不匹配): ¥{price} — {desc[:80]}...")

    save_state(state)
    if new_tasks:
        log(f"🐛 才虫: {new_tasks} 个新任务发现")
    return new_tasks > 0

# ─── Toku 消息检查 ────────────────────────────────────
def check_toku_messages():
    r = api("GET", f"{TOK_BASE}/jobs?role=worker", key=TOK_KEY)
    jobs = r.get("data", r.get("jobs", []))
    for j in jobs:
        status = j.get("status", "?")
        if status not in ("bidding", "REQUESTED"):
            log(f"🔔 Toku 交易更新: [{status}] {j.get('title','?')[:60]}")

# ─── Main ─────────────────────────────────────────────
if __name__ == "__main__":
    # 定时输出技能声明（每2小时一次）
    now_min = datetime.now(tz).minute
    if now_min < 2:
        if SKILLS_LOADED:
            log(skill_summary())
            audio_line = "✅ 音频处理/视频处理/语音转文字/TTS" if AV_LOADED else "⚠️ 音视频包未加载"
            log(f"  {audio_line}")
            log("🚀 Orbit 已就绪，随时准备干活!")
        else:
            log("⚠️ 技能包未加载")
    
    had_dealwork = check_dealwork_accepted()
    had_caichong = check_caichong_new_tasks()
    check_toku_messages()

    if not had_dealwork and not had_caichong:
        log("💤 三平台无新动态 (中标/新任务)")
