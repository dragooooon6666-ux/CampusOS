"""系统设置 API — AI 配置 + 监控源"""

import json
import urllib.request
from fastapi import APIRouter, HTTPException

from backend.config import (
    get_all_settings, save_settings, get_provider_info,
    get_active_provider, AI_PROVIDERS,
)
from backend.database import get_db

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/ai")
def get_ai_config():
    s = get_all_settings()
    providers = {}
    for pid, info in AI_PROVIDERS.items():
        providers[pid] = {
            "label": info["label"],
            "model": info["model"],
            "key_url": info["key_url"],
            "has_key": bool(s.get("AI_API_KEYS", {}).get(pid, "")),
        }
    return {
        "active_provider": get_active_provider(),
        "ai_mode": s.get("AI_MODE", False),
        "custom_model": s.get("AI_MODEL", ""),
        "providers": providers,
    }


@router.put("/ai")
def update_ai_config(data: dict):
    updates = {}
    if "active_provider" in data:
        pid = data["active_provider"]
        if pid not in AI_PROVIDERS:
            raise HTTPException(400, f"不支持的模型: {pid}")
        updates["AI_PROVIDER"] = pid
    if "ai_mode" in data:
        updates["AI_MODE"] = bool(data["ai_mode"])
    if "custom_model" in data:
        updates["AI_MODEL"] = data["custom_model"].strip()
    if "api_key" in data and "provider" in data:
        keys = get_all_settings().get("AI_API_KEYS", {})
        keys[data["provider"]] = data["api_key"].strip()
        updates["AI_API_KEYS"] = keys

    if updates:
        save_settings(**updates)
    return {"status": "ok"}


@router.post("/ai/test")
def test_ai_connection(data: dict):
    """测试 AI 连接"""
    provider_id = data.get("provider", get_active_provider())
    api_key = data.get("api_key", "").strip()

    info = AI_PROVIDERS[provider_id]
    if not api_key:
        from backend.config import get_api_key
        api_key = get_api_key(provider_id)

    if not api_key:
        return {"ok": False, "error": "未配置 API Key"}

    url = f"{info['base_url'].rstrip('/')}/chat/completions"
    payload = {
        "model": info["model"],
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 5,
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return {"ok": True, "model": body.get("model", info["model"])}
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        return {"ok": False, "error": f"HTTP {e.code}: {detail}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
