"""Reusable full-width scrollable page surface."""

from __future__ import annotations

import customtkinter as ctk

from safedesk.gui import design_system as ds


class ScrollablePage(ctk.CTkScrollableFrame):
    """Scrollable content area for pages that can exceed the window height."""

    def __init__(self, master, **kwargs):
        self.mousewheel_units = int(kwargs.pop("mousewheel_units", 4))
        self.middle_drag_pixels_per_unit = int(kwargs.pop("middle_drag_pixels_per_unit", 8))
        self._middle_drag_last_y: int | None = None
        super().__init__(
            master,
            fg_color=ds.CONTENT_BG,
            scrollbar_button_color=ds.BORDER_MUTED,
            scrollbar_button_hover_color=ds.SAFEDESK_RED,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        self.bind_widget_for_scroll(self)

    def bind_widget_for_scroll(self, widget) -> None:
        """Bind local page scroll helpers to a widget and its current children."""

        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>", "<ButtonPress-2>", "<B2-Motion>", "<ButtonRelease-2>"):
            try:
                widget.bind(sequence, self._handle_scroll_event, add="+")
            except Exception:
                pass
        try:
            for child in widget.winfo_children():
                self.bind_widget_for_scroll(child)
        except Exception:
            pass

    def bind_descendants_for_scroll(self) -> None:
        """Refresh scroll bindings after dynamic content is rendered."""

        self.bind_widget_for_scroll(self)

    def _scroll_canvas(self, units: int) -> None:
        canvas = getattr(self, "_parent_canvas", None)
        if canvas is None:
            return
        canvas.yview_scroll(units, "units")

    def _handle_scroll_event(self, event):
        if event.type.name == "MouseWheel":
            delta = getattr(event, "delta", 0)
            if delta:
                self._scroll_canvas(-int(delta / 120) * self.mousewheel_units)
                return "break"
        if getattr(event, "num", None) == 4:
            self._scroll_canvas(-self.mousewheel_units)
            return "break"
        if getattr(event, "num", None) == 5:
            self._scroll_canvas(self.mousewheel_units)
            return "break"
        if event.type.name == "ButtonPress":
            self._middle_drag_last_y = int(getattr(event, "y_root", 0))
            return "break"
        if event.type.name == "Motion" and self._middle_drag_last_y is not None:
            current_y = int(getattr(event, "y_root", self._middle_drag_last_y))
            delta = current_y - self._middle_drag_last_y
            units = int(delta / self.middle_drag_pixels_per_unit)
            if units:
                self._scroll_canvas(units)
                self._middle_drag_last_y = current_y
            return "break"
        if event.type.name == "ButtonRelease":
            self._middle_drag_last_y = None
            return "break"
        return None
