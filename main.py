import re
from fastapi import FastAPI, Request
from supabase import create_client, Client

# ==========================================
# 1. 설정 정보 (본인의 Supabase 정보)
# ==========================================
SUPABASE_URL = "https://your-project.supabase.co"  # 👈 본인의 Project URL
SUPABASE_KEY = "your-publishable-key"               # 👈 본인의 Publishable Key

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# 📌 localtunnel 보안 패과용 헤더 자동 추가
@app.middleware("http")
async def add_bypass_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["bypass-tunnel-reminder"] = "true"
    return response

# ==========================================
# 2. 유튜브 URL 추출 함수
# ==========================================
def extract_youtube_ids(text: str):
    pattern = r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})"
    return list(set(re.findall(pattern, text)))

# ==========================================
# 3. 슬랙 이벤트 수신 서버
# ==========================================
@app.post("/slack/events")
async def slack_events(request: Request):
    data = await request.json()

    # 슬랙 Challenge 인증용
    if "challenge" in data:
        return {"challenge": data["challenge"]}

    event = data.get("event", {})
    
    # 📌 [디버깅 추가] 슬랙에서 이벤트가 들어오면 무조건 로그를 찍습니다!
    print("\n📩 [이벤트 도착!]:", event)

    # 봇 자신이 보낸 메시지는 무시 (무한 루프 방지)
    if event.get("bot_id") or event.get("subtype") == "bot_message":
        return {"status": "ok"}

    text = event.get("text", "")
    channel_id = event.get("channel", "")
    user_id = event.get("user", "")

    video_ids = extract_youtube_ids(text)
    print(f"🔍 추출된 비디오 ID: {video_ids}")

    for v_id in video_ids:
        try:
            supabase.table("links").insert({
                "channel_id": channel_id,
                "video_id": v_id,
                "slack_user_id": user_id
            }).execute()
            print(f"✅ [DB 저장 완료] 채널: {channel_id} | 비디오: {v_id}")
        except Exception as e:
            print(f"❌ [DB 저장 실패]: {e}")

    return {"status": "ok"}