# xray-node-ws

在 Node.js PaaS（Velixir / Render / Railway 等）上跑 **VLESS + WebSocket + TLS**。
Node 进程只做两件事：响应健康检查、把 `/ws` 的 WebSocket 升级流量原样转发给本机的 Xray-core。
TLS 由平台边缘（https 域名）终结，所以客户端用 `security=tls` + `443` + `sni=你的域名`。

## 文件

- `server.js` — HTTP 服务 + WS 转发 + 拉起 Xray
- `scripts/install-xray.js` — 安装时从 GitHub Releases 拉 `Xray-linux-64.zip`（postinstall）
- `tools/make-vless-qr.py` — 生成 vless:// 链接和二维码 PNG
- `test/e2e-local.py` — 本地回环链路测试
- `test/e2e-inet.py` — 经代理访问公网的真实连通测试

## 环境变量

| 变量 | 必填 | 说明 |
| --- | --- | --- |
| `UUID` | 是 | VLESS 用户 ID，用 `uuidgen` 或在线生成 v4 UUID |
| `WSPATH` | 否 | WebSocket 路径，默认 `/ws`，建议改成随机串如 `/a7f3c9` |
| `PORT` | 否 | 平台注入的端口，默认 3000 |
| `XRAY_PORT` | 否 | Xray 内部监听端口，默认 10000，不对外暴露 |
| `XRAY_VERSION` | 否 | 固定 Xray 版本，如 `v26.10.31`；不填则取 latest |
| `XRAY_BIN` | 否 | 覆盖二进制路径（本地测试用） |

## 平台设置

- Build：`npm install`（会触发 postinstall 下载 Xray）
- Start：`npm start`
- Health check path：`/`
- 如果平台构建阶段禁止外网，把 `XRAY_VERSION` 设好重试，或改用 Docker 构建
- 端口必须走平台给的 `PORT`，不要写死

## 生成分享链接和二维码

```bash
python tools/make-vless-qr.py \
  --host your-app.example.com \
  --port 443 \
  --uuid <UUID> \
  --path /ws \
  --name my-node \
  --out vless-qr.png
```

输出形如：

```
vless://<UUID>@your-app.example.com:443?encryption=none&security=tls&sni=your-app.example.com&fp=chrome&type=ws&host=your-app.example.com&path=%2Fws#my-node
```

Shadowrocket：扫码即导入；也可手动「类型 VLESS / 地址 / 端口 443 / UUID / 传输 ws / 路径 / TLS 开 / SNI」。

## 本地验证

```bash
python test/e2e-local.py   # 回环：直连 Xray 与经 Node 转发
python test/e2e-inet.py    # 公网：经代理访问 gstatic / github / cloudflare
```
