#!/usr/bin/env python3
"""Deploy xray-node-ws directly to Render using Render REST API.

Usage:
  python tools/deploy-render.py --token <RENDER_API_KEY> [--repo <GITHUB_REPO_URL>] [--uuid <UUID>]
"""
import argparse
import json
import sys
import time
import urllib.request
import uuid

API_BASE = "https://api.render.com/v1"


def get_owner_id(token: str) -> str:
    req = urllib.request.Request(
        f"{API_BASE}/owners?limit=1",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        if not data or not isinstance(data, list):
            raise RuntimeError("Failed to fetch Render owner profile")
        return data[0]["owner"]["id"]


def create_web_service(token: str, owner_id: str, repo: str, vless_uuid: str, name: str = "xray-node-ws") -> dict:
    payload = {
        "type": "web_service",
        "name": name,
        "ownerId": owner_id,
        "repo": repo,
        "branch": "main",
        "autoDeploy": "yes",
        "serviceDetails": {
            "env": "node",
            "plan": "free",
            "region": "oregon",
            "buildCommand": "npm install",
            "startCommand": "npm start",
            "healthCheckPath": "/healthz",
            "envVars": [
                {"key": "UUID", "value": vless_uuid},
                {"key": "WSPATH", "value": "/ws"},
                {"key": "NODE_ENV", "value": "production"},
            ],
        },
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{API_BASE}/services",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def wait_for_service(token: str, service_id: str, timeout: int = 300) -> str:
    print(f"Waiting for deployment to complete on Render (Service: {service_id})...")
    start = time.time()
    while time.time() - start < timeout:
        req = urllib.request.Request(
            f"{API_BASE}/services/{service_id}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                url = data.get("serviceDetails", {}).get("url")
                if url:
                    return url
        except Exception as e:
            print(f"Polling warning: {e}")
        time.sleep(10)
    return ""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--token", required=True, help="Render API Key (rnd_...)")
    p.add_argument("--repo", default="", help="GitHub Repo URL")
    p.add_argument("--uuid", default="", help="VLESS UUID")
    p.add_argument("--name", default="xray-node-ws", help="Service name")
    args = p.parse_args()

    vless_uuid = args.uuid or str(uuid.uuid4())
    print(f"Using UUID: {vless_uuid}")

    try:
        owner_id = get_owner_id(args.token)
        print(f"Authenticated with Render! Owner ID: {owner_id}")
        svc = create_web_service(args.token, owner_id, args.repo, vless_uuid, args.name)
        svc_id = svc["id"]
        print(f"Service created! ID: {svc_id}")
        svc_url = svc.get("serviceDetails", {}).get("url") or wait_for_service(args.token, svc_id)
        print(f"Public URL: {svc_url}")
        print("\n=== Deployment Successful ===")
        print(f"UUID: {vless_uuid}")
        print(f"Domain: {svc_url.replace('https://', '') if svc_url else 'Pending'}")
    except Exception as e:
        print(f"Render API deployment error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
