from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from agent.stream import generate_sse_stream
from agent.schema.chat import ChatRequest
from api.core.logger import APILogger
from config.settings import get_config


logger = APILogger()
router = APIRouter()
config = get_config()


@router.post("/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    채팅 API 엔드포인트 (SSE 스트리밍)

    Args:
        request: 채팅 요청 (chat_id + 단일 메시지)

    Returns:
        StreamingResponse: SSE 형식의 스트리밍 응답
    """
    try:
        logger.info(f"채팅 요청 받음 - chat_id: {request.chat_id}, role: {request.message.role}, content: {request.message.content[:100]}...")

        # 현재는 단일 메시지만 처리 (추후 히스토리 관리 추가 예정)
        messages = [request.message]
        logger.info(f"채팅 메시지 목록: {messages}")
        
        background_tasks.add_task(
            save_conversation_after_streaming,
            request,
            response_data,
            completion_event,
        )

        # 채팅 메시지 목록을 리스트로 변환
        return StreamingResponse(
            generate_sse_stream(messages),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "X-Chat-Id": request.chat_id
            }
        )
    except Exception as e:
        logger.error(f"채팅 API 에러: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def save_conversation_after_streaming(
    request: QueryRequest,
    response_data: Dict[str, Any],
    completion_event: asyncio.Event,
):
    """스트리밍 완료 후 대화 저장"""

    try:
        await asyncio.wait_for(completion_event.wait(), timeout=30.0)
    
    except SaveConversationTimeoutError:
        logger.error(
            "\n>>>Streaming 완료 대기 시간이 초과하여 대화내역 저장 실패하였습니다.\n"
        )
        return

    try:
        # ChatHistoryManager를 사용하여 대화 저장
        history_manager = ChatHistoryManager()

        # final_state 형식으로 저장 데이터 구성
        final_state = response_data.get("final_state", {})
        if not final_state:
            # final_state가 없으면 기본 정보로 구성
            final_state = {
                "id": request.chat_id,
                "user_no": request.user_no,
                "chat_id": request.chat_id,
                "room_id": request.room_id,
                "user_query": request.user_query,
                "exe_date": request.exe_date,
                "intents": response_data.get("intents", []),
                "output": response_data.get("content", ""),
                "metadata": response_data.get("metadata", {}),
                "rag_document_ids": response_data.get("rag_document_ids", []),
                "chat_type": response_data.get("chat_type", 0),
            }
        else:
            # final_state에 output 추가
            final_state["output"] = response_data.get("content", "")

        # 대화 저장
        await history_manager.save_conversation(
            chat_id=request.chat_id, final_state=final_state
        )

        logger.debug(f"대화 저장 완료: chat_id={request.chat_id}")

    except Exception as e:
        logger.error(f"대화 저장 실패: {e}")