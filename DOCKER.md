# Docker 部署指南

本專案支援 Docker 容器化部署，包含 LINE Bot 服務和可選的 Nginx 反向代理。

## 快速開始

### 1. 準備環境變數

```bash
# 複製環境變數範本
cp .env.docker .env

# 編輯 .env 填入 LINE Bot 憑證
nano .env
```

### 2. 啟動服務

```bash
# 僅啟動 LINE Bot
docker-compose up -d

# 啟動 LINE Bot + Nginx 反向代理
docker-compose --profile with-nginx up -d
```

### 3. 查看日誌

```bash
# 查看即時日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f web
```

### 4. 停止服務

```bash
docker-compose down
```

## Docker Compose 架構

### 服務說明

#### web (LINE Bot 主服務)
- **映像**: 自訂建置（基於 Python 3.11）
- **端口**: 5000
- **功能**: 
  - Flask Web 服務
  - LINE Bot Webhook 處理
  - 權證爬蟲功能

#### nginx (反向代理 - 可選)
- **映像**: nginx:alpine
- **端口**: 80, 443
- **功能**:
  - HTTP/HTTPS 反向代理
  - 負載均衡
  - SSL/TLS 終止

### 網路配置

所有服務連接到 `warrant-network` 橋接網路。

## 環境變數

在 `.env` 檔案中設定：

```env
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_CHANNEL_SECRET=your_secret
FLASK_ENV=production
HOST=0.0.0.0
PORT=5000
```

## Volume 掛載

- `./config.json` → `/app/config.json` - 常用查詢設定
- `./logs` → `/app/logs` - 日誌輸出目錄

## 進階用法

### 重新建置映像

```bash
docker-compose build --no-cache
```

### 僅啟動特定服務

```bash
docker-compose up -d web
```

### 進入容器

```bash
docker-compose exec web bash
```

### 查看資源使用

```bash
docker-compose stats
```

## Nginx 設定

如需使用 Nginx 反向代理，請編輯 `nginx.conf`：

### HTTP 模式（預設）
```bash
docker-compose --profile with-nginx up -d
```

### HTTPS 模式
1. 將 SSL 憑證放到 `ssl/` 目錄
2. 取消註解 `nginx.conf` 中的 HTTPS server block
3. 重啟服務

## 生產環境建議

### 1. 使用 HTTPS
```bash
# 放置 SSL 憑證
mkdir -p ssl
cp cert.pem ssl/
cp key.pem ssl/
```

### 2. 限制資源使用
在 `docker-compose.yml` 中加入：
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
```

### 3. 健康檢查
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 4. 日誌輪轉
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 常見問題

### Q: 容器啟動失敗？
```bash
# 查看詳細日誌
docker-compose logs web

# 檢查環境變數
docker-compose config
```

### Q: Playwright 執行錯誤？
確認 Dockerfile 中已安裝所有依賴：
```dockerfile
RUN uv run playwright install-deps chromium
```

### Q: 如何更新設定？
```bash
# 修改 config.json 後重啟
docker-compose restart web
```

### Q: 端口衝突？
修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "5001:5000"  # 改用 5001
```

## 監控與維護

### 日誌位置
- 容器日誌: `docker-compose logs`
- 應用日誌: `./logs/`

### 備份
```bash
# 備份設定
tar -czf backup.tar.gz config.json .env

# 備份日誌
tar -czf logs_backup.tar.gz logs/
```

### 更新
```bash
# 拉取最新程式碼
git pull

# 重新建置並啟動
docker-compose up -d --build
```

## 安全建議

1. ✅ 不要將 `.env` 提交到 Git
2. ✅ 使用強密碼和 Token
3. ✅ 啟用 HTTPS
4. ✅ 定期更新 Docker 映像
5. ✅ 限制容器資源使用
6. ✅ 設定防火牆規則

## 參考資源

- [Docker 官方文件](https://docs.docker.com/)
- [Docker Compose 文件](https://docs.docker.com/compose/)
- [Nginx 設定指南](https://nginx.org/en/docs/)
