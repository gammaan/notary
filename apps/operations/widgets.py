from django import forms
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _


class StaffFileUploadWidget(forms.FileInput):
    """Staff file input — inline row (default) or expanded drop zone."""

    def __init__(self, *args, drop_label=None, hint=None, layout="inline", **kwargs):
        self.drop_label = drop_label or _("Drag and Drop files")
        self.hint = hint or _("Click to browse or drop a file here")
        self.layout = layout
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        css_class = attrs.get("class", "")
        attrs["class"] = f"{css_class} staff-file-drop__input".strip()
        input_html = super().render(name, value, attrs, renderer)
        input_id = attrs.get("id", f"id_{name}")

        if self.layout == "zone":
            return format_html(
                '<div class="staff-file-drop staff-file-drop--zone" data-staff-file-drop>'
                "{}"
                '<label class="staff-file-drop__surface staff-file-drop__surface--zone" for="{}" tabindex="0">'
                '<span class="staff-file-drop__icon-wrap" aria-hidden="true">'
                '<i class="fa-solid fa-arrow-up-from-bracket staff-file-drop__icon"></i>'
                "</span>"
                '<span class="staff-file-drop__text" data-default-text="{}">{}</span>'
                '<span class="staff-file-drop__hint">{}</span>'
                "</label>"
                '<span class="staff-file-drop__name" aria-live="polite"></span>'
                "</div>",
                input_html,
                input_id,
                self.drop_label,
                self.drop_label,
                self.hint,
            )

        return format_html(
            '<div class="staff-file-drop staff-file-drop--inline" data-staff-file-drop>'
            "{}"
            '<label class="staff-file-drop__surface staff-file-drop__surface--inline" for="{}" tabindex="0">'
            '<span class="staff-file-drop__text">{}</span>'
            '<i class="fa-solid fa-cloud-arrow-up staff-file-drop__icon" aria-hidden="true"></i>'
            "</label>"
            '<span class="staff-file-drop__name" aria-live="polite"></span>'
            "</div>",
            input_html,
            input_id,
            self.drop_label,
        )
