from decimal import Decimal
from typing import Any, Dict, List, Optional

import gradio as gr
import sprites.web.gradio_helpers as GradioHelper


class GradioEvents:
    def __init__(self, web_sprite):
        self.web_sprite = web_sprite
        self.features = self.web_sprite.ui["features"]
        self.available_agents_ui_names: List[str] = []
        self.available_agents_names: List[str] = []
        for agent in web_sprite.AVAILABLE_AGENTS:
            self.available_agents_ui_names.append(GradioHelper.get_class_ui_name(agent))
            self.available_agents_names.append(GradioHelper.get_class_name(agent))

    def create_event_handlers(self):
        def creator(feature):
            self.handlers(
                feature["ui"]["components"], feature["ui"]["components_state"]
            )

        for _, feature in self.features.items():
            creator(feature)

        self.create_nav_events()

    def handlers(
        self,
        components,
        components_state,
    ):
        gr.on(
            triggers=[
                # components["chat_tab_generate_button"].click,
                components["chat_tab_in_text"].submit,
            ],
            fn=lambda *comp_vals: comp_vals,
            inputs=list(components.values()),
            outputs=list(components_state.values()),
        ).then(
            fn=lambda: "Proooooomptering",
            outputs=components["chat_tab_status_text"],
        ).then(
            fn=self.web_sprite.run_chat,
            inputs=list(components_state.values()),
            outputs=[
                components["chat_tab_out_text"],
                components["chat_tab_in_token_count"],
                components["chat_tab_out_token_count"],
                components["chat_tab_total_token_count"],
            ],
        ).success(
            fn=lambda: "",
            outputs=components["chat_tab_in_text"],
        ).success(
            fn=self.get_spend,
            outputs=[
                components["chat_tab_response_cost"],
                components["chat_tab_total_cost"],
            ],
        )

    def get_spend(self):
        req = f"Request price: ${round(self.web_sprite.app.last_request_cost, 4)}"
        self.web_sprite.app.last_request_cost = Decimal("0")
        tot = f"Total spend: ${round(self.web_sprite.app.total_cost, 4)}"
        return [req, tot]

    def create_nav_events(self):
        all_nav_tabs = []
        all_chat_ui_rows = []
        for _, feature in self.web_sprite.ui["features"].items():
            all_nav_tabs.append(feature["settings_tab_component"])
            all_chat_ui_rows.append(feature["chat_ui_row"])

        for feature_nav_tab in all_nav_tabs:
            feature_nav_tab.select(
                fn=self.change_feature,
                inputs=None,
                outputs=all_chat_ui_rows,
            )

    def change_feature(self, evt: gr.SelectData):
        output = []
        for ui_name in self.available_agents_ui_names:
            if evt.value == ui_name:
                output.append(gr.Row(visible=True))
                self.web_sprite.config.current_feature_ui_name = ui_name
            else:
                output.append(gr.Row(visible=False))
        return output
