"""SafeDesk brand design tokens for the GUI."""

SAFEDESK_BLACK = "#000000"
SAFEDESK_DEEP_RED = "#850F0D"
SAFEDESK_RED = "#B61D18"
SAFEDESK_ALERT = "#F85E51"
SAFEDESK_NEUTRAL = "#C3B9AB"

APP_BG = "#0D0D0D"
SIDEBAR_BG = "#111111"
CONTENT_BG = "#171717"
CARD_BG = "#202020"
CARD_BG_ALT = "#262626"
BORDER_MUTED = "#3A302E"
TEXT_PRIMARY = "#F4EEE8"
TEXT_SECONDARY = SAFEDESK_NEUTRAL
TEXT_MUTED = "#8F8680"

SUCCESS = "#5E9F74"
WARNING = SAFEDESK_ALERT
DANGER = SAFEDESK_DEEP_RED

RADIUS_SM = 6
RADIUS_MD = 8
RADIUS_LG = 10

SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 24

FONT_H1 = 26
FONT_H2 = 20
FONT_H3 = 16
FONT_BODY = 13
FONT_SMALL = 12


def card_kwargs() -> dict[str, object]:
    return {
        "fg_color": CARD_BG,
        "corner_radius": RADIUS_MD,
        "border_width": 1,
        "border_color": BORDER_MUTED,
    }


def panel_kwargs() -> dict[str, object]:
    return {
        "fg_color": CARD_BG_ALT,
        "corner_radius": RADIUS_MD,
        "border_width": 1,
        "border_color": BORDER_MUTED,
    }


def transparent_kwargs() -> dict[str, str]:
    return {"fg_color": "transparent"}


def primary_button_kwargs() -> dict[str, object]:
    return {
        "fg_color": SAFEDESK_RED,
        "hover_color": SAFEDESK_DEEP_RED,
        "text_color": TEXT_PRIMARY,
        "corner_radius": RADIUS_SM,
        "border_width": 0,
    }


def secondary_button_kwargs() -> dict[str, object]:
    return {
        "fg_color": CARD_BG_ALT,
        "hover_color": BORDER_MUTED,
        "text_color": TEXT_PRIMARY,
        "corner_radius": RADIUS_SM,
        "border_width": 1,
        "border_color": BORDER_MUTED,
    }


def banner_colors(kind: str = "neutral") -> dict[str, str]:
    styles = {
        "neutral": {
            "fg_color": CARD_BG,
            "border_color": BORDER_MUTED,
            "accent": TEXT_MUTED,
            "text": TEXT_SECONDARY,
        },
        "info": {
            "fg_color": "#211C1B",
            "border_color": BORDER_MUTED,
            "accent": SAFEDESK_NEUTRAL,
            "text": TEXT_PRIMARY,
        },
        "warning": {
            "fg_color": "#2A1B18",
            "border_color": SAFEDESK_ALERT,
            "accent": SAFEDESK_ALERT,
            "text": TEXT_PRIMARY,
        },
        "success": {
            "fg_color": "#18231D",
            "border_color": SUCCESS,
            "accent": SUCCESS,
            "text": TEXT_PRIMARY,
        },
        "danger": {
            "fg_color": "#241211",
            "border_color": SAFEDESK_DEEP_RED,
            "accent": SAFEDESK_RED,
            "text": TEXT_PRIMARY,
        },
    }
    return styles.get(kind, styles["neutral"])
