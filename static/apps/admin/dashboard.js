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
      danger: readCssVar("--danger", "#f87171"),
      muted: readCssVar("--text-faint", "#8a8278"),
      grid: isLight ? "rgba(0,0,0,0.08)" : "rgba(255,255,255,0.08)",
      text: readCssVar("--text-secondary", "#c8c0b4"),
      palette: ["#c9a962", "#86efac", "#93c5fd", "#fcd34d", "#f9a8d4", "#a5b4fc", "#fdba74"],
      income: readCssVar("--accent-light", "#c9a962"),
      expense: readCssVar("--danger", "#f87171"),
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

  function doughnutOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { boxWidth: 10, padding: 14, font: { size: 11 } },
        },
      },
    };
  }

  function initDoughnut(canvasId, dataId, palette) {
    const data = parseChartData(dataId);
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data || !data.labels?.length) return;

    new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: data.labels,
        datasets: [{
          data: data.values,
          backgroundColor: palette,
          borderWidth: 0,
          hoverOffset: 6,
        }],
      },
      options: doughnutOptions(),
    });
  }

  function initDashboardCharts() {
    if (typeof Chart === "undefined") return;

    const colors = chartColors();
    Chart.defaults.color = colors.text;
    Chart.defaults.borderColor = colors.grid;
    Chart.defaults.font.family = "'M PLUS Rounded 1c', system-ui, sans-serif";

    initDoughnut("chart-matter-status", "chart-matter-status-data", colors.palette);

    const incomeExpenseData = parseChartData("chart-income-expense-data");
    const incomeExpenseCanvas = document.getElementById("chart-income-expense");
    if (incomeExpenseCanvas && incomeExpenseData?.labels?.length) {
      new Chart(incomeExpenseCanvas, {
        type: "bar",
        data: {
          labels: incomeExpenseData.labels,
          datasets: [{
            data: incomeExpenseData.values,
            backgroundColor: [colors.income, colors.expense + "cc"],
            borderRadius: 8,
            maxBarThickness: 72,
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

    initDoughnut(
      "chart-income-status",
      "chart-income-status-data",
      [colors.income, "#86efac", "#93c5fd", "#fcd34d", "#a5b4fc"]
    );
    initDoughnut(
      "chart-expense-status",
      "chart-expense-status-data",
      [colors.expense, "#fdba74", "#f9a8d4", "#c4b5fd", "#94a3b8"]
    );

    const revenueData = parseChartData("chart-revenue-data");
    const revenueCanvas = document.getElementById("chart-revenue");
    if (revenueCanvas && revenueData) {
      new Chart(revenueCanvas, {
        type: "bar",
        data: {
          labels: revenueData.labels,
          datasets: [
            {
              label: "Paid income",
              data: revenueData.values,
              backgroundColor: colors.income,
              borderRadius: 6,
              maxBarThickness: 28,
            },
            {
              label: "Paid expenses",
              data: revenueData.expenses || [],
              backgroundColor: colors.expense + "cc",
              borderRadius: 6,
              maxBarThickness: 28,
            },
          ],
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
          plugins: {
            legend: {
              position: "bottom",
              labels: { boxWidth: 10, padding: 12, font: { size: 11 } },
            },
          },
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
