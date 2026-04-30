"""
SmartShop AI - Agent Service (LangGraph Multi-Agent Orchestrator)
Manage execution flow: Manager -> Sales/Support Agent.
"""

import json
import logging
import os
import time
import uuid
from typing import AsyncGenerator, Optional

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from prompts.prompts import (
    MANAGER_SYSTEM_PROMPT,
    SALES_SYSTEM_PROMPT,
    SUPPORT_SYSTEM_PROMPT,
)
from tools.search_product import search_product, format_product_for_llm
from tools.check_order import check_order, format_order_for_llm
from services.rag_service import get_rag_service
from services.sentiment_service import analyze_sentiment
from services.history_service import load_history, save_message
from models.schemas import AgentType, SentimentResult, ChatResponse

logger = logging.getLogger(__name__)


def _build_langchain_history(raw_history: list) -> list:
    """Convert raw history from DB into LangChain message objects."""
    messages = []
    for item in raw_history:
        if item["role"] == "user":
            messages.append(HumanMessage(content=item["content"]))
        else:
            messages.append(AIMessage(content=item["content"]))
    return messages


def _get_llm(provider: str, model: str, streaming: bool = False):
    """Initialize LLM based on provider.
    
    Supports custom base_url for OpenAI-compatible providers (Groq, Together, etc.)
    by reading OPENAI_BASE_URL from .env.
    """
    if provider == "openai":
        base_url = os.getenv("OPENAI_BASE_URL")  # None = use default OpenAI
        return ChatOpenAI(
            model=model,
            temperature=0.7,
            streaming=streaming,
            base_url=base_url,  # Groq: https://api.groq.com/openai/v1
        )
    elif provider == "gemini":
        return ChatGoogleGenerativeAI(model=model, temperature=0.7, streaming=streaming)
    raise ValueError(f"LLM provider không hỗ trợ: {provider}")


async def _route_to_agent(message: str, llm) -> AgentType:
    """
    Use Manager Agent to classify the user question -> route to the appropriate agent.
    
    Returns:
        AgentType (sales_agent or support_agent)
    """
    logger.info(f"[Manager] Routing message: '{message[:60]}...'")
    
    try:
        messages = [
            SystemMessage(content=MANAGER_SYSTEM_PROMPT),
            HumanMessage(content=message)
        ]
        
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        
        # Parse JSON response from Manager
        # Remove markdown code blocks if any
        clean_content = content.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean_content)
        
        agent_name = parsed.get("agent", "sales_agent")
        agent_type = AgentType(agent_name)
        
        logger.info(f"[Manager] Routing → {agent_type}")
        return agent_type

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning(f"[Manager] Error parsing routing response: {e}. Fallback -> sales_agent")
        return AgentType.SALES


async def _run_sales_agent(
    message: str,
    sentiment_label: str,
    session_history: list,
    llm,
) -> str:
    """
    Sales Agent: consult products using Tool Calling.
    """
    logger.info(f"[SalesAgent] Processing: '{message[:60]}...'")
    
    # Search for relevant products
    products = search_product(message, max_results=3)
    
    product_context = ""
    if products:
        product_lines = [format_product_for_llm(p) for p in products]
        product_context = f"\n\n[FOUND PRODUCT INFORMATION]\n" + "\n\n".join(product_lines)
    else:
        product_context = "\n\n[PRODUCT INFORMATION]: No matching products found in the system."

    sentiment_note = f"\n[CUSTOMER SENTIMENT]: {sentiment_label.upper()}"
    
    system_prompt = SALES_SYSTEM_PROMPT + sentiment_note + product_context
    
    messages = [SystemMessage(content=system_prompt)] + session_history + [HumanMessage(content=message)]
    
    try:
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"[SalesAgent] Error calling LLM: {e}", exc_info=True)
        raise


async def _run_support_agent(
    message: str,
    sentiment_label: str,
    session_history: list,
    llm,
    llm_provider: str,
    llm_model: str,
) -> str:
    """
    Support Agent: handle orders and policies.
    Automatically detect intent for order lookup or policy inquiry.
    """
    logger.info(f"[SupportAgent] Processing: '{message[:60]}...'")
    
    context_parts = []
    
    # Check if there is an order ID or phone number in the message
    import re
    order_id_match = re.search(r'ORD[-\s]?\d{4}[-\s]?\d{3,}', message.upper())
    phone_match = re.search(r'0[3-9]\d{8}', message)
    
    if order_id_match or phone_match:
        order_id = order_id_match.group().replace(" ", "-") if order_id_match else None
        phone = phone_match.group() if phone_match else None
        
        order = check_order(order_id=order_id, phone_number=phone)
        if order:
            context_parts.append(f"[ORDER INFORMATION]\n{format_order_for_llm(order)}")
        else:
            context_parts.append("[ORDER INFORMATION]: No order found with the provided information.")
    
    # Check if the question is related to policies
    policy_keywords = ["bảo hành", "đổi trả", "vận chuyển", "hoàn tiền", "trả hàng", 
                       "giao hàng", "phí ship", "chính sách", "quy định", "thanh toán", "trả góp"]
    
    if any(kw in message.lower() for kw in policy_keywords):
        rag_service = get_rag_service(llm_provider=llm_provider, model_name=llm_model)
        policy_answer = await rag_service.query_policy(message)
        context_parts.append(f"[POLICY INFORMATION]\n{policy_answer}")
    
    context = "\n\n".join(context_parts)
    sentiment_note = f"\n[CUSTOMER SENTIMENT]: {sentiment_label.upper()}"
    
    system_prompt = SUPPORT_SYSTEM_PROMPT + sentiment_note
    if context:
        system_prompt += f"\n\n{context}"
    
    messages = [SystemMessage(content=system_prompt)] + session_history + [HumanMessage(content=message)]
    
    try:
        response = await llm.ainvoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"[SupportAgent] Error calling LLM: {e}", exc_info=True)
        raise


async def process_chat(
    message: str,
    session_id: Optional[str] = None,
    llm_provider: str = "openai",
    llm_model: str = "gpt-4o-mini",
) -> ChatResponse:
    """
    Process a chat message through the Multi-Agent pipeline:
    1. Sentiment Analysis
    2. Manager Agent routing
    3. Sales or Support Agent
    4. Update session history
    
    Returns:
        ChatResponse with complete information.
    """
    start_time = time.time()
    
    # Create session ID if not exists
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Load chat history from SQLite (Persistent Memory)
    raw_history = await load_history(session_id, limit=6)
    history = _build_langchain_history(raw_history)
    
    logger.info(f"[AgentService] Processing message | session={session_id} | history_len={len(history)}")
    
    # Step 1: Sentiment Analysis
    sentiment_label, sentiment_score = await analyze_sentiment(message)
    
    # Initialize LLM
    llm = _get_llm(llm_provider, llm_model)
    manager_llm = _get_llm(llm_provider, llm_model)
    
    # Step 2: Manager routing
    agent_type = await _route_to_agent(message, manager_llm)
    
    # Step 3: Run the selected agent
    try:
        if agent_type == AgentType.SALES:
            response_text = await _run_sales_agent(
                message=message,
                sentiment_label=sentiment_label,
                session_history=history,
                llm=llm,
            )
        else:
            response_text = await _run_support_agent(
                message=message,
                sentiment_label=sentiment_label,
                session_history=history,
                llm=llm,
                llm_provider=llm_provider,
                llm_model=llm_model,
            )
    except Exception as e:
        logger.error(f"[AgentService] Critical error: {e}", exc_info=True)
        response_text = "Sorry, I am experiencing a technical issue. Please try again later or contact the hotline 1800-5555."
        agent_type = AgentType.SUPPORT
    
    # Step 4: Save history to SQLite (Persistent)
    await save_message(session_id, "user", message)
    await save_message(session_id, "assistant", response_text)
    
    processing_time = (time.time() - start_time) * 1000
    logger.info(f"[AgentService] Completed | agent={agent_type} | time={processing_time:.0f}ms")
    
    return ChatResponse(
        response=response_text,
        agent_used=agent_type,
        sentiment=SentimentResult(label=sentiment_label, score=sentiment_score),
        session_id=session_id,
        processing_time_ms=round(processing_time, 1),
    )


async def process_chat_stream(
    message: str,
    session_id: Optional[str] = None,
    llm_provider: str = "openai",
    llm_model: str = "gpt-4o-mini",
) -> AsyncGenerator[str, None]:
    """
    Streaming version of process_chat using SSE.
    Yields chunks as Server-Sent Events.
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Load history from SQLite (Persistent Memory)
    raw_history = await load_history(session_id, limit=6)
    history = _build_langchain_history(raw_history)
    
    sentiment_label, sentiment_score = await analyze_sentiment(message)
    manager_llm = _get_llm(llm_provider, llm_model)
    agent_type = await _route_to_agent(message, manager_llm)
    
    # Send metadata first
    meta = json.dumps({
        "type": "meta",
        "agent_used": agent_type.value,
        "sentiment": {"label": sentiment_label, "score": sentiment_score},
        "session_id": session_id,
    }, ensure_ascii=False)
    yield f"data: {meta}\n\n"
    
    # Streaming LLM response
    stream_llm = _get_llm(llm_provider, llm_model, streaming=True)
    
    if agent_type == AgentType.SALES:
        products = search_product(message, max_results=3)
        product_context = ""
        if products:
            product_lines = [format_product_for_llm(p) for p in products]
            product_context = f"\n\n[FOUND PRODUCT INFORMATION]\n" + "\n\n".join(product_lines)
        else:
            product_context = "\n\n[PRODUCT INFORMATION]: No matching products found in the system."
        
        system_prompt = SALES_SYSTEM_PROMPT + f"\n[CUSTOMER SENTIMENT]: {sentiment_label.upper()}" + product_context
    else:
        # ===== BUG FIX: Build context for support agent in streaming mode =====
        import re
        context_parts = []
        
        # Kiểm tra nếu có mã đơn hàng hoặc số điện thoại trong tin nhắn
        order_id_match = re.search(r'ORD[-\s]?\d{4}[-\s]?\d{3,}', message.upper())
        phone_match = re.search(r'0[3-9]\d{8}', message)
        
        if order_id_match or phone_match:
            order_id = order_id_match.group().replace(" ", "-") if order_id_match else None
            phone = phone_match.group() if phone_match else None
            
            order = check_order(order_id=order_id, phone_number=phone)
            if order:
                context_parts.append(f"[ORDER INFORMATION]\n{format_order_for_llm(order)}")
            else:
                context_parts.append("[ORDER INFORMATION]: No order found with the provided information.")
        
        # Check if the question is related to policies (RAG)
        policy_keywords = ["bảo hành", "đổi trả", "vận chuyển", "hoàn tiền", "trả hàng",
                           "giao hàng", "phí ship", "chính sách", "quy định", "thanh toán", "trả góp"]
        
        if any(kw in message.lower() for kw in policy_keywords):
            rag_service = get_rag_service(llm_provider=llm_provider, model_name=llm_model)
            policy_answer = await rag_service.query_policy(message)
            context_parts.append(f"[POLICY INFORMATION]\n{policy_answer}")
        
        context = "\n\n".join(context_parts)
        system_prompt = SUPPORT_SYSTEM_PROMPT + f"\n[CUSTOMER SENTIMENT]: {sentiment_label.upper()}"
        if context:
            system_prompt += f"\n\n{context}"
    
    messages = [SystemMessage(content=system_prompt)] + history[-6:] + [HumanMessage(content=message)]
    
    full_response = ""
    try:
        async for chunk in stream_llm.astream(messages):
            if chunk.content:
                full_response += chunk.content
                chunk_data = json.dumps({"type": "chunk", "content": chunk.content}, ensure_ascii=False)
                yield f"data: {chunk_data}\n\n"
    except Exception as e:
        logger.error(f"[AgentService:stream] Streaming error: {e}", exc_info=True)
        error_data = json.dumps({"type": "error", "content": "Processing error, please try again."})
        yield f"data: {error_data}\n\n"
    
    # Send end signal
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    # Save history to SQLite after streaming finishes
    if full_response:
        await save_message(session_id, "user", message)
        await save_message(session_id, "assistant", full_response)
