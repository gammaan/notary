(() => {
  "use strict";

  function readCssVar(name, fallback) {
    const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return value || fallback;
  }

  function chartColors() {
    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    return {
      accent: readCssVar("--accent-light", "#c9a962"),
      accentDeep: readCssVar("--accent", "#a68b4a"),
      muted: readCssVar("--text-faint", "#8a8278"),
      grid: isLight ? "rgba(0,0,0,0.08)" : "rgba(255,255,255,0.08)",
      text: readCssVar("--text-secondary", "#c8c0b4"),
      palette: ["#c9a962", "#86efac", "#93c5fd", "#fcd34d", "#f9a8d4", "#a5b4fc", "#fdba74"],
    };
  }

  function parseChartData(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch {
      return null;
    }
  }

  function initDashboardCharts() {
    if (typeof Chart === "undefined") return;

    const colors = chartColors();
    Chart.defaults.color = colors.text;
    Chart.defaults.borderColor = colors.grid;
    Chart.defaults.font.family = "'M PLUS Rounded 1c', system-ui, sans-serif";

    const statusData = parseChartData("chart-matter-status-data");
    const statusCanvas = document.getElementById("chart-matter-status");
    if (statusCanvas && statusData) {
      new Chart(statusCanvas, {
        type: "doughnut",
        data: {
          labels: statusData.labels,
          datasets: [{
            data: statusData.values,
            backgroundColor: colors.palette,
            borderWidth: 0,
            hoverOffset: 6,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "68%",
          plugins: {
            legend: {
              position: "bottom",
              labels: { boxWidth: 10, padding: 14, font: { size: 11 } },
            },
          },
        },
      });
    }

    const revenueData = parseChartData("chart-revenue-data");
    const revenueCanvas = document.getElementById("chart-revenue");
    if (revenueCanvas && revenueData) {
      new Chart(revenueCanvas, {
        type: "bar",
        data: {
          labels: revenueData.labels,
          datasets: [{
            label: "Paid income",
            data: revenueData.values,
            backgroundColor: colors.accent,
            borderRadius: 6,
            maxBarThickness: 36,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { grid: { display: false } },
            y: {
              beginAtZero: true,
              ticks: { callback: (v) => "$" + v },
            },
          },
          plugins: { legend: { display: false } },
        },
      });
    }

    const servicesData = parseChartData("chart-services-data");
    const servicesCanvas = document.getElementById("chart-services");
    if (servicesCanvas && servicesData) {
      new Chart(servicesCanvas, {
        type: "bar",
        data: {
          labels: servicesData.labels,
          datasets: [{
            label: "Matters",
            data: servicesData.values,
            backgroundColor: colors.palette.map((c) => c + "cc"),
            borderRadius: 6,
            maxBarThickness: 22,
          }],
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { beginAtZero: true, grid: { color: colors.grid } },
            y: { grid: { display: false } },
          },
          plugins: { legend: { display: false } },
        },
      });
    }
  }

  document.addEventListener("DOMContentLoaded", initDashboardCharts);
})();
