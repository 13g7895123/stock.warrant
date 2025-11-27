"""
LINE Bot 主程式
Flask + LINE Bot SDK 實作
"""

import os
import asyncio
import logging
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
from dotenv import load_dotenv

from .commands import parse_command, get_help_message, get_unknown_command_message, validate_stock_code
from .handlers import handle_quick_query, handle_normal_query, handle_outofmoney_query, format_warrant_message


# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# LINE Bot 設定
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    logger.error("請設定 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_CHANNEL_SECRET 環境變數")
    raise ValueError("缺少 LINE Bot 設定")

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/")
def home():
    """健康檢查端點"""
    return "權證查詢 LINE Bot 運行中 ✓", 200


@app.route("/callback", methods=['POST'])
def callback():
    """LINE Bot Webhook 端點"""
    # 取得 X-Line-Signature header
    signature = request.headers.get('X-Line-Signature')
    
    # 取得 request body
    body = request.get_data(as_text=True)
    logger.info(f"收到 webhook 請求: {body}")
    
    # 驗證簽名
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("無效的簽名")
        abort(400)
    
    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理文字訊息"""
    message_text = event.message.text
    reply_token = event.reply_token
    
    logger.info(f"收到訊息: {message_text}")
    
    # 解析指令
    command = parse_command(message_text)
    
    # 處理不同類型的指令
    if command['type'] == 'help':
        reply_text = get_help_message()
        send_reply(reply_token, reply_text)
    
    elif command['type'] == 'unknown':
        reply_text = get_unknown_command_message()
        send_reply(reply_token, reply_text)
    
    elif command['type'] in ['quick', 'normal', 'outofmoney']:
        stock_code = command.get('stock_code')
        
        # 驗證股票代號
        if not validate_stock_code(stock_code):
            reply_text = "❌ 股票代號格式錯誤\n請輸入 4-6 位數字的股票代號"
            send_reply(reply_token, reply_text)
            return
        
        # 先回應處理中訊息
        processing_msg = f"🔄 正在查詢 {stock_code} 的權證資料...\n請稍候片刻"
        send_reply(reply_token, processing_msg)
        
        # 執行查詢（在背景執行）
        max_pages = command.get('max_pages', None)
        asyncio.run(process_query_and_push(
            command['type'],
            stock_code,
            event.source.user_id,
            max_pages
        ))


async def process_query_and_push(query_type: str, stock_code: str, user_id: str, max_pages=None):
    """
    執行查詢並推送結果
    
    Args:
        query_type: 'quick', 'normal' 或 'outofmoney'
        stock_code: 股票代號
        user_id: LINE 用戶 ID
        max_pages: 最大頁數（僅適用於 outofmoney 查詢）
    """
    try:
        # 執行查詢
        if query_type == 'quick':
            result = await handle_quick_query(stock_code)
            reply_text = format_warrant_message(result, "快查")
        elif query_type == 'outofmoney':
            result = await handle_outofmoney_query(stock_code, max_pages)
            reply_text = format_warrant_message(result, "價外")
        else:
            result = await handle_normal_query(stock_code)
            reply_text = format_warrant_message(result, "查詢")
        
        # 推送結果
        push_message(user_id, reply_text)
        
    except Exception as e:
        logger.error(f"查詢處理失敗: {e}", exc_info=True)
        error_msg = f"❌ 查詢失敗\n{str(e)}"
        push_message(user_id, error_msg)


def send_reply(reply_token: str, text: str):
    """回覆訊息"""
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=text)]
                )
            )
        logger.info(f"已回覆訊息: {text[:50]}...")
    except Exception as e:
        logger.error(f"回覆訊息失敗: {e}")


def push_message(user_id: str, text: str):
    """推送訊息"""
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message(
                {
                    'to': user_id,
                    'messages': [TextMessage(text=text)]
                }
            )
        logger.info(f"已推送訊息給 {user_id}: {text[:50]}...")
    except Exception as e:
        logger.error(f"推送訊息失敗: {e}")


def run_bot(host='0.0.0.0', port=5000, debug=False):
    """啟動 Flask 伺服器"""
    logger.info(f"啟動 LINE Bot 伺服器 on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_bot(debug=True)
