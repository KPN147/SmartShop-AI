"""
SmartShop AI - Tool: Check Order
Kiểm tra trạng thái đơn hàng từ mock database.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).parent.parent / "data" / "orders.json"


def _load_orders() -> List[Dict[str, Any]]:
    """Load orders từ JSON file."""
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Không tìm thấy file: {DATA_PATH}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Lỗi parse JSON orders: {e}")
        return []


def check_order(
    order_id: Optional[str] = None,
    phone_number: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Kiểm tra trạng thái đơn hàng theo mã đơn hoặc số điện thoại.
    
    Args:
        order_id: Mã đơn hàng (ví dụ: ORD-2024-001).
        phone_number: Số điện thoại khách hàng.
    
    Returns:
        Thông tin đơn hàng nếu tìm thấy, None nếu không có.
    """
    if not order_id and not phone_number:
        logger.warning("[Tool:check_order] Không cung cấp order_id hoặc phone_number")
        return None

    logger.info(f"[Tool:check_order] order_id='{order_id}', phone='{phone_number}'")
    
    orders = _load_orders()
    
    # Tìm theo order_id (ưu tiên)
    if order_id:
        order_id_clean = order_id.strip().upper()
        for order in orders:
            if order.get("order_id", "").upper() == order_id_clean:
                logger.info(f"[Tool:check_order] Tìm thấy đơn hàng: {order_id_clean}")
                return order
    
    # Tìm theo số điện thoại (trả về đơn hàng mới nhất)
    if phone_number:
        phone_clean = phone_number.strip().replace(" ", "").replace("-", "")
        matched_orders = []
        for order in orders:
            stored_phone = order.get("customer_phone", "").replace(" ", "").replace("-", "")
            if stored_phone == phone_clean:
                matched_orders.append(order)
        
        if matched_orders:
            # Trả về đơn hàng mới nhất (dựa theo order_date)
            matched_orders.sort(key=lambda x: x.get("order_date", ""), reverse=True)
            logger.info(f"[Tool:check_order] Tìm thấy {len(matched_orders)} đơn hàng cho số điện thoại {phone_clean}")
            return matched_orders[0]
    
    logger.info(f"[Tool:check_order] Không tìm thấy đơn hàng nào")
    return None


def format_order_for_llm(order: Dict[str, Any]) -> str:
    """Format thông tin đơn hàng thành chuỗi dễ đọc cho LLM."""
    price_formatted = f"{order.get('total_price', 0):,}đ".replace(",", ".")
    
    tracking_info = ""
    if order.get("tracking_code"):
        tracking_info = f"\n  Mã vận đơn: {order['tracking_code']} ({order.get('shipping_carrier', 'N/A')})"
    
    estimated = order.get("estimated_delivery")
    delivery_info = f"\n  Dự kiến giao: {estimated}" if estimated else ""
    
    return (
        f"📦 **Đơn hàng #{order['order_id']}**\n"
        f"  Khách hàng: {order['customer_name']} | SĐT: {order['customer_phone']}\n"
        f"  Sản phẩm: {order['product_name']} (SL: {order['quantity']})\n"
        f"  Tổng tiền: {price_formatted}\n"
        f"  Trạng thái: **{order['status']}**\n"
        f"  Ngày đặt: {order['order_date']}"
        f"{delivery_info}"
        f"{tracking_info}\n"
        f"  Địa chỉ giao hàng: {order['address']}"
    )
