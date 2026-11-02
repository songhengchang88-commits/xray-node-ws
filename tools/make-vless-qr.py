#!/usr/bin/env python3
"""Build a VLESS/WS/TLS share link and render it as a QR code PNG.

Example:
  python tools/make-vless-qr.py --host node.example.com --port 443 \
      --uuid 11111111-2222-3333-4444-555555555555 --path /ws --name my-node
"""
import argparse
import urllib.parse

import qrcode


def build_link(host: str, port: int, uuid: str, path: str, name: str, sni: str | None, fp: str) -> str:
    query = {
        "encryption": "none",
        "security": "tls",
        "sni": sni or host,
        "fp": fp,
        "type": "ws",
        "host": host,
        "path": path,
    }
    qs = urllib.parse.urlencode(query, quote_via=urllib.parse.quote, safe="")
    return f"vless://{uuid}@{host}:{port}?{qs}#{urllib.parse.quote(name)}"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", required=True, help="public domain of the app")
    p.add_argument("--port", type=int, default=443)
    p.add_argument("--uuid", required=True, help="VLESS client id")
    p.add_argument("--path", default="/ws", help="websocket path")
    p.add_argument("--name", default="my-node", help="profile name shown in client")
    p.add_argument("--sni", default=None, help="defaults to --host")
    p.add_argument("--fp", default="chrome", help="utls fingerprint")
    p.add_argument("--out", default="vless-qr.png")
    a = p.parse_args()

    link = build_link(a.host, a.port, a.uuid, a.path, a.name, a.sni, a.fp)
    img = qrcode.make(link)
    img.save(a.out)
    print(link)
    print(f"saved {a.out}")


if __name__ == "__main__":
    main()
