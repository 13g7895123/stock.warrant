"""
指令解析器
解析用戶輸入的 LINE 訊息，判斷指令類型和參數
"""

import re
import logging
from typing import Dict, Optional


logger = logging.getLogger(__name__)


def parse_command(message: str) -> Dict[str, any]:
    """
    解析用戶訊息，返回指令類型和參數
    
    支援的指令格式：
    - "快查 6669" → 快速查詢（元大 + 前3頁）
    - "查詢 2330" → 普通查詢（全部資料）
    - "價外 6669" → 價外查詢（全部頁面）
    - "價外 6669 5" → 價外查詢（指定頁數）
    - "幫助" / "help" → 顯示說明
    
    Returns:
        {
            'type': 'quick' | 'normal' | 'outofmoney' | 'help' | 'unknown',
            'stock_code': str (optional),
            'max_pages': int (optional),
            'raw_message': str
        }
    """
    message = message.strip()
    
    # 快速查詢
    quick_pattern = r'^快查\s+(\d{4,6})$'
    match = re.match(quick_pattern, message)
    if match:
        stock_code = match.group(1)
        logger.info(f"解析到快查指令: {stock_code}")
        return {
            'type': 'quick',
            'stock_code': stock_code,
            'raw_message': message
        }
    
    # 普通查詢
    normal_pattern = r'^查詢\s+(\d{4,6})$'
    match = re.match(normal_pattern, message)
    if match:
        stock_code = match.group(1)
        logger.info(f"解析到查詢指令: {stock_code}")
        return {
            'type': 'normal',
            'stock_code': stock_code,
            'raw_message': message
        }
    
    # 價外查詢（帶頁數參數）
    outofmoney_with_pages_pattern = r'^價外\s+(\d{4,6})\s+(\d+)$'
    match = re.match(outofmoney_with_pages_pattern, message)
    if match:
        stock_code = match.group(1)
        max_pages = int(match.group(2))
        logger.info(f"解析到價外查詢指令: {stock_code}, 頁數: {max_pages}")
        return {
            'type': 'outofmoney',
            'stock_code': stock_code,
            'max_pages': max_pages,
            'raw_message': message
        }
    
    # 價外查詢（不指定頁數，查全部）
    outofmoney_pattern = r'^價外\s+(\d{4,6})$'
    match = re.match(outofmoney_pattern, message)
    if match:
        stock_code = match.group(1)
        logger.info(f"解析到價外查詢指令: {stock_code}, 頁數: 全部")
        return {
            'type': 'outofmoney',
            'stock_code': stock_code,
            'max_pages': None,
            'raw_message': message
        }
    
    # 幫助指令
    if message.lower() in ['幫助', 'help', '說明', '?', '？']:
        return {
            'type': 'help',
            'raw_message': message
        }
    
    # 未知指令
    logger.warning(f"無法識別的指令: {message}")
    return {
        'type': 'unknown',
        'raw_message': message
    }


def get_help_message() -> str:
    """返回幫助訊息"""
    return """
📖 權證查詢機器人使用說明

🔍 快速查詢（元大權證 + 前3頁）
指令: 快查 股票代號
範例: 快查 6669

🔎 完整查詢（全部權證 + 全部頁面）
指令: 查詢 股票代號
範例: 查詢 2330

� 價外查詢（只顯示價外權證）
指令: 價外 股票代號 [頁數]
範例: 
• 價外 6669     （查全部頁面）
• 價外 6669 5   （只查前5頁）

�💡 說明:
• 快查: 篩選元大權證，只查前3頁
• 查詢: 不篩選，查詢所有頁面的權證
• 價外: 只顯示價外權證（價內外<0），可自訂頁數

❓ 需要幫助？
輸入「幫助」查看此說明
"""


def get_unknown_command_message() -> str:
    """返回無法識別指令的訊息"""
    return """
❌ 無法識別的指令

請使用以下格式:
• 快查 6669     （元大權證查詢）
• 查詢 2330     （完整查詢）
• 價外 6669     （價外權證查詢，全部頁面）
• 價外 6669 5   （價外權證查詢，指定頁數）
• 幫助          （查看說明）

💡 股票代號為 4-6 位數字
"""


def validate_stock_code(stock_code: str) -> bool:
    """驗證股票代號格式"""
    if not stock_code:
        return False
    
    # 台股代號通常是 4-6 位數字
    if not stock_code.isdigit():
        return False
    
    if len(stock_code) < 4 or len(stock_code) > 6:
        return False
    
    return True
