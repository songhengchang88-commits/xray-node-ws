const fs = require("fs");
const path = require("path");
const os = require("os");
const https = require("https");
const AdmZip = require("adm-zip");

const BIN_DIR = path.join(__dirname, "..", "bin");
const BIN = path.join(BIN_DIR, "xray");
const REPO = "XTLS/Xray-core";

function get(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { "User-Agent": "xray-node-ws" } }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        res.resume();
        return get(res.headers.location).then(resolve, reject);
      }
      if (res.statusCode !== 200) {
        res.resume();
        return reject(new Error("HTTP " + res.statusCode + " for " + url));
      }
      const chunks = [];
      res.on("data", (c) => chunks.push(c));
      res.on("end", () => resolve(Buffer.concat(chunks)));
    }).on("error", reject);
  });
}

async function main() {
  if (process.platform !== "linux") {
    console.log("[install-xray] non-linux host (" + process.platform + "), skipping binary download");
    return;
  }
  if (fs.existsSync(BIN)) {
    console.log("[install-xray] binary already present");
    return;
  }
  const pinned = process.env.XRAY_VERSION;
  let tag, assetName, assetUrl;
  if (pinned) {
    tag = pinned;
    assetName = "Xray-linux-64.zip";
    assetUrl = "https://github.com/" + REPO + "/releases/download/" + tag + "/" + assetName;
  } else {
    try {
      const rel = JSON.parse((await get("https://api.github.com/repos/" + REPO + "/releases/latest")).toString());
      tag = rel.tag_name;
      const asset = (rel.assets || []).find((a) => /^Xray-linux-64\.zip$/.test(a.name));
      if (!asset) throw new Error("linux-64 asset not found in " + tag);
      assetName = asset.name;
      assetUrl = asset.browser_download_url;
    } catch (apiErr) {
      console.warn("[install-xray] GitHub API lookup failed (" + apiErr.message + "), falling back to pinned release");
      tag = "v25.1.30";
      assetName = "Xray-linux-64.zip";
      assetUrl = "https://github.com/" + REPO + "/releases/download/" + tag + "/" + assetName;
    }
  }
  console.log("[install-xray] downloading " + tag + " / " + assetName);
  const zipBuf = await get(assetUrl);
  fs.mkdirSync(BIN_DIR, { recursive: true });
  const zip = new AdmZip(zipBuf);
  zip.extractAllTo(BIN_DIR, true);
  if (!fs.existsSync(BIN)) throw new Error("xray binary not found after extract");
  fs.chmodSync(BIN, 0o755);
  console.log("[install-xray] ready: " + BIN + " (" + tag + ")");
}

main().catch((e) => {
  console.error("[install-xray] failed: " + e.message);
  process.exit(1);
});
