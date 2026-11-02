import os
import zipfile
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY_ZIP = os.path.join(ROOT, "deploy.zip")
DESKTOP_ZIP = os.path.join(os.path.expanduser("~"), "Desktop", "xray-node-ws-deploy.zip")

FILES_TO_PACK = [
    "server.js",
    "package.json",
    "Dockerfile",
    ".dockerignore",
    ".env.example",
    "README.md",
    "scripts/install-xray.js",
    "tools/make-vless-qr.py",
]

print("Packaging deployment files...")
with zipfile.ZipFile(DEPLOY_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
    for rel_path in FILES_TO_PACK:
        full_path = os.path.join(ROOT, rel_path.replace("/", os.sep))
        if os.path.exists(full_path):
            z.write(full_path, rel_path)
            print(f"  + Added: {rel_path} ({os.path.getsize(full_path)} bytes)")
        else:
            print(f"  ! Warning: {rel_path} not found")

try:
    shutil.copy2(DEPLOY_ZIP, DESKTOP_ZIP)
    print(f"Copied to Desktop: {DESKTOP_ZIP}")
except Exception as e:
    print(f"Desktop copy skipped: {e}")

print(f"Created: {DEPLOY_ZIP} (Size: {os.path.getsize(DEPLOY_ZIP)} bytes)")
