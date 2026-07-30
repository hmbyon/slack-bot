import re
from fastapi import FastAPI, Request
from supabase import create_client, Client

# ==========================================
# 1. 설정 정보 (끝에 슬래시 / 절대 넣지 마세요!)
# ==========================================
SUPABASE_URL = "https://htxjlpfqqqqueylucpis.supabase.co/rest/v1"  # 예: https://abcxyz.supabase.co
SUPABASE_KEY = "sb_publishable_1Ppr4HTGY6PL_G_8ESbLNg_7OAPFekW"                 # anon public key

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# ==========================================
# 2. 유튜브 URL 추출 함수
# ==========================================
def extract_youtube_ids(text: str):
    pattern = r"(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([a-zA-Z0-9_-]{11})"
    matches = re.findall(pattern, text)
    return list(set(matches))

# ==========================================
# 3. 슬랙 이벤트 수신 핸들러
# ==========================================
@app.post("/slack/events")
async def slack_events(request: Request):
    data = await request.json()

    if "challenge" in data:
        return {"challenge": data["challenge"]}

    event = data.get("event", {})

    if event.get("subtype") in ["message_changed", "message_deleted"] or event.get("bot_id"):
        return {"status": "ok"}

    text = event.get("text", "")
    channel_id = event.get("channel", "")
    user_id = event.get("user", "")

    video_ids = extract_youtube_ids(text)

    for v_id in video_ids:
        try:
            # 📌 dict 데이터를 바로 넣어서 insert
            payload = {
                "channel_id": str(channel_id),
                "video_id": str(v_id),
                "slack_user_id": str(user_id)
            }
            res = supabase.from_("links").insert(payload).execute()
            print(f"✅ DB 저장 성공: {v_id}")
        except Exception as e:
            print(f"❌ DB 저장 실패: {e}")

    return {"status": "ok"}