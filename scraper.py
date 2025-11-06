#!/usr/bin/env python3
"""
權證資訊爬蟲系統
從 HiStock 網站爬取指定股票代號的所有權證資料
"""

import argparse
import asyncio
import logging
import random
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser


# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class WarrantScraper:
    """權證資訊爬蟲"""
    
    BASE_URL = "https://histock.tw/stock/warrant.aspx"
    MAX_RETRIES = 3
    
    def __init__(self, stock_code: str, headless: bool = False):
        self.stock_code = stock_code
        self.headless = headless
        self.warrants: List[Dict[str, str]] = []
        self.failed_pages: List[int] = []
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    def build_url(self, page_number: int) -> str:
        """構建指定頁碼的 URL"""
        return f"{self.BASE_URL}?no={self.stock_code}&r=15&p={page_number}&d=1"
    
    async def init_browser(self):
        """初始化瀏覽器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        logger.info(f"瀏覽器已啟動 (headless={self.headless})")
    
    async def close_browser(self):
        """關閉瀏覽器"""
        if self.browser:
            await self.browser.close()
            logger.info("瀏覽器已關閉")
    
    async def get_last_page_number(self) -> Optional[int]:
        """取得最後一頁的頁碼"""
        try:
            # 尋找「最後一頁」元素（通常在分頁區域）
            # 根據 HiStock 網站結構，最後一頁連結通常包含 "Last" 或最大頁碼
            last_page_link = await self.page.query_selector('a[title*="最後"] , a:has-text("末頁"), a:has-text("Last")')
            
            if last_page_link:
                href = await last_page_link.get_attribute('href')
                if href and 'p=' in href:
                    # 從 URL 中提取頁碼
                    page_num = href.split('p=')[1].split('&')[0]
                    return int(page_num)
            
            # 備選方案：尋找所有分頁連結中的最大數字
            page_links = await self.page.query_selector_all('a[href*="p="]')
            max_page = 1
            for link in page_links:
                href = await link.get_attribute('href')
                if href and 'p=' in href:
                    try:
                        page_num = int(href.split('p=')[1].split('&')[0])
                        max_page = max(max_page, page_num)
                    except (ValueError, IndexError):
                        continue
            
            return max_page if max_page > 1 else None
            
        except Exception as e:
            logger.warning(f"無法取得最後一頁頁碼: {e}")
            return None
    
    async def extract_warrant_data(self) -> List[Dict[str, str]]:
        """從當前頁面擷取權證資料"""
        warrants = []
        
        try:
            # 等待表格載入
            await self.page.wait_for_selector('table', timeout=10000)
            
            # 尋找包含權證資料的表格
            # 通常是 id 包含 "warrant" 或 class 包含 "data" 的表格
            table = await self.page.query_selector('table#GCWT1, table.tbl, table[id*="warrant"]')
            
            if not table:
                # 嘗試尋找第一個有資料的表格
                table = await self.page.query_selector('table')
            
            if not table:
                logger.warning("找不到權證表格")
                return warrants
            
            # 取得所有資料行（跳過標題行）
            rows = await table.query_selector_all('tr')
            
            for row in rows[1:]:  # 跳過標題行
                try:
                    cells = await row.query_selector_all('td')
                    
                    if len(cells) < 5:
                        continue
                    
                    # 提取各欄位資料
                    warrant_name = await cells[0].inner_text()
                    warrant_code = await cells[1].inner_text()
                    price = await cells[2].inner_text()
                    moneyness = await cells[3].inner_text()  # 價內外程度
                    remaining_days = await cells[4].inner_text()
                    
                    # 清理資料
                    warrant_data = {
                        '權證名稱': warrant_name.strip(),
                        '代號': warrant_code.strip(),
                        '價格': price.strip(),
                        '價內外': moneyness.strip(),
                        '剩餘天數': remaining_days.strip()
                    }
                    
                    warrants.append(warrant_data)
                    
                except Exception as e:
                    logger.debug(f"跳過無效的資料行: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"擷取權證資料時發生錯誤: {e}")
        
        return warrants
    
    async def scrape_page_with_retry(self, page_number: int) -> List[Dict[str, str]]:
        """爬取指定頁面，包含重試機制"""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                url = self.build_url(page_number)
                logger.debug(f"正在訪問: {url} (嘗試 {attempt}/{self.MAX_RETRIES})")
                
                await self.page.goto(url, wait_until='networkidle', timeout=30000)
                
                # 擷取資料
                warrants = await self.extract_warrant_data()
                
                return warrants
                
            except Exception as e:
                logger.warning(f"第 {page_number} 頁爬取失敗 (嘗試 {attempt}/{self.MAX_RETRIES}): {e}")
                
                if attempt < self.MAX_RETRIES:
                    # 隨機延遲 1-3 秒後重試
                    delay = random.uniform(1, 3)
                    logger.info(f"等待 {delay:.1f} 秒後重試...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"第 {page_number} 頁爬取失敗，已達最大重試次數")
                    self.failed_pages.append(page_number)
                    return []
        
        return []
    
    async def scrape_all_pages(self):
        """爬取所有頁面的權證資料"""
        await self.init_browser()
        
        try:
            page_number = 1
            last_page = None
            
            while True:
                logger.info(f"正在處理第 {page_number} 頁...")
                
                # 爬取當前頁面
                page_warrants = await self.scrape_page_with_retry(page_number)
                
                # 如果是第一頁，嘗試取得總頁數
                if page_number == 1 and last_page is None:
                    last_page = await self.get_last_page_number()
                    if last_page:
                        logger.info(f"偵測到總共有 {last_page} 頁")
                
                # 累積資料
                if page_warrants:
                    self.warrants.extend(page_warrants)
                    progress_info = f"第 {page_number}"
                    if last_page:
                        progress_info += f"/{last_page}"
                    progress_info += f" 頁，累計 {len(self.warrants)} 筆"
                    logger.info(progress_info)
                else:
                    # 如果當前頁面沒有資料，視為已到達最後
                    logger.info(f"第 {page_number} 頁無資料，停止爬取")
                    break
                
                # 判斷是否繼續
                if last_page and page_number >= last_page:
                    logger.info(f"已到達最後一頁 (第 {last_page} 頁)")
                    break
                
                page_number += 1
                
                # 頁面之間短暫延遲，避免請求過快
                await asyncio.sleep(0.5)
                
        finally:
            await self.close_browser()
    
    def print_results(self):
        """輸出爬取結果"""
        print("\n" + "="*80)
        print("權證資料爬取結果")
        print("="*80)
        
        if not self.warrants:
            print("未找到任何權證資料")
            return
        
        # 輸出標題
        print("權證名稱,代號,價格,價內外,剩餘天數")
        print("-"*80)
        
        # 輸出每筆資料
        for warrant in self.warrants:
            print(f"{warrant['權證名稱']},{warrant['代號']},{warrant['價格']},{warrant['價內外']},{warrant['剩餘天數']}")
        
        # 統計資訊
        print("="*80)
        print(f"統計資訊:")
        print(f"  總筆數: {len(self.warrants)}")
        
        if self.failed_pages:
            print(f"  失敗頁數: {len(self.failed_pages)} ({', '.join(map(str, self.failed_pages))})")
        else:
            print(f"  失敗頁數: 0")
        
        print("="*80 + "\n")


async def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description='權證資訊爬蟲 - 從 HiStock 爬取指定股票的權證資料'
    )
    parser.add_argument(
        'stock_code',
        type=str,
        help='股票代號 (例如: 6669)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='使用 headless 模式執行 (背景執行，不顯示瀏覽器視窗)'
    )
    
    args = parser.parse_args()
    
    logger.info(f"開始爬取股票代號: {args.stock_code}")
    
    scraper = WarrantScraper(args.stock_code, args.headless)
    
    try:
        await scraper.scrape_all_pages()
        scraper.print_results()
    except KeyboardInterrupt:
        logger.info("\n使用者中斷執行")
    except Exception as e:
        logger.error(f"執行過程發生錯誤: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
