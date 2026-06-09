"""
配置管理：双模型 AI（DeepSeek + Kimi）+ 系统设置
"""

import json
import os
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = BASE_DIR / "config" / "settings.json"

AI_PROVIDERS = {
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "key_url": "https://platform.deepseek.com/api_keys",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "kimi": {
        "label": "Kimi (月之暗面)",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
        "key_url": "https://platform.moonshot.cn/console/api-keys",
        "env_key": "MOONSHOT_API_KEY",
    },
}

_DEFAULTS = {
    "AI_MODE": False,
    "AI_PROVIDER": "deepseek",
    "AI_MODEL": "",
    "AI_API_KEYS": {"deepseek": "", "kimi": ""},
}

_settings: dict = {}
_state_lock = threading.RLock()


def _read_settings_file() -> dict:
    s = dict(_DEFAULTS)
    s["AI_API_KEYS"] = dict(_DEFAULTS["AI_API_KEYS"])
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            loaded = json.load(f)
            s.update(loaded)
            if "AI_API_KEYS" in loaded:
                s["AI_API_KEYS"] = {**_DEFAULTS["AI_API_KEYS"], **loaded["AI_API_KEYS"]}
            if s.get("AI_PROVIDER") not in AI_PROVIDERS:
                s["AI_PROVIDER"] = "deepseek"
    return s


def _write_settings_file(settings: dict) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


_settings = _read_settings_file()


def reload_settings() -> None:
    global _settings
    _settings = _read_settings_file()


def save_settings(**updates) -> None:
    global _settings
    current = _read_settings_file()
    current.update(updates)
    _write_settings_file(current)
    _settings = current


# ── AI 查询 API ──

def get_active_provider() -> str:
    return _settings.get("AI_PROVIDER", "deepseek")


def get_provider_info(provider_id: str | None = None) -> dict:
    pid = provider_id or get_active_provider()
    return AI_PROVIDERS[pid]


def get_api_base_url(provider_id: str | None = None) -> str:
    return get_provider_info(provider_id)["base_url"].rstrip("/")


def get_api_model(provider_id: str | None = None) -> str:
    custom = _settings.get("AI_MODEL", "").strip()
    if custom:
        return custom
    return get_provider_info(provider_id)["model"]


def get_api_key(provider_id: str | None = None) -> str:
    pid = provider_id or get_active_provider()
    env_key = AI_PROVIDERS[pid]["env_key"]
    env_val = os.environ.get(env_key, "").strip()
    if env_val:
        return env_val
    generic = os.environ.get("AI_API_KEY", "").strip()
    if generic:
        return generic
    return _settings.get("AI_API_KEYS", {}).get(pid, "").strip()


def is_ai_mode_enabled() -> bool:
    return bool(_settings.get("AI_MODE", False))


def get_all_settings() -> dict:
    return dict(_settings)
