"""
SmartShop AI - Sentiment Analysis Service (v2)
Upgrade: Use LLM for more accurate sentiment analysis.
Fallback to keyword-based if LLM is unavailable.
"""

import logging
import os
import re
from typing import Tuple

logger = logging.getLogger(__name__)

# ===== Keyword-based fallback (fast, offline) =====

POSITIVE_KEYWORDS = [
    "tốt", "hay", "tuyệt", "xuất sắc", "hài lòng", "thích", "yêu", "cảm ơn", "ok", "ổn",
    "ngon", "xịn", "đỉnh", "chất", "cool", "vui", "good", "great", "perfect", "love",
    "muốn mua", "quan tâm", "thú vị", "hữu ích", "giúp ích", "cần", "tìm"
]

NEGATIVE_KEYWORDS = [
    "tệ", "xấu", "tức", "giận", "thất vọng", "không hài lòng", "lỗi", "hỏng", "bị lừa",
    "chán", "bực", "khó chịu", "bực bội", "phàn nàn", "khiếu nại", "trả hàng", "hoàn tiền",
    "không nhận", "sai", "nhầm", "muộn", "trễ", "chậm", "bao giờ mới", "mãi không"
]

NEUTRAL_KEYWORDS = [
    "cho hỏi", "thông tin", "hỏi", "cần biết", "như thế nào", "bao nhiêu", "ở đâu",
    "khi nào", "ai", "gì", "là gì", "xem", "check", "kiểm tra", "tra cứu"
]


def _analyze_keyword(text: str) -> Tuple[str, float]:
    """Analyze sentiment using keywords (fallback)."""
    text_lower = text.lower()
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_lower)
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)
    neu_count = sum(1 for kw in NEUTRAL_KEYWORDS if kw in text_lower)
    total = pos_count + neg_count + neu_count

    if total == 0:
        return "neutral", 0.5
    if neg_count > pos_count:
        return "negative", round(min(0.5 + (neg_count / total) * 0.45, 0.95), 2)
    elif pos_count > neg_count:
        return "positive", round(min(0.5 + (pos_count / total) * 0.45, 0.95), 2)
    return "neutral", 0.60


async def _analyze_with_llm(text: str) -> Tuple[str, float]:
    """
    Analyze sentiment using LLM (more accurate than keyword-based).
    Uses LLM provider configured in .env.
    Raises exception if LLM is unavailable -> caller will fallback.
    """
    import json as _json

    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    prompt = (
        "Phân tích cảm xúc của câu sau bằng tiếng Việt.\n"
        "Trả về JSON với format CHÍNH XÁC (không thêm markdown):\n"
        "{\"label\": \"positive\"|\"negative\"|\"neutral\", \"score\": <0.0-1.0>}\n\n"
        f"Câu cần phân tích: \"{text}\"\n\n"
        "Quy tắc:\n"
        "- positive: vui vẻ, hài lòng, khen ngợi, muốn mua, hỏi thông tin tích cực\n"
        "- negative: tức giận, phàn nàn, khiếu nại, thất vọng, chê bai\n"
        "- neutral: câu hỏi trung tính, tra cứu thông tin, không biểu đạt cảm xúc rõ\n"
        "- score: độ tự tin từ 0.5 đến 1.0\n\n"
        "JSON:"
    )

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(model=model, temperature=0, base_url=base_url)
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        llm = ChatGoogleGenerativeAI(model=model, temperature=0)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    from langchain_core.messages import HumanMessage
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    raw = response.content.strip()

    # Clean up if LLM still returns markdown block
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
    parsed = _json.loads(raw)

    label = parsed.get("label", "neutral")
    score = float(parsed.get("score", 0.6))

    if label not in ("positive", "negative", "neutral"):
        label = "neutral"
    score = max(0.0, min(1.0, score))

    return label, round(score, 2)


async def analyze_sentiment(text: str, use_ml: bool = False) -> Tuple[str, float]:
    """
    Analyze sentiment of Vietnamese text.

    Strategy:
    1. Try using LLM (most accurate).
    2. If LLM fails or use_ml=False -> keyword-based (fast, offline).

    Args:
        text: Text to analyze.
        use_ml: Legacy param (kept for backward compatibility). Currently always tries LLM first.

    Returns:
        Tuple (label: "positive"|"negative"|"neutral", score: float 0-1)
    """
    logger.info(f"[SentimentService] Analyzing: '{text[:60]}'")

    try:
        label, score = await _analyze_with_llm(text)
        logger.info(f"[SentimentService] LLM result: {label} ({score})")
        return label, score
    except Exception as e:
        logger.warning(f"[SentimentService] LLM unavailable, fallback to keyword-based: {e}")
        label, score = _analyze_keyword(text)
        logger.info(f"[SentimentService] Keyword-based: {label} ({score})")
        return label, score
