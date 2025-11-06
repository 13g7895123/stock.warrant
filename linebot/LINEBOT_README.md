# 權證查詢 LINE Bot

整合權證爬蟲系統的 LINE Bot 機器人

## 功能

### 快速查詢（元大權證）
```
快查 6669
```
- 篩選元大權證
- 只查前 3 頁
- 使用 `config.json` 設定

### 完整查詢（全部權證）
```
查詢 2330
```
- 不篩選券商
- 查詢所有頁面
- 完整資料

### 幫助說明
```
幫助
```

## 設定步驟

### 1. 建立 LINE Bot
1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立 Provider 和 Messaging API Channel
3. 取得 **Channel Access Token** 和 **Channel Secret**

### 2. 設定環境變數
```bash
# 複製範本
cp .env.example .env

# 編輯 .env 填入憑證
nano .env
```

### 3. 安裝依賴
```bash
# 已在專案根目錄安裝
uv add line-bot-sdk flask python-dotenv
```

### 4. 啟動 Bot
```bash
# 開發模式
uv run python -m linebot.bot

# 或使用 Flask 指令
export FLASK_APP=linebot.bot
uv run flask run
```

### 5. 設定 Webhook URL
1. 使用 ngrok 或其他工具建立公開 URL：
```bash
ngrok http 5000
```

2. 在 LINE Developers Console 設定 Webhook URL：
```
https://your-domain.com/callback
```

3. 啟用 Webhook

## 專案結構

```
linebot/
├── __init__.py          # 模組初始化
├── bot.py               # Flask 主程式和 webhook
├── handlers.py          # 查詢處理器（快查/普查）
├── commands.py          # 指令解析器
└── README.md            # 說明文件
```

## 使用範例

### 用戶輸入
```
快查 6669
```

### Bot 回應
```
🔍 快查結果 (元大)
找到 5 筆資料（前3頁）
==============================

📊 緯穎元大59購03
代號: 036805 | 價格: 1.9
價內外: 價外 10.65%
剩餘天數: 315天
──────────────────────────────
...
```

## 部署建議

### 開發環境
- 本機運行 + ngrok

### 生產環境
- **Railway**: 自動部署，免費額度
- **Render**: 免費方案，易於設定
- **Heroku**: 穩定但需付費
- **AWS Lambda**: Serverless 方案

## 故障排除

### Webhook 驗證失敗
- 檢查 `LINE_CHANNEL_SECRET` 是否正確
- 確認 Webhook URL 可公開訪問

### 爬蟲執行失敗
- 確認已安裝 Playwright：`uv run playwright install chromium`
- 檢查 `config.json` 設定檔存在

### 訊息無回應
- 查看日誌輸出
- 確認 `LINE_CHANNEL_ACCESS_TOKEN` 正確
- 檢查 Webhook 是否啟用

## 進階功能（待實作）

- [ ] 用戶個人設定儲存
- [ ] Flex Message 美化回應
- [ ] CSV 檔案匯出
- [ ] 查詢歷史記錄
- [ ] 自訂篩選條件
- [ ] 定時推送功能

## License

MIT
