import hashlib
import hmac
import time
from typing import Any, Mapping

from ..core.config import settings


def verify_telegram_auth(data: Mapping[str, Any], max_age_seconds: int = 86400) -> bool:
    """
    Проверка подписи данных от Telegram Login Widget.
    data — словарь со всеми полями, включая 'hash'.
    """

    if "hash" not in data:
        return False

    received_hash = data["hash"]
    auth_data = {k: v for k, v in data.items() if k != "hash"}

    # 1. Собираем data-check-string
    data_check_arr = [f"{k}={auth_data[k]}" for k in sorted(auth_data.keys())]
    data_check_string = "\n".join(data_check_arr)

    # 2. Ключ HMAC
    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode("utf-8")).digest()

    # 3. HMAC-SHA256
    calculated_hash = hmac.new(
        secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        return False

    # 4. Проверка срока давности (опционально, но полезно)
    auth_ts_raw = auth_data.get("auth_date")
    try:
        auth_ts = int(auth_ts_raw)
    except (TypeError, ValueError):
        return False

    if time.time() - auth_ts > max_age_seconds:
        return False

    return True
