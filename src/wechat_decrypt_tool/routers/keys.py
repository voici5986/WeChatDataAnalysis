from typing import Optional

from fastapi import APIRouter

from ..key_store import get_account_keys_from_store
from ..media_helpers import _load_media_keys, _resolve_account_dir
from ..path_fix import PathFixRoute

router = APIRouter(route_class=PathFixRoute)


@router.get("/api/keys", summary="获取账号已保存的密钥")
async def get_saved_keys(account: Optional[str] = None):
    """获取账号的数据库密钥与图片密钥（用于前端自动回填）"""
    account_name: Optional[str] = None
    account_dir = None

    try:
        account_dir = _resolve_account_dir(account)
        account_name = account_dir.name
    except Exception:
        # 账号可能尚未解密；仍允许从全局 store 读取（如果传入了 account）
        account_name = str(account or "").strip() or None

    keys: dict = {}
    if account_name:
        keys = get_account_keys_from_store(account_name)

    # 兼容：如果 store 里没有图片密钥，尝试从账号目录的 _media_keys.json 读取
    if account_dir and isinstance(keys, dict):
        try:
            media = _load_media_keys(account_dir)
            if keys.get("image_xor_key") in (None, "") and media.get("xor") is not None:
                keys["image_xor_key"] = f"0x{int(media['xor']):02X}"
            if keys.get("image_aes_key") in (None, "") and str(media.get("aes") or "").strip():
                keys["image_aes_key"] = str(media.get("aes") or "").strip()
        except Exception:
            pass

    # 仅返回需要的字段
    result = {
        "db_key": str(keys.get("db_key") or "").strip(),
        "image_xor_key": str(keys.get("image_xor_key") or "").strip(),
        "image_aes_key": str(keys.get("image_aes_key") or "").strip(),
        "updated_at": str(keys.get("updated_at") or "").strip(),
    }

    return {
        "status": "success",
        "account": account_name,
        "keys": result,
    }

