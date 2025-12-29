from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from agent.stream import generate_sse_stream
from agent.schema.chat import ChatRequest
from api.core.logger import APILogger
from config.settings import get_config


logger = APILogger()
router = APIRouter()
config = get_config()


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    채팅 API 엔드포인트 (SSE 스트리밍)

    Args:
        request: 채팅 요청 (메시지 목록)

    Returns:
        StreamingResponse: SSE 형식의 스트리밍 응답
    """
    try:
        return StreamingResponse(
            generate_sse_stream(request.messages),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"채팅 API 에러: {e}")
        raise HTTPException(status_code=500, detail=str(e))
