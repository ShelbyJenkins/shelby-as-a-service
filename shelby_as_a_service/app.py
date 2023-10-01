import argparse
import concurrent.futures
import os
from typing import Dict, Optional, List, Any
from dotenv import load_dotenv
import modules.utils.app_manager as AppManager
import modules.utils.config_manager as ConfigManager
from modules.utils.log_service import Logger
from pydantic import BaseModel
from modules.index.data_model import IndexModel
from sprites.web.web_sprite import WebSprite


class AppBase(BaseModel):
    app_manager: Any = AppManager
    config_manager: Any = ConfigManager
    log: Any = Logger
    prompt_template_path: str = "shelby_as_a_service/modules/prompt_templates"
    local_index_dir: Optional[str] = None

    # Set during run
    app_name: str = "base"
    config: Dict[str, str] = {}
    secrets: Dict[str, str] = {}
    required_secrets: List[str] = []
    total_cost: float = 0.0

    index: Any = IndexModel
    web_sprite: Any = WebSprite

    def setup_app(self, app_name):
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

        # Index needs to init first
        self.index = IndexModel(self)

        self.web_sprite = WebSprite(self)

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


def main():
    """
    By default, this script runs the web app locally.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "app_name",
        type=str,
        nargs="?",
        help=f"Runs with a configuration from apps/<app_name>/app_config.json.",
    )
    args = parser.parse_args()

    if args.app_name:
        app_name = args.app_name
    else:
        app_name = "base"

    print(f"app.py is being run as: {app_name}")

    app = AppBase()
    app.setup_app(app_name=app_name)
    app.run_sprites()


if __name__ == "__main__":
    main()
