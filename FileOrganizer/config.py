"""
项目配置管理

支持 OpenAI / DeepSeek / Kimi 三家模型，托盘菜单配置 API Key。
"""

import json
import os
import threading
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
_SETTINGS_FILE = _BASE_DIR / "config" / "settings.json"
_EXAMPLE_FILE = _BASE_DIR / "config" / "settings.example.json"

# 三家均兼容 OpenAI Chat Completions 接口
AI_PROVIDERS = {
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "key_url": "https://platform.openai.com/api-keys",
        "env_key": "OPENAI_API_KEY",
    },
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "key_url": "https://platform.deepseek.com/api_keys",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "kimi": {
        "label": "Kimi",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
        "key_url": "https://platform.moonshot.cn/console/api-keys",
        "env_key": "MOONSHOT_API_KEY",
    },
}

_DEFAULTS = {
    "AI_MODE": False,
    "AI_PROVIDER": "openai",
    "AI_MODEL": "",
    "AI_API_KEYS": {
        "openai": "",
        "deepseek": "",
        "kimi": "",
    },
}

_settings: dict = {}
AI_MODE: bool = False
AI_PROVIDER: str = "openai"
AI_MODEL: str = ""
_state_lock = threading.RLock()


def _migrate_legacy_settings(settings: dict) -> dict:
    """兼容旧版 OPENAI_API_KEY 配置。"""
    if settings.get("OPENAI_API_KEY") and not settings.get("AI_API_KEYS"):
        settings["AI_API_KEYS"] = {
            "openai": settings.get("OPENAI_API_KEY", ""),
            "deepseek": "",
            "kimi": "",
        }

    keys = settings.setdefault("AI_API_KEYS", dict(_DEFAULTS["AI_API_KEYS"]))
    for provider_id in AI_PROVIDERS:
        keys.setdefault(provider_id, "")

    if settings.get("OPENAI_API_KEY") and not keys.get("openai"):
        keys["openai"] = settings["OPENAI_API_KEY"]

    if settings.get("AI_PROVIDER") not in AI_PROVIDERS:
        settings["AI_PROVIDER"] = "openai"

    return settings


def _read_settings_file() -> dict:
    settings = dict(_DEFAULTS)
    settings["AI_API_KEYS"] = dict(_DEFAULTS["AI_API_KEYS"])

    if _SETTINGS_FILE.exists():
        with open(_SETTINGS_FILE, encoding="utf-8") as file:
            settings.update(json.load(file))

    return _migrate_legacy_settings(settings)


def _write_settings_file(settings: dict) -> None:
    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, indent=2, ensure_ascii=False)


def _apply_settings(settings: dict) -> None:
    global AI_MODE, AI_PROVIDER, AI_MODEL

    with _state_lock:
        _settings.clear()
        _settings.update(settings)
        AI_MODE = bool(settings["AI_MODE"])
        AI_PROVIDER = str(settings["AI_PROVIDER"])
        AI_MODEL = str(settings.get("AI_MODEL", "")).strip()


def reload_settings() -> None:
    with _state_lock:
        _apply_settings(_read_settings_file())


def save_settings(**updates) -> None:
    with _state_lock:
        settings = _read_settings_file()
        settings.update(updates)
        _write_settings_file(settings)
        _apply_settings(settings)


_apply_settings(_read_settings_file())


def get_provider_ids() -> list[str]:
    return list(AI_PROVIDERS.keys())


def get_provider_info(provider_id: str | None = None) -> dict:
    provider_id = provider_id or get_ai_provider()
    return AI_PROVIDERS[provider_id]


def get_provider_label(provider_id: str | None = None) -> str:
    return get_provider_info(provider_id)["label"]


def get_ai_provider() -> str:
    with _state_lock:
        provider = str(_settings.get("AI_PROVIDER", "openai"))
        return provider if provider in AI_PROVIDERS else "openai"


def set_ai_provider(provider_id: str) -> None:
    if provider_id not in AI_PROVIDERS:
        raise ValueError(f"不支持的模型: {provider_id}")
    save_settings(AI_PROVIDER=provider_id)


def get_api_base_url(provider_id: str | None = None) -> str:
    return get_provider_info(provider_id)["base_url"].rstrip("/")


def get_api_model(provider_id: str | None = None) -> str:
    with _state_lock:
        custom_model = str(_settings.get("AI_MODEL", "")).strip()
        if custom_model:
            return custom_model
    return get_provider_info(provider_id)["model"]


def is_ai_mode_enabled() -> bool:
    with _state_lock:
        return bool(AI_MODE)


def set_ai_mode(enabled: bool) -> None:
    save_settings(AI_MODE=enabled)


def toggle_ai_mode() -> bool:
    new_value = not is_ai_mode_enabled()
    set_ai_mode(new_value)
    return new_value


def get_ai_api_key(provider_id: str | None = None) -> str:
    provider_id = provider_id or get_ai_provider()
    env_name = AI_PROVIDERS[provider_id]["env_key"]
    env_key = os.environ.get(env_name, "").strip()
    if env_key:
        return env_key

    generic_key = os.environ.get("AI_API_KEY", "").strip()
    if generic_key:
        return generic_key

    with _state_lock:
        keys = _settings.get("AI_API_KEYS", {})
        return str(keys.get(provider_id, "")).strip()


def has_api_key(provider_id: str | None = None) -> bool:
    # get_ai_api_key 内部已有锁，无需重复加锁
    return bool(get_ai_api_key(provider_id))


def set_ai_api_key(api_key: str, provider_id: str | None = None) -> None:
    provider_id = provider_id or get_ai_provider()
    settings = _read_settings_file()
    keys = settings.setdefault("AI_API_KEYS", dict(_DEFAULTS["AI_API_KEYS"]))
    keys[provider_id] = api_key.strip()
    save_settings(AI_API_KEYS=keys)


def clear_ai_api_key(provider_id: str | None = None) -> None:
    set_ai_api_key("", provider_id)


def save_ai_config(provider_id: str, api_key: str, model: str = "") -> None:
    settings = _read_settings_file()
    keys = settings.setdefault("AI_API_KEYS", dict(_DEFAULTS["AI_API_KEYS"]))
    keys[provider_id] = api_key.strip()
    save_settings(
        AI_PROVIDER=provider_id,
        AI_API_KEYS=keys,
        AI_MODEL=model.strip(),
    )


def get_api_key_source(provider_id: str | None = None) -> str:
    provider_id = provider_id or get_ai_provider()
    env_name = AI_PROVIDERS[provider_id]["env_key"]
    if os.environ.get(env_name, "").strip() or os.environ.get("AI_API_KEY", "").strip():
        return "环境变量"
    if get_ai_api_key(provider_id):
        return "已保存"
    return "未配置"


def get_api_key_hint() -> str:
    provider = get_provider_label()
    return (
        f"未找到 {provider} API Key。请在托盘菜单「配置 AI」填写，"
        f"或设置环境变量 {AI_PROVIDERS[get_ai_provider()]['env_key']}。"
    )


def get_settings_path() -> Path:
    return _SETTINGS_FILE


def get_example_settings_path() -> Path:
    return _EXAMPLE_FILE


# 兼容旧代码别名
def get_openai_api_key() -> str:
    return get_ai_api_key()


def set_openai_api_key(api_key: str) -> None:
    set_ai_api_key(api_key, "openai")


def clear_openai_api_key() -> None:
    clear_ai_api_key("openai")
