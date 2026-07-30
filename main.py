import re
from fastapi import FastAPI, Request
from supabase import create_client, Client

# ==========================================
# 1. 설정 정보 (본인의 진짜 Supabase 정보로 수정 필수! 👈)
# ==========================================
SUPABASE_URL = "https://htxjlpfqqqqueylucpis.supabase.co/rest/v1/"  # 👈 본인의 진짜 Supabase URL
SUPABASE_KEY = "sb_publishable_1Ppr4HTGY6PL_G_8ESbLNg_7OAPFekW"            # 👈 본인의 진짜 Supabase Key

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# ==========================================
# 2. 유튜브 URL 추출 함수
# ==========================================
def extract_youtube_ids(text: str):
    # 슬랙은 URL을 <https://...|label> 형태로 전달할 수 있어 이를 정제합니다.
    pattern = r"(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([a-zA-Z0-9_-]{11})"
    matches = re.findall(pattern, text)
    return list(set(matches))

# ==========================================
# 3. 슬랙 이벤트 수신 서버
# ==========================================
@app.post("/slack/events")
async def slack_events(request: Request):
    data = await request.json()

    # 슬랙 URL 검증(Challenge) 처리
    if "challenge" in data:
        return {"challenge": data["challenge"]}

    event = data.get("event", {})
    
    print(f"\n📩 [이벤트 감지]: type={event.get('type')}, subtype={event.get('subtype')}")

    # 메시지 수정/삭제 등의 이벤트는 무시하고 새 메시지만 처리
    if event.get("subtype") in ["message_changed", "message_deleted"]:
        return {"status": "ok"}

    # 봇 자신이 보낸 메시지는 무시
    if event.get("bot_id"):
        return {"status": "ok"}

    text = event.get("text", "")
    channel_id = event.get("channel", "")
    user_id = event.get("user", "")

    video_ids = extract_youtube_ids(text)
    print(f"🔍 본문: {text}")
    print(f"🔍 추출된 비디오 ID: {video_ids}")

    for v_id in video_ids:
        try:
            res = supabase.table("links").insert({
                "channel_id": channel_id,
                "video_id": v_id,
                "slack_user_id": user_id
            }).execute()
            print(f"✅ [DB 저장 성공] 채널: {channel_id} | 비디오: {v_id}")
        except Exception as e:
            print(f"❌ [DB 저장 실패]: {e}")

    return {"status": "ok"}