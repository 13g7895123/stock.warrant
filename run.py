#!/usr/bin/env python3
"""
權證爬蟲執行腳本
預設讀取 config.json 設定檔執行常用查詢
使用 -n 參數可切換為普通查詢模式（無篩選條件）
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# 導入爬蟲類別
from scraper import WarrantScraper


# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.json") -> dict:
    """載入設定檔"""
    try:
        if not os.path.exists(config_path):
            logger.error(f"設定檔不存在: {config_path}")
            logger.info("請先建立 config.json 設定檔，可參考 config.example.json")
            sys.exit(1)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logger.info(f"已載入設定檔: {config_path}")
        return config
    
    except json.JSONDecodeError as e:
        logger.error(f"設定檔格式錯誤: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"載入設定檔失敗: {e}")
        sys.exit(1)


def print_config_info(stock_code: str, config: dict):
    """顯示設定資訊"""
    print("\n" + "="*80)
    print("查詢設定")
    print("="*80)
    print(f"股票代號: {stock_code}")
    print(f"Headless 模式: {config.get('headless', False)}")
    
    max_pages = config.get('max_pages')
    pages_text = '全部' if max_pages is None else f'{max_pages} 頁'
    print(f"爬取頁數: {pages_text}")
    
    filter_name = config.get('filter_name')
    filter_text = '無' if filter_name is None else f'權證名稱包含 "{filter_name}"'
    print(f"篩選條件: {filter_text}")
    print("="*80 + "\n")


async def run_with_config(stock_code: str, config: dict):
    """使用設定檔執行爬蟲"""
    headless = config.get('headless', False)
    max_pages = config.get('max_pages')
    filter_name = config.get('filter_name')
    
    print_config_info(stock_code, config)
    
    scraper = WarrantScraper(stock_code, headless, max_pages, filter_name)
    
    try:
        await scraper.scrape_all_pages()
        scraper.print_results()
    except KeyboardInterrupt:
        logger.info("\n使用者中斷執行")
    except Exception as e:
        logger.error(f"執行過程發生錯誤: {e}", exc_info=True)


async def run_normal_query(stock_code: str):
    """執行普通查詢（無篩選條件）"""
    print("\n" + "="*80)
    print("普通查詢模式（無篩選條件）")
    print("="*80)
    print(f"股票代號: {stock_code}")
    print(f"Headless 模式: True")
    print(f"爬取頁數: 全部")
    print(f"篩選條件: 無")
    print("="*80 + "\n")
    
    scraper = WarrantScraper(stock_code, headless=True, max_pages=None, filter_name=None)
    
    try:
        await scraper.scrape_all_pages()
        scraper.print_results()
    except KeyboardInterrupt:
        logger.info("\n使用者中斷執行")
    except Exception as e:
        logger.error(f"執行過程發生錯誤: {e}", exc_info=True)


async def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description='權證爬蟲執行腳本 - 使用設定檔查詢',
        epilog='範例:\n'
               '  python run.py 6669               # 使用 config.json 設定查詢股票 6669\n'
               '  python run.py 2330 -c my.json    # 使用自訂設定檔查詢股票 2330\n'
               '  python run.py -n 2330            # 普通查詢股票代號 2330（無篩選）',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'stock_code',
        nargs='?',
        type=str,
        help='股票代號'
    )
    
    parser.add_argument(
        '-n', '--normal',
        action='store_true',
        help='普通查詢模式：無任何篩選條件（需搭配 stock_code）'
    )
    
    parser.add_argument(
        '-c', '--config',
        metavar='CONFIG_FILE',
        type=str,
        default='config.json',
        help='指定設定檔路徑（預設: config.json）'
    )
    
    args = parser.parse_args()
    
    # 檢查是否有提供股票代號
    if not args.stock_code:
        parser.error("請提供股票代號")
    
    # 判斷執行模式
    if args.normal:
        # 普通查詢模式
        logger.info(f"執行普通查詢: 股票代號 {args.stock_code}")
        await run_normal_query(args.stock_code)
    else:
        # 設定檔查詢模式
        config = load_config(args.config)
        await run_with_config(args.stock_code, config)


if __name__ == "__main__":
    asyncio.run(main())
