(() => {
  "use strict";

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

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
      document.querySelectorAll(".theme-toggle__label").forEach((el) => {
        el.textContent = themeName === "light" ? labelDark : labelLight;
      });
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

  function initPageEnter() {
    const header = document.querySelector(".site-header");
    if (!header) return;
    header.classList.add("is-entered");
  }

  function initStagger() {
    document.querySelectorAll("[data-stagger]").forEach((group) => {
      const items = group.querySelectorAll(
        ":scope > .bento-card, :scope > .workflow-node, :scope > .security-card, :scope > .experience-item, :scope > .cms-card"
      );
      items.forEach((item, index) => {
        item.style.setProperty("--delay", index);
      });
    });
  }

  function initHeroSplit() {
    document.querySelectorAll("[data-split]").forEach((line, lineIndex) => {
      if (line.querySelector("span")) return;

      const text = line.textContent.trim();
      line.textContent = "";
      const span = document.createElement("span");
      span.textContent = text;
      line.appendChild(span);

      if (prefersReducedMotion) {
        line.classList.add("is-revealed");
        return;
      }

      setTimeout(() => line.classList.add("is-revealed"), 200 + lineIndex * 120);
    });
  }

  function initReveal() {
    const items = document.querySelectorAll("[data-reveal], [data-stagger]");

    if (prefersReducedMotion) {
      items.forEach((el) => el.classList.add("is-visible"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const delay = entry.target.dataset.delay;
          if (delay) entry.target.style.setProperty("--delay", delay);
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -4% 0px" }
    );

    items.forEach((item) => observer.observe(item));
  }

  function initHeader() {
    const header = document.querySelector(".site-header");
    if (!header) return;

    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        header.classList.toggle("is-scrolled", window.scrollY > 24);
        ticking = false;
      });
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  function initMobileNav() {
    const toggle = document.querySelector(".menu-toggle");
    const nav = document.querySelector(".mobile-nav");
    if (!toggle || !nav) return;

    nav.hidden = false;

    const close = () => {
      toggle.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
      nav.classList.remove("is-open");
      document.body.classList.remove("is-menu-open");
    };

    const open = () => {
      toggle.classList.add("is-open");
      toggle.setAttribute("aria-expanded", "true");
      nav.classList.add("is-open");
      document.body.classList.add("is-menu-open");
    };

    toggle.addEventListener("click", () => {
      nav.classList.contains("is-open") ? close() : open();
    });

    nav.querySelectorAll("a").forEach((link) => link.addEventListener("click", close));
  }

  function initCursorGlow() {
    const glow = document.querySelector(".cursor-glow");
    if (!glow || prefersReducedMotion || !finePointer) return;

    window.addEventListener(
      "mousemove",
      (e) => {
        glow.style.transform = `translate3d(${e.clientX}px, ${e.clientY}px, 0)`;
        glow.classList.add("is-active");
      },
      { passive: true }
    );

    document.addEventListener("mouseleave", () => {
      glow.classList.remove("is-active");
    });
  }

  function initMagnetic() {
    if (prefersReducedMotion || !finePointer) return;

    document.querySelectorAll(".magnetic").forEach((btn) => {
      btn.addEventListener("mousemove", (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        btn.style.transform = `translate(${x * 0.12}px, ${y * 0.12}px)`;
      });

      btn.addEventListener("mouseleave", () => {
        btn.style.transform = "";
      });
    });
  }

  function initWorkflowHighlight() {
    const nodes = document.querySelectorAll(".workflow-node");
    if (!nodes.length) return;

    if (prefersReducedMotion) {
      nodes.forEach((n) => n.classList.add("is-active"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          entry.target.classList.toggle("is-active", entry.isIntersecting);
        });
      },
      { threshold: 0.5 }
    );

    nodes.forEach((node) => observer.observe(node));
  }

  function initSmoothAnchors() {
    document.querySelectorAll('a[href^="#"]').forEach((link) => {
      link.addEventListener("click", (e) => {
        const id = link.getAttribute("href");
        if (!id || id === "#") return;
        const target = document.querySelector(id);
        if (!target) return;
        e.preventDefault();
        target.scrollIntoView({ behavior: prefersReducedMotion ? "auto" : "smooth", block: "start" });
      });
    });
  }

  initTheme();
  initStagger();
  initPageEnter();
  initHeroSplit();
  initReveal();
  initHeader();
  initMobileNav();
  initCursorGlow();
  initMagnetic();
  initWorkflowHighlight();
  initSmoothAnchors();
})();
