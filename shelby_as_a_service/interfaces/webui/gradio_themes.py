from __future__ import annotations

import typing
from typing import Iterable

from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes


class AtYourServiceTheme(Base):
    css = """

    .gradio-container { 
        height: 100vh;
        max-width: 100vw !important;
        box-sizing: border-box;
        margin: 0 !important;
        padding: 0 !important;
    }

    #main_row {
        height: 100vh;
        width: 100vw;
        display: flex;
        box-sizing: border-box;
        flex-direction: row;
    }
    #SETTINGS_UI_COL {
        height: 100vh;
        display: flex;
        box-sizing: border-box;
        flex-direction: column;
        
        padding: 1% !important;
        border-right-width: 4px !important; 
    }
    
    #primary_ui_col {
        height: 100vh;
        display: flex;
        flex-direction: col;
        box-sizing: border-box;
    }
    .primary_ui_row {
        height: 100%;
        display: flex;
        box-sizing: border-box;
        flex-direction: column;
    }
    .primary_ui_col > div:first-child {
        display: flex;
        flex-direction: column;
        flex-grow: 1 !important;
    }
    .chat_tab_button {
        margin: 3% !important;
        width: auto !important;
    }
    
    footer[class*='svelte-'] {
        display: none !important;
    }

    """

    def __init__(
        self,
        *,
        primary_hue: colors.Color | str = colors.neutral,
        secondary_hue: colors.Color | str = colors.neutral,
        neutral_hue: colors.Color | str = colors.green,
        spacing_size: sizes.Size | str = sizes.spacing_sm,
        radius_size: sizes.Size | str = sizes.radius_sm,
        text_size: sizes.Size | str = sizes.text_sm,
        font: fonts.Font
        | str
        | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("REM"),
            fonts.GoogleFont("Belanosima"),
            "ui-sans-serif",
            "sans-serif",
        ),
        font_mono: fonts.Font
        | str
        | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("Inter"),
            fonts.GoogleFont("REM"),
            "ui-monospace",
            "monospace",
        ),
    ):
        super().__init__(
            primary_hue=primary_hue,
            secondary_hue=secondary_hue,
            neutral_hue=neutral_hue,
            spacing_size=spacing_size,
            radius_size=radius_size,
            text_size=text_size,
            font=font,
            font_mono=font_mono,
        )
        super().set(
            # sizes
            # layout_gap="1px",
            block_padding="5px",
            block_border_width_dark="0px",
            block_label_border_width_dark="0px",
            block_title_border_width_dark="0px",
            panel_border_width_dark="0px",
            checkbox_border_width_dark="0px",
            checkbox_label_border_width_dark="0px",
            input_border_width_dark="0px",
            button_border_width_dark="0px",
            # body color
            body_background_fill_dark="black",
            background_fill_primary_dark="black",
            background_fill_secondary_dark="black",
            input_background_fill_dark="black",  # Leave same as main background
            chatbot_code_background_color_dark="black",
            block_background_fill_dark="black",
            border_color_primary_dark="#653b12",
            block_border_color_dark="black",
            input_border_color_dark="green",
            input_border_color_focus_dark="black",
            input_border_color_hover_dark=None,
            block_title_border_color_dark="black",
            block_label_border_color_dark="black",
            panel_border_color_dark="black",
            # radio and checkbox and button
            button_primary_background_fill_dark="green",
            button_primary_background_fill_hover_dark="#653b12",
            checkbox_background_color_focus_dark="black",
            checkbox_border_color_dark="#653b12",
            checkbox_border_color_focus_dark="#653b12",
            radio_circle="black",
            checkbox_label_background_fill_dark="black",
            checkbox_background_color_dark="#2a2a2a",
            # selected
            checkbox_border_color_selected_dark="black",
            checkbox_background_color_selected_dark="green",
            checkbox_label_background_fill_selected_dark=None,
            # hover
            checkbox_background_color_hover_dark="#653b12",
            checkbox_border_color_hover_dark=None,
            checkbox_label_background_fill_hover_dark="black",
            # idk
            checkbox_label_border_color_dark="#2a2a2a",
            checkbox_label_gap=None,
            checkbox_label_padding=None,
            checkbox_label_text_size=None,
            checkbox_label_text_weight=None,
            checkbox_label_text_color=None,
            checkbox_label_text_color_dark=None,
            checkbox_label_text_color_selected=None,
            checkbox_label_text_color_selected_dark=None,
        )
