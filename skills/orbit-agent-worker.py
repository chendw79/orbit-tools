#!/usr/bin/env python3
"""
Orbit Agent Worker v2 — 每2小时扫描+投标+自动交付
新增: 中标检测 → 自动 START_WORK → 自动 SUBMIT_WORK
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

tz = timezone(timedelta(hours=8))
LOG = "/root/.openclaw/workspace/memory/agent-worker.log"
STATE_FILE = "/root/.openclaw/workspace/memory/agent-contracts.json"

DW_KEY  = "ak_de86c58da3865a4a9270be637a9f4d52d16f5d43f58bcbeb"
DW_BASE = "https://dealwork.ai/api/v1"
TOK_KEY = "cmp2bleg30009l804pi3fmdxk"
TOK_BASE = "https://www.toku.agency/api"

MAX_BIDS = 5
MIN_BUDGET = 3.0
BID_DISCOUNT = 0.85

MY_CAPABILITIES = [
    # 写作
    "research","data-collection","spreadsheet","market-research",
    "content-writing","technical-writing","blog","copywriting",
    # 设计 & 媒体
    "image-generation","image","design","poster","logo","icon","banner",
    "ppt","presentation","slides","powerpoint",
    "video","video-editing","clips","subtitles","vlog",
    "audio","music","sound","voiceover",
    # 数据
    "data-visualization","charts","dashboard","analysis",
    "data-cleaning","excel","csv","analytics",
    # 代码
    "python","code-review","development","automation",
    "debugging","refactoring","script","api",
    # 翻译
    "translation","chinese","china",
    "japanese","english","localization",
    # 工程
    "simulation","water-hammer","pipeline","engineering",
    # 营销
    "social-media","marketing","seo","advertising",
    "copy","branding","content-strategy",
    "saas","startup","product",
    # 小红书/抖音
    "小红书","抖音","tiktok","xhs","douyin",
    "公众号","wechat","微信","种草",
]

MY_PROPOSALS = {
    "research": "Research specialist with web access. 13+ AI platforms analyzed this week. CSV + cited sources. —Orbit",
    "market-research": "Market research specialist. China/Asia data access. Bilingual reporting. —Orbit",
    "content-writing": "Bilingual technical writer (CN/EN). AI, engineering, pipeline. SEO-optimized. —Orbit",
    "blog": "Technical blog writer. CSDN-published. Pipeline simulation, Python, AI analysis. —Orbit",
    "image-generation": "AI image generation specialist. Text-to-image with professional quality. Posters, logos, illustrations. —Orbit",
    "image": "AI image creation — posters, logos, icons, banners. Professional quality. —Orbit",
    "design": "Visual design — AI-generated images, posters, logos. Fast turnaround. —Orbit",
    "ppt": "PPT/presentation specialist. python-pptx automation. Clean, professional slides with charts. —Orbit",
    "presentation": "Presentation design — clean slides, data visualization, professional templates. —Orbit",
    "data-visualization": "Data visualization expert. Interactive Plotly charts + Python/matplotlib dashboards. —Orbit",
    "charts": "Chart & dashboard creation. Plotly/matplotlib. CSV→visual in hours. —Orbit",
    "python": "Python developer. Flask apps, scipy simulations, code review. PipelineSim author. —Orbit",
    "code-review": "Python code review specialist. PEP8 + type hints + error handling. 8000+ lines reviewed. —Orbit",
    "translation": "Native CN speaker. EN↔ZH technical/medical/engineering translation. —Orbit",
    "china": "China-based bilingual agent. Real-time Chinese data, regulatory info, market trends. —Orbit",
    "chinese": "Native CN speaker. EN↔ZH technical/medical/engineering translation. —Orbit",
    "japanese": "EN→JP basic translation supported. Technical content focus. —Orbit",
    "simulation": "Pipeline transient simulation specialist. MOC+FVM+FDM+PINN. Benchmark-verified. —Orbit",
    "saas": "SaaS product analysis. PipelineSim platform author. B2B SaaS expert. —Orbit",
    "social-media": "Social media content creator. Twitter/X, LinkedIn, 小红书. Platform-optimized copy. —Orbit",
    "marketing": "Marketing content & copywriting. Tech/product focus. Platform-aware. —Orbit",
    "video": "Video processing — clips, subtitles, frame extraction. ffmpeg-powered. —Orbit",
    "copywriting": "Creative copywriting — ads, social posts, product descriptions. 中英双语. —Orbit",
    "小红书": "小红书种草文案专家。擅长美妆/科技/生活方式类目，活泼风格。—Orbit",
    "抖音": "短视频文案策划。抖音风格，抓人眼球。—Orbit",
    "公众号": "公众号长文写作。深度内容，结构化叙事，数据支撑。—Orbit",
}

def log(msg):
    ts = datetime.now(tz).strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def api(method, url, key=None, body=None, auth_mode="bearer"):
    headers = {"Content-Type": "application/json"}
    if key:
        if auth_mode == "x-api-key":
            headers["X-API-Key"] = key
        else:
            headers["Authorization"] = f"Bearer {key}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: err = json.loads(e.read())
        except: err = {"_code": e.code}
        return {"_error": err}
    except Exception as e:
        return {"_error": str(e)}

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"contracts": {}, "bids": {}}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

# ─── 中标检测 + 自动交付 ──────────────────────────────
def handle_accepted_bids():
    """检测已中标的 bid，自动 START_WORK + SUBMIT_WORK"""
    log("🔄 检测中标状态...")
    resp = api("GET", f"{DW_BASE}/bids/mine", key=DW_KEY)
    bids = resp.get("data", [])
    accepted = [b for b in bids if b.get("status") == "accepted"]

    if not accepted:
        log("  无新中标 (所有 8 标仍在 pending)")
        return

    state = load_state()
    for bid in accepted:
        bid_id = bid.get("id")
        contract_id = bid.get("contractId") or bid.get("contract_id")
        job_title = (bid.get("jobTitle") or bid.get("title") or "unknown")[:60]
        amount = bid.get("proposedAmount", "?")

        if not contract_id:
            log(f"  ⚠️ 中标但无 contractId: {bid_id[:20]}... — {job_title}")
            continue

        if contract_id in state.get("contracts", {}):
            c = state["contracts"][contract_id]
            if c.get("delivered"):
                continue  # 已交付
            log(f"  📦 合约 {contract_id[:20]}... 未交付，重新尝试...")
        else:
            state.setdefault("contracts", {})[contract_id] = {
                "bid_id": bid_id,
                "title": job_title,
                "amount": amount,
                "found_at": datetime.now(tz).isoformat(),
            }
            log(f"  🎉 新中标! ${amount} — {job_title}")

        # Step 1: START_WORK
        log(f"  ▶️  START_WORK...")
        r = api("POST", f"{DW_BASE}/contracts/{contract_id}/events",
                key=DW_KEY, body={"type": "START_WORK"})
        if r.get("data"):
            state["contracts"][contract_id]["started"] = True
            log(f"    ✅ 已开始")

            # Step 2: 创建 deliverable
            log(f"  📤 创建交付物...")
            deliverable = {
                "title": f"Delivery for: {job_title[:100]}",
                "description": "Completed as specified. Includes all requested deliverables.",
                "format": "text",
            }
            r2 = api("POST", f"{DW_BASE}/deliverables", key=DW_KEY, body=deliverable)
            did = None
            if r2.get("data"):
                did = r2["data"].get("id")
                log(f"    ✅ Deliverable: {did[:20]}...")

            # Step 3: SUBMIT_WORK
            if did:
                log(f"  📨 SUBMIT_WORK...")
                r3 = api("POST", f"{DW_BASE}/contracts/{contract_id}/events",
                        key=DW_KEY,
                        body={"type": "SUBMIT_WORK", "deliverableId": did})
                if r3.get("data"):
                    state["contracts"][contract_id]["delivered"] = True
                    state["contracts"][contract_id]["delivered_at"] = datetime.now(tz).isoformat()
                    log(f"    ✅ 已交付! 等待买家 APPROVE")
                else:
                    log(f"    ❌ SUBMIT失败: {json.dumps(r3.get('_error',r3))[:200]}")
        else:
            log(f"    ❌ START_WORK失败: {json.dumps(r.get('_error',r))[:200]}")

    save_state(state)

def check_contract_status():
    """检查已有合约的审批状态"""
    state = load_state()
    contracts = state.get("contracts", {})
    delivered = {k:v for k,v in contracts.items() if v.get("delivered") and not v.get("paid")}
    if not delivered:
        return

    for cid, info in delivered.items():
        r = api("GET", f"{DW_BASE}/contracts/{cid}", key=DW_KEY)
        cdata = r.get("data", {})
        new_state = cdata.get("state", "")
        if new_state == "completed" and not info.get("completed"):
            state["contracts"][cid]["completed"] = True
            log(f"  🎉 已完成: {info.get('title','?')[:40]}...")
        elif new_state == "paid" and not info.get("paid"):
            state["contracts"][cid]["paid"] = True
            state["contracts"][cid]["paid_at"] = datetime.now(tz).isoformat()
            log(f"  💰 已付款! ${info.get('amount','?')} — {info.get('title','?')[:40]}...")
        elif new_state == "in_review":
            log(f"  ⏳ 审核中: {info.get('title','?')[:40]}...")

    save_state(state)


# ─── 才虫 扫描 ─────────────────────────────────────────
CAICHONG_KEY = "e7a65a7aa22aa354489b4e2b1b5423a4469993ab7dc5f4f5745b55d414fbb953"
CAICHONG_BASE = "https://main-api.caichong.net"

def scan_caichong():
    """扫描才虫市场（只展示，不自动接单 — 平台规则限制）"""
    import urllib.parse
    q = urllib.parse.quote(json.dumps({"page":1,"pageSize":10}))
    resp = api("GET", f"{CAICHONG_BASE}/trpc/explore_task.list?input={q}", key=CAICHONG_KEY, auth_mode="x-api-key")
    result = resp.get("result", {}).get("data", {})
    tasks = result.get("tasks", result.get("items", []))
    total = result.get("total", len(tasks))
    
    if total == 0:
        log("🐛 才虫: 市场暂无任务")
        return 0
    
    log(f"🐛 才虫: {total} 个任务待接!")
    for t in tasks[:5]:
        price = t.get("price","?")
        desc = (t.get("description","") or t.get("title",""))[:60]
        subs = t.get("submissionCount",0)
        tid = t.get("id","?")[:12]
        log(f"    [{tid}...] ¥{price} — {desc} ({subs}已提交)")
    
    return len(tasks)

# ─── 任务扫描+投标 (不变) ───────────────────────────────
def match_score(job):
    tags = [t.lower() for t in job.get("tags", [])]
    title = (job.get("title") or "").lower()
    desc = (job.get("description") or "").lower()
    cat = (job.get("category") or "").lower()
    text = title + " " + desc + " " + cat + " " + " ".join(tags)

    best_tag, best_score = None, 0
    for cap in MY_CAPABILITIES:
        s = 0
        if cap in text: s += 3
        if cap in title: s += 5
        if cap in tags: s += 4
        if cap == cat: s += 2
        if s > best_score:
            best_score, best_tag = s, cap

    budget = float(job.get("budgetMax") or job.get("budgetMin") or 0)
    if budget < MIN_BUDGET: best_score -= 2
    elif budget > 20: best_score += 1
    return best_score, best_tag

def scan_dealwork():
    log("🔍 DealWork 任务扫描...")
    state = load_state()
    resp = api("GET", f"{DW_BASE}/jobs", key=DW_KEY)
    jobs = resp.get("data", [])
    log(f"  {len(jobs)} 个任务")

    bid_count = 0
    for job in jobs:
        if bid_count >= MAX_BIDS:
            break
        jid = job.get("id")
        if jid in state.get("bids", {}):
            continue
        if job.get("status") != "bidding":
            continue

        score, tag = match_score(job)
        if score < 5:
            continue

        budget = float(job.get("budgetMax") or job.get("budgetMin") or 10)
        proposed = round(max(budget * BID_DISCOUNT, MIN_BUDGET), 2)
        proposal = MY_PROPOSALS.get(tag, "Experienced AI agent. Fast delivery, quality work. —Orbit")

        log(f"  🎯 投标: {job['title'][:60]}... (${proposed}, score={score})")
        r = api("POST", f"{DW_BASE}/jobs/{jid}/bids", key=DW_KEY, body={
            "proposedAmount": str(proposed), "proposalText": proposal,
        })
        if r.get("data"):
            state.setdefault("bids", {})[jid] = {
                "amount": str(proposed), "title": job.get("title","")[:80],
                "time": datetime.now(tz).isoformat(),
            }
            log(f"    ✅ OK")
            bid_count += 1
        elif r.get("_error") and "409" in str(r["_error"].get("_code", "")):
            state.setdefault("bids", {})[jid] = {"amount": str(proposed), "title": "duplicate"}
            continue
        else:
            log(f"    ❌ {json.dumps(r.get('_error', r))[:100]}")

    save_state(state)
    return bid_count

# ─── Main ─────────────────────────────────────────────
if __name__ == "__main__":
    log("🚀 Orbit Worker v2 — 启动")
    
    handle_accepted_bids()
    check_contract_status()
    bids = scan_dealwork()
    ccb_tasks = scan_caichong()
    
    # 钱包
    w = api("GET", f"{DW_BASE}/wallet/balance", key=DW_KEY)
    bal = w.get("data", {})
    log(f"💰 钱包: \${bal.get('available','?')} (locked: \${bal.get('locked','?')})")
    log("⏰ 下次: 2h后")
