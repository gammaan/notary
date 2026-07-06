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

  function initProfileMenu() {
    const trigger = document.getElementById("staff-profile-trigger");
    const menu = document.getElementById("staff-profile-dropdown");
    if (!trigger || !menu) return;

    const close = () => {
      trigger.setAttribute("aria-expanded", "false");
      menu.hidden = true;
    };

    trigger.addEventListener("click", (event) => {
      event.stopPropagation();
      const open = menu.hidden;
      if (open) {
        trigger.setAttribute("aria-expanded", "true");
        menu.hidden = false;
      } else {
        close();
      }
    });

    document.addEventListener("click", (event) => {
      if (!menu.hidden && !menu.contains(event.target) && event.target !== trigger) {
        close();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") close();
    });
  }

  function initFileDrop() {
    document.querySelectorAll("[data-staff-file-drop]").forEach((zone) => {
      const input = zone.querySelector(".staff-file-drop__input");
      const nameEl = zone.querySelector(".staff-file-drop__name");
      if (!input || !nameEl) return;

      const showName = () => {
        const file = input.files && input.files[0];
        zone.classList.toggle("has-file", Boolean(file));

        const inlineText = zone.querySelector(
          ".staff-file-drop__surface--inline .staff-file-drop__text"
        );
        if (inlineText) {
          inlineText.textContent = file
            ? file.name
            : zone.dataset.defaultLabel || inlineText.textContent;
        }

        const zoneText = zone.querySelector(
          ".staff-file-drop__surface--zone .staff-file-drop__text"
        );
        if (zoneText) {
          zoneText.textContent = file
            ? file.name
            : zoneText.dataset.defaultText || zone.dataset.defaultLabel || zoneText.textContent;
        }

        if (nameEl && zone.classList.contains("staff-file-drop--zone")) {
          nameEl.textContent = "";
        } else if (nameEl) {
          nameEl.textContent = file ? file.name : "";
        }
      };

      const inlineText = zone.querySelector(
        ".staff-file-drop__surface--inline .staff-file-drop__text"
      );
      if (inlineText) {
        zone.dataset.defaultLabel = inlineText.textContent.trim();
      }
      const zoneText = zone.querySelector(
        ".staff-file-drop__surface--zone .staff-file-drop__text"
      );
      if (zoneText && zoneText.dataset.defaultText) {
        zone.dataset.defaultLabel = zoneText.dataset.defaultText;
      }

      input.addEventListener("change", showName);

      ["dragenter", "dragover"].forEach((type) => {
        zone.addEventListener(type, (event) => {
          event.preventDefault();
          zone.classList.add("is-dragover");
        });
      });

      ["dragleave", "drop"].forEach((type) => {
        zone.addEventListener(type, (event) => {
          event.preventDefault();
          zone.classList.remove("is-dragover");
        });
      });

      zone.addEventListener("drop", (event) => {
        const files = event.dataTransfer && event.dataTransfer.files;
        if (!files || !files.length) return;
        if (typeof DataTransfer !== "undefined") {
          const dt = new DataTransfer();
          dt.items.add(files[0]);
          input.files = dt.files;
        }
        showName();
      });

      if (zone.classList.contains("staff-file-drop--zone")) {
        nameEl.textContent = "";
      }
    });
  }

  function initActionMenus() {
    document.querySelectorAll("[data-staff-action-menu]").forEach((menuRoot) => {
      const trigger = menuRoot.querySelector(".staff-action-menu__trigger");
      const panel = menuRoot.querySelector(".staff-action-menu__panel");
      if (!trigger || !panel) return;

      const close = () => {
        trigger.setAttribute("aria-expanded", "false");
        panel.hidden = true;
      };

      trigger.addEventListener("click", (event) => {
        event.stopPropagation();
        const open = panel.hidden;
        document.querySelectorAll("[data-staff-action-menu] .staff-action-menu__panel").forEach((other) => {
          if (other !== panel) {
            other.hidden = true;
            const otherTrigger = other.closest("[data-staff-action-menu]")?.querySelector(".staff-action-menu__trigger");
            if (otherTrigger) otherTrigger.setAttribute("aria-expanded", "false");
          }
        });
        if (open) {
          trigger.setAttribute("aria-expanded", "true");
          panel.hidden = false;
        } else {
          close();
        }
      });

      document.addEventListener("click", (event) => {
        if (!panel.hidden && !menuRoot.contains(event.target)) close();
      });

      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") close();
      });
    });
  }

  initTheme();
  initProfileMenu();
  initActionMenus();
  initFileDrop();
})();
