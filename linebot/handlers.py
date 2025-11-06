"""
權證查詢處理器
處理快查和普查的核心邏輯
"""

import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
import sys

# 加入上層目錄到路徑，以便導入 scraper
sys.path.append(str(Path(__file__).parent.parent))
from scraper import WarrantScraper


logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.json") -> dict:
    """載入設定檔"""
    try:
        config_file = Path(__file__).parent.parent / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"載入設定檔失敗: {e}")
        return {
            "headless": True,
            "max_pages": 3,
            "filter_name": "元大"
        }


async def handle_quick_query(stock_code: str) -> Dict[str, any]:
    """
    快速查詢：使用 config.json 設定
    - filter_name: "元大" (或設定檔中的值)
    - max_pages: 3 (或設定檔中的值)
    - headless: true
    
    Returns:
        {
            'success': bool,
            'warrants': List[Dict],
            'total': int,
            'pages': int,
            'filter': str,
            'error': str (if failed)
        }
    """
    try:
        logger.info(f"執行快速查詢: {stock_code}")
        
        config = load_config('config.json')
        
        scraper = WarrantScraper(
            stock_code=stock_code,
            headless=config.get('headless', True),
            max_pages=config.get('max_pages', 3),
            filter_name=config.get('filter_name', '元大')
        )
        
        await scraper.scrape_all_pages()
        
        result = {
            'success': True,
            'warrants': scraper.warrants,
            'total': len(scraper.warrants),
            'filter': config.get('filter_name', '元大'),
            'max_pages': config.get('max_pages', 3),
            'failed_pages': scraper.failed_pages
        }
        
        logger.info(f"快速查詢完成: 找到 {result['total']} 筆資料")
        return result
        
    except Exception as e:
        logger.error(f"快速查詢失敗: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


async def handle_normal_query(stock_code: str) -> Dict[str, any]:
    """
    普通查詢：查詢全部資料
    - filter_name: None (不篩選)
    - max_pages: None (全部頁面)
    - headless: true
    
    Returns:
        {
            'success': bool,
            'warrants': List[Dict],
            'total': int,
            'pages': int,
            'error': str (if failed)
        }
    """
    try:
        logger.info(f"執行普通查詢: {stock_code}")
        
        scraper = WarrantScraper(
            stock_code=stock_code,
            headless=True,
            max_pages=None,
            filter_name=None
        )
        
        await scraper.scrape_all_pages()
        
        result = {
            'success': True,
            'warrants': scraper.warrants,
            'total': len(scraper.warrants),
            'filter': '無',
            'max_pages': '全部',
            'failed_pages': scraper.failed_pages
        }
        
        logger.info(f"普通查詢完成: 找到 {result['total']} 筆資料")
        return result
        
    except Exception as e:
        logger.error(f"普通查詢失敗: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def format_warrant_message(result: Dict[str, any], query_type: str = "快查") -> str:
    """
    格式化權證查詢結果為 LINE 訊息
    
    Args:
        result: 查詢結果
        query_type: "快查" 或 "查詢"
    
    Returns:
        格式化的訊息字串
    """
    if not result['success']:
        return f"❌ 查詢失敗\n錯誤訊息: {result.get('error', '未知錯誤')}"
    
    warrants = result['warrants']
    total = result['total']
    
    if total == 0:
        return f"🔍 {query_type}結果\n未找到任何權證資料"
    
    # 標題
    if query_type == "快查":
        header = f"🔍 快查結果 ({result['filter']})\n找到 {total} 筆資料（前{result['max_pages']}頁）\n"
    else:
        header = f"🔍 查詢結果\n找到 {total} 筆資料（全部頁面）\n"
    
    header += "=" * 30 + "\n\n"
    
    # 如果資料太多，只顯示前10筆並提示
    display_warrants = warrants[:10]
    
    message_parts = [header]
    
    for i, warrant in enumerate(display_warrants, 1):
        warrant_info = (
            f"📊 {warrant['權證名稱']}\n"
            f"代號: {warrant['代號']} | 價格: {warrant['價格']}\n"
            f"價內外: {warrant['價內外']}\n"
            f"剩餘天數: {warrant['剩餘天數']}\n"
            f"{'─' * 30}\n"
        )
        message_parts.append(warrant_info)
    
    # 如果有更多資料，加上提示
    if total > 10:
        message_parts.append(f"\n⚠️ 僅顯示前 10 筆\n總共 {total} 筆資料")
    
    # 失敗頁面提示
    if result['failed_pages']:
        message_parts.append(f"\n⚠️ 部分頁面爬取失敗: {', '.join(map(str, result['failed_pages']))}")
    
    return ''.join(message_parts)


def format_simple_warrant_list(result: Dict[str, any]) -> str:
    """
    簡化版權證列表（適合資料量大的情況）
    """
    if not result['success']:
        return f"❌ 查詢失敗\n{result.get('error', '未知錯誤')}"
    
    total = result['total']
    if total == 0:
        return "🔍 未找到任何權證資料"
    
    warrants = result['warrants'][:20]  # 只顯示前20筆
    
    lines = [f"🔍 找到 {total} 筆資料\n"]
    
    for warrant in warrants:
        line = f"{warrant['權證名稱']} | {warrant['價格']} | {warrant['價內外']}"
        lines.append(line)
    
    if total > 20:
        lines.append(f"\n... 還有 {total - 20} 筆資料")
    
    return '\n'.join(lines)
