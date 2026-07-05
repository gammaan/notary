(() => {
  "use strict";

  function initTheme() {
    const root = document.documentElement;
    const toggles = document.querySelectorAll(".theme-toggle");
    const stored = localStorage.getItem("theme");
    const theme = stored === "light" || stored === "dark" ? stored : root.getAttribute("data-theme") || "dark";

    root.setAttribute("data-theme", theme);

    const labelLight = root.dataset.labelLight || "Light mode";
    const labelDark = root.dataset.labelDark || "Dark mode";

    const updateThemeLabels = (themeName) => {
      const label = themeName === "light" ? labelDark : labelLight;
      toggles.forEach((btn) => btn.setAttribute("aria-label", label));
    };

    toggles.forEach((toggle) => {
      toggle.addEventListener("click", () => {
        const current = root.getAttribute("data-theme") === "light" ? "light" : "dark";
        const next = current === "light" ? "dark" : "light";
        root.setAttribute("data-theme", next);
        localStorage.setItem("theme", next);
        updateThemeLabels(next);
      });
    });

    updateThemeLabels(theme);
  }

  initTheme();
})();
