import re
import ssl
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"}
ctx = ssl.create_default_context()

urls = [
    "https://velixir.com/",
    "https://velixir.com/lander",
    "https://velixir.io/",
    "https://velixir.app/",
    "https://velixir.dev/",
]

for url in urls:
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15, context=ctx)
        body = r.read(30000).decode("utf-8", "ignore")
        title = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
        print(url, "->", r.status, "|", (title.group(1).strip()[:60] if title else "no title"), "| bytes", len(body))
        low = body.lower()
        hits = [k for k in ["for sale", "parked", "buy this domain", "hugedomains", "sedo", "afternic", "sign up", "register"] if k in low]
        print("   keywords:", hits)
    except Exception as e:
        print(url, "-> ERR", type(e).__name__, str(e)[:100])
