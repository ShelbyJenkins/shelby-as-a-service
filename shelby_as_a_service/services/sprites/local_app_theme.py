from __future__ import annotations
from typing import Iterable
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes


class AtYourServiceTheme(Base):
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
            body_background_fill_dark="black",
            background_fill_primary_dark="black",
            background_fill_secondary_dark="black",
            input_background_fill_dark='black', # Leave same as main background
            chatbot_code_background_color_dark='black',
            
            block_background_fill_dark='black',
            border_color_primary_dark="#653b12",
            block_border_color_dark='black',
            input_border_color_dark='black',
            input_border_color_focus_dark='black',
            input_border_color_hover_dark='black',
            block_title_border_color_dark='black',
            block_label_border_color_dark='black',
            panel_border_color_dark='black'
        )



