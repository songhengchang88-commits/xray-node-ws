const http = require("http");
const net = require("net");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const PORT = Number(process.env.PORT || 3000);
let WSPATH = process.env.WSPATH || "/ws";
if (!WSPATH.startsWith("/")) WSPATH = "/" + WSPATH;
const UUID = process.env.UUID;
const XRAY_HOST = "127.0.0.1";
const XRAY_PORT = Number(process.env.XRAY_PORT || 10000);
const DEFAULT_BIN = path.join(__dirname, "bin", process.platform === "win32" ? "xray.exe" : "xray");
const BIN = process.env.XRAY_BIN || DEFAULT_BIN;
const RUNTIME = path.join(__dirname, "runtime");

if (!UUID) {
  console.error("[fatal] env UUID is required (VLESS client id)");
  process.exit(1);
}

function writeConfig() {
  fs.mkdirSync(RUNTIME, { recursive: true });
  const cfg = {
    log: { loglevel: "warning" },
    inbounds: [
      {
        listen: XRAY_HOST,
        port: XRAY_PORT,
        protocol: "vless",
        settings: {
          clients: [{ id: UUID }],
          decryption: "none"
        },
        streamSettings: {
          network: "ws",
          wsSettings: { path: WSPATH }
        }
      }
    ],
    outbounds: [{ protocol: "freedom", settings: {} }]
  };
  const file = path.join(RUNTIME, "config.json");
  fs.writeFileSync(file, JSON.stringify(cfg, null, 2));
  return file;
}

let xray = null;
function startXray() {
  if (!fs.existsSync(BIN)) {
    console.error("[warn] xray binary missing at " + BIN + "; run npm install/postinstall");
    return;
  }
  const cfgFile = writeConfig();
  xray = spawn(BIN, ["-c", cfgFile], { stdio: "inherit" });
  xray.on("exit", (code, sig) => {
    console.error("[xray] exited code=" + code + " signal=" + sig);
  });
}

const server = http.createServer((req, res) => {
  if (req.url === "/" || req.url === "/healthz") {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("ok");
    return;
  }
  res.writeHead(404, { "Content-Type": "text/plain" });
  res.end("not found");
});

server.on("upgrade", (req, socket, head) => {
  const reqPath = (req.url || "").split("?")[0];
  if (reqPath !== WSPATH) {
    socket.destroy();
    return;
  }
  const upstream = net.connect(XRAY_PORT, XRAY_HOST, () => {
    let raw = req.method + " " + req.url + " HTTP/1.1\r\n";
    for (let i = 0; i < req.rawHeaders.length; i += 2) {
      raw += req.rawHeaders[i] + ": " + req.rawHeaders[i + 1] + "\r\n";
    }
    raw += "\r\n";
    upstream.write(raw);
    if (head && head.length) upstream.write(head);
    socket.pipe(upstream).pipe(socket);
  });
  upstream.on("error", (e) => {
    console.error("[proxy] upstream error: " + e.message);
    socket.destroy();
  });
  socket.on("error", () => upstream.destroy());
});

startXray();
server.listen(PORT, "0.0.0.0", () => {
  console.log("[node] listening on " + PORT + ", ws path " + WSPATH);
});

function shutdown() {
  if (xray) xray.kill("SIGTERM");
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(0), 3000);
}
process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);

