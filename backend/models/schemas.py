"""
SmartShop AI - Pydantic Schemas
Validate tất cả requests và responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class AgentType(str, Enum):
    SALES = "sales_agent"
    SUPPORT = "support_agent"
    MANAGER = "manager_agent"


# ===== REQUEST SCHEMAS =====

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Tin nhắn của người dùng")
    session_id: Optional[str] = Field(default=None, description="ID phiên chat để duy trì context")
    stream: bool = Field(default=False, description="Bật streaming response (SSE)")

    model_config = {"json_schema_extra": {"example": {"message": "Tôi muốn mua iPhone 15, bạn có thể tư vấn không?", "session_id": "user-123", "stream": False}}}


# ===== RESPONSE SCHEMAS =====

class SentimentResult(BaseModel):
    label: SentimentLabel
    score: float = Field(..., ge=0.0, le=1.0, description="Độ tin cậy từ 0 đến 1")


class ProductInfo(BaseModel):
    id: str
    name: str
    category: str
    brand: str
    price: int
    stock: int
    description: str
    rating: float
    tags: List[str]


class OrderInfo(BaseModel):
    order_id: str
    customer_name: str
    customer_phone: str
    product_name: str
    quantity: int
    total_price: int
    status: str
    shipping_carrier: Optional[str] = None
    tracking_code: Optional[str] = None
    order_date: str
    estimated_delivery: Optional[str] = None
    address: str


class ChatResponse(BaseModel):
    response: str = Field(..., description="Câu trả lời từ AI")
    agent_used: AgentType = Field(..., description="Agent đã xử lý câu hỏi")
    sentiment: SentimentResult = Field(..., description="Kết quả phân tích cảm xúc")
    session_id: str = Field(..., description="ID phiên chat")
    processing_time_ms: Optional[float] = Field(default=None, description="Thời gian xử lý (ms)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "response": "iPhone 15 Pro Max là lựa chọn tuyệt vời với chip A17 Pro và camera 48MP!",
                "agent_used": "sales_agent",
                "sentiment": {"label": "positive", "score": 0.85},
                "session_id": "user-123",
                "processing_time_ms": 1250.5
            }
        }
    }


class StreamChunk(BaseModel):
    """Chunk data cho SSE streaming"""
    content: str
    is_final: bool = False
    agent_used: Optional[AgentType] = None
    sentiment: Optional[SentimentResult] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    services: dict


# ===== TOOL SCHEMAS (cho LLM Tool Calling) =====

class SearchProductInput(BaseModel):
    query: str = Field(..., description="Từ khóa tìm kiếm sản phẩm (tên, category, brand, tính năng)")
    max_results: int = Field(default=3, ge=1, le=10, description="Số lượng kết quả tối đa")


class CheckOrderInput(BaseModel):
    order_id: Optional[str] = Field(default=None, description="Mã đơn hàng (ví dụ: ORD-2024-001)")
    phone_number: Optional[str] = Field(default=None, description="Số điện thoại khách hàng")


class SearchPolicyInput(BaseModel):
    query: str = Field(..., description="Câu hỏi về chính sách (bảo hành, đổi trả, vận chuyển)")
