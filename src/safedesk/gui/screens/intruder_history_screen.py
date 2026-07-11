"""Owner-only local intruder evidence history screen."""

import customtkinter as ctk

from safedesk.app.application import RuntimeContext
from safedesk.gui import design_system as ds
from safedesk.gui.components.info_banner import InfoBanner
from safedesk.gui.components.page_header import PageHeader
from safedesk.gui.components.scrollable_page import ScrollablePage
from safedesk.intruder_history import IntruderEvidenceItem, IntruderHistoryReader
from safedesk.logging.event_logger import build_logger_from_config


class IntruderHistoryScreen(ctk.CTkFrame):
    """Read-only owner review surface for local intruder evidence."""

    def __init__(self, master, context: RuntimeContext):
        super().__init__(master, fg_color=ds.CONTENT_BG)
        self.context = context
        self.config = context.load_result.config
        self.reader = IntruderHistoryReader(self.config)
        self.summary = self.reader.build_summary()
        self.event_logger = build_logger_from_config(self.config)
        self.thumbnail_images = []
        self._log_history_opened()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ScrollablePage(self, mousewheel_units=6)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)

        PageHeader(
            page,
            "Intruder History",
            "Owner-only review of locally captured unknown/unverified evidence.",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 10))

        InfoBanner(
            page,
            "Read-only local evidence review. This screen does not start camera, run recognition, send messages, or change evidence files.",
            kind="info",
            compact=True,
        ).grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 10))

        summary = ctk.CTkFrame(page, fg_color="transparent")
        summary.grid(row=2, column=0, sticky="ew")
        for column in range(3):
            summary.grid_columnconfigure(column, weight=1, uniform="intruder_summary")
        self._summary_tile(summary, "Total Captures", str(self.summary.total_count), 0)
        self._summary_tile(summary, "Images Available", str(self.summary.image_available_count), 1)
        self._summary_tile(summary, "Most Recent", self.summary.most_recent_capture, 2)

        list_frame = ctk.CTkFrame(page, fg_color="transparent")
        list_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        list_frame.grid_columnconfigure(0, weight=1)

        if not self.summary.items:
            InfoBanner(
                list_frame,
                "No intruder evidence captured yet.",
                kind="neutral",
                compact=True,
            ).grid(row=0, column=0, sticky="ew", padx=4, pady=6)
        else:
            for index, item in enumerate(self.summary.items):
                self._evidence_card(list_frame, item, index)

        page.bind_descendants_for_scroll()

    def _summary_tile(self, master, label: str, value: str, column: int) -> None:
        tile = ctk.CTkFrame(master, **ds.card_kwargs())
        tile.grid(row=0, column=column, sticky="nsew", padx=4, pady=6)
        tile.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            tile,
            text=label,
            text_color=ds.TEXT_MUTED,
            font=ctk.CTkFont(size=ds.FONT_SMALL),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(ds.SPACE_LG, 2))
        ctk.CTkLabel(
            tile,
            text=value,
            text_color=ds.TEXT_PRIMARY,
            font=ctk.CTkFont(size=ds.FONT_H3, weight="bold"),
            anchor="w",
            wraplength=280,
        ).grid(row=1, column=0, sticky="ew", padx=ds.SPACE_LG, pady=(0, ds.SPACE_LG))

    def _evidence_card(self, master, item: IntruderEvidenceItem, row: int) -> None:
        card = ctk.CTkFrame(master, **ds.card_kwargs())
        card.grid(row=row, column=0, sticky="ew", padx=4, pady=6)
        card.grid_columnconfigure(1, weight=1)

        preview = ctk.CTkFrame(card, width=150, height=100, **ds.panel_kwargs())
        preview.grid(row=0, column=0, sticky="nsw", padx=ds.SPACE_LG, pady=ds.SPACE_LG)
        preview.grid_propagate(False)
        preview.grid_columnconfigure(0, weight=1)
        preview.grid_rowconfigure(0, weight=1)

        thumbnail = self._load_thumbnail(item)
        if thumbnail is None:
            ctk.CTkLabel(
                preview,
                text="Preview unavailable" if item.image_available else "Image missing",
                text_color=ds.TEXT_SECONDARY,
                wraplength=120,
            ).grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        else:
            ctk.CTkLabel(preview, text="", image=thumbnail).grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        details = ctk.CTkFrame(card, fg_color="transparent")
        details.grid(row=0, column=1, sticky="nsew", padx=(0, ds.SPACE_LG), pady=ds.SPACE_LG)
        details.grid_columnconfigure(0, weight=1)

        rows = [
            ("Capture ID", item.capture_id),
            ("Timestamp", item.captured_at),
            ("Status", item.status),
            ("Message", item.safe_message),
            ("Image", "available" if item.image_available else "missing"),
        ]
        if item.event_reference:
            rows.append(("Event reference", item.event_reference))

        for index, (label, value) in enumerate(rows):
            ctk.CTkLabel(
                details,
                text=f"{label}: {value}",
                text_color=ds.TEXT_SECONDARY if index else ds.TEXT_PRIMARY,
                font=ctk.CTkFont(size=ds.FONT_BODY, weight="bold" if index == 0 else "normal"),
                anchor="w",
                justify="left",
                wraplength=760,
            ).grid(row=index, column=0, sticky="ew", pady=2)

    def _load_thumbnail(self, item: IntruderEvidenceItem):
        if not item.preview_allowed or item.preview_path is None:
            return None
        try:
            from PIL import Image

            with Image.open(item.preview_path) as image:
                preview_image = image.convert("RGB").copy()
            preview_image.thumbnail((138, 88))
            thumbnail = ctk.CTkImage(light_image=preview_image, dark_image=preview_image, size=preview_image.size)
            self.thumbnail_images.append(thumbnail)
            return thumbnail
        except Exception:
            return None

    def _log_history_opened(self) -> None:
        try:
            self.event_logger.log_app_event(
                action="intruder_history_opened",
                status="info",
                message="Intruder History opened.",
                metadata={
                    "item_count": self.summary.total_count,
                    "image_available_count": self.summary.image_available_count,
                    "result_status": "loaded",
                },
            )
        except Exception:
            pass
