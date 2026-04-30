"""
SmartShop AI - Chat Router
Các API endpoints cho chức năng chat.
"""

import logging
import os
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from models.schemas import ChatRequest, ChatResponse, HealthResponse
from services.agent_service import process_chat, process_chat_stream

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


def _get_llm_config() -> tuple[str, str]:
    """Lấy LLM provider và model từ environment variables."""
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "openai":
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    elif provider == "gemini":
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    else:
        logger.warning(f"Provider không rõ: {provider}, fallback về openai")
        provider = "openai"
        model = "gpt-4o-mini"
    
    return provider, model


@router.post(
    "",
    response_model=ChatResponse,
    summary="Gửi tin nhắn chat",
    description="Xử lý tin nhắn qua Multi-Agent pipeline và trả về phản hồi đầy đủ.",
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Endpoint chính cho chat.
    
    - **message**: Nội dung tin nhắn của khách hàng.
    - **session_id**: ID phiên để duy trì lịch sử hội thoại (optional).
    - **stream**: Nếu True, redirect sang SSE endpoint.
    """
    if request.stream:
        raise HTTPException(
            status_code=400,
            detail="Để sử dụng streaming, vui lòng dùng endpoint GET /chat/stream"
        )
    
    provider, model = _get_llm_config()
    
    try:
        logger.info(f"[ChatRouter] Nhận request | provider={provider} | session={request.session_id}")
        response = await process_chat(
            message=request.message,
            session_id=request.session_id,
            llm_provider=provider,
            llm_model=model,
        )
        return response
    except Exception as e:
        logger.error(f"[ChatRouter] Lỗi xử lý chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý: {str(e)}")


@router.get(
    "/stream",
    summary="Chat với SSE Streaming",
    description="Streaming response sử dụng Server-Sent Events (SSE).",
)
async def chat_stream(message: str, session_id: str = None) -> StreamingResponse:
    """
    Endpoint streaming SSE.
    
    Query params:
    - **message**: Nội dung tin nhắn.
    - **session_id**: ID phiên (optional).
    """
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message không được để trống")
    
    provider, model = _get_llm_config()
    
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for chunk in process_chat_stream(
                message=message,
                session_id=session_id,
                llm_provider=provider,
                llm_model=model,
            ):
                yield chunk
        except Exception as e:
            logger.error(f"[ChatRouter:stream] Lỗi generator: {e}", exc_info=True)
            import json
            yield f"data: {json.dumps({'type': 'error', 'content': 'Lỗi server'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
