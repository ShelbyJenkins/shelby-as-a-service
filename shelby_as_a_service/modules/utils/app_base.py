import concurrent.futures
import os
from decimal import Decimal
from typing import Any, Dict, List, Optional

import modules.utils.app_manager as AppManager
import modules.utils.config_manager as ConfigManager
from dotenv import load_dotenv
from modules.utils.log_service import Logger


class AppBase:
    _instance: Optional["AppBase"] = None
    app_manager: Any = AppManager
    config_manager: Any = ConfigManager
    prompt_template_path: str = "shelby_as_a_service/modules/prompt_templates"

    config: Dict[str, str] = {}
    secrets: Dict[str, str] = {}
    required_secrets: List[str] = []
    total_cost: Decimal = Decimal("0")
    last_request_cost: Decimal = Decimal("0")

    def __init__(self, app_name):
        # self.app_name = AppManager.initialize_app_config(app_name)
        self.app_name = app_name

        self.log = Logger(
            self.app_name,
            self.app_name,
            f"{self.app_name}.md",
            level="INFO",
        )

        load_dotenv(os.path.join(f"apps/{self.app_name}/", ".env"))
        self.config = AppManager.load_app_file(self.app_name)
        self.local_index_dir = f"apps/{self.app_name}/index"

    def setup_app(self):
        from modules.index.data_model import IndexModel

        # Index needs to init first
        self.index = IndexModel()

        from sprites.web.web_sprite import WebSprite

        self.web_sprite = WebSprite()

        # Check secrets
        for secret in self.required_secrets:
            if self.secrets.get(secret, None) is None:
                print(f"Secret: {secret} is None!")

        return self

    def run_sprites(self):
        self.web_sprite.run_sprite()
        # with concurrent.futures.ThreadPoolExecutor() as executor:
        # for sprite_name in self.enabled_sprites:
        #     sprite = getattr(self, sprite_name)
        #     executor.submit(sprite.run_sprite())
