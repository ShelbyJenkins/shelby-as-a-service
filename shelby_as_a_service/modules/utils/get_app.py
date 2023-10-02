from typing import Optional
from modules.utils.app_base import AppBase

_instance: Optional[AppBase] = None


def get_app(app_name: Optional[str] = None) -> AppBase:
    global _instance
    if _instance is None:
        if app_name is None:
            raise ValueError(
                "AppBase must be initialized with an app_name before it can be used without it."
            )
        _instance = AppBase(app_name=app_name)
    return _instance
