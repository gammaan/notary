(() => {
  "use strict";

  function initSelect2() {
    if (typeof jQuery === "undefined" || !jQuery.fn.select2) return;

    jQuery(function ($) {
      $(".staff-select2").each(function () {
        const $el = $(this);
        if ($el.data("select2")) return;
        $el.select2({
          width: "100%",
          placeholder: $el.data("placeholder") || "Select…",
          allowClear: Boolean($el.data("allow-clear")) || !$el.prop("required"),
        });
      });
    });
  }

  document.addEventListener("DOMContentLoaded", initSelect2);
})();
