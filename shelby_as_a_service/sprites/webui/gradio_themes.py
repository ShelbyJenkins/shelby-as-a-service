from __future__ import annotations

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
    #settings_panel_col {
        height: 100vh;
        display: flex;
        box-sizing: border-box;
        flex-direction: column;
        flex-grow: 1.5 !important;
        padding: 1% !important;
        border-right-width: 4px !important; 
    }
    
    #chat_ui_panel_col {
        height: 100vh;
        display: flex;
        flex-direction: row;
        flex-grow: 9.5 !important;
        box-sizing: border-box;
    }

    #chat_ui_row {
        height: height: 100vh;
        display: flex;
        box-sizing: border-box;
        flex-direction: column;
        flex-grow: 8 !important;        
    }
    #chat_ui_col {
        height: height: 100vh;
        display: flex;
        box-sizing: border-box;
        flex-direction: column;
        flex-grow: 8 !important;        
    }
    .chat_ui_col > div:first-child {
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    
    #chat_tab_out_text {
        flex-grow: 7;
    }
    #chat_tab_out_text label,
    #chat_tab_out_text textarea {
        width: 100% !important;
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
    }
    #chat_tab_out_text textarea {
        flex-grow: 1 !important; 
        resize: none !important; 
        box-sizing: border-box !important; 
    }
    
    #chat_tab_in_text {
        flex-grow: 3;
    }
    #chat_tab_in_text label,
    #chat_tab_in_text textarea {
        width: 100% !important;
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
    }
    #chat_tab_in_text textarea {
        flex-grow: 1 !important; 
        resize: none !important; 
        box-sizing: border-box !important; 
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
            layout_gap="0",
            block_border_width="0px",
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
            # radio and checkbox
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
