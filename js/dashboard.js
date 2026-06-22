/**
 * Pulse — Dashboard JavaScript
 * Loads user-scoped stats from /api/stats and renders Bento Grid panels
 */

document.addEventListener("DOMContentLoaded", function () {

  // Resolve design system theme variables
  const isLight = document.documentElement.classList.contains("theme-light");
  
  // Custom semantic chart colors
  const colors = {
    positive: "#10b981", // Emerald
    negative: "#ef4444", // Red
    neutral: "#8b8fa3",  // Slate
    warning: "#f59e0b",  // Amber
    accent: "#6366f1",   // Indigo
    accent2: "#a855f7",  // Purple
    ink: isLight ? "#0f172a" : "#f3f4f6",
    inkMuted: isLight ? "#64748b" : "#9ca3af",
    grid: isLight ? "rgba(0, 0, 0, 0.05)" : "rgba(255, 255, 255, 0.05)",
    border: isLight ? "#e2e8f0" : "rgba(255, 255, 255, 0.08)",
    surface: isLight ? "#ffffff" : "#10121a",
  };

  const catColors = ["#6366f1", "#a855f7", "#ec4899", "#f59e0b", "#10b981", "#3b82f6"];
  const emoColors = ["#10b981", "#3b82f6", "#f59e0b", "#8b8fa3", "#ef4444", "#a855f7"];

  let pieChart, barChart, trendChart, categoryChart, emotionChart;

  // Global Chart.js defaults configuration
  if (typeof Chart !== "undefined") {
    Chart.defaults.color = colors.inkMuted;
    Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
    Chart.defaults.font.size = 12;
  }

  // =========================================================================
  // Load Dashboard Data
  // =========================================================================
  async function loadDashboard() {
    try {
      // Fetch stats summary
      const resStats = await fetch("/api/stats");
      const data = await resStats.json();

      // Stat counters
      animateCounter("statTotal", data.total);
      animateCounter("statPositive", data.positive);
      animateCounter("statNegative", data.negative);
      animateCounter("statNeutral", data.neutral);

      // Simple metrics
      const avgEl = document.getElementById("statAvgPolarity");
      if (avgEl) avgEl.textContent = data.avg_polarity.toFixed(2);

      const catEl = document.getElementById("statCategory");
      if (catEl) catEl.textContent = data.most_common_category || "N/A";

      const emoEl = document.getElementById("statEmotion");
      if (emoEl) emoEl.textContent = data.most_common_emotion || "N/A";

      const growthEl = document.getElementById("statGrowth");
      if (growthEl) {
        const g = data.monthly_growth;
        growthEl.textContent = (g >= 0 ? "+" : "") + g + "%";
        growthEl.style.color = g >= 0 ? colors.positive : colors.negative;
      }

      // Render Charts
      if (typeof Chart !== "undefined") {
        renderTrendChart(data.trend);
        renderCategoryChart(data.categories);
        renderEmotionChart(data.emotions);
        renderPieChart(data);
        renderBarChart(data);
      } else {
        console.warn("Chart.js is not loaded. Skipping chart rendering.");
      }

      // Render side bento elements
      renderKeywords(data.keyword_freq);
      renderInsights(data.insights);

      // Load Recent Feedback
      loadRecentFeedback();

    } catch (err) {
      console.error("Dashboard statistics loading failed:", err);
    }
  }

  // =========================================================================
  // Load Recent Feedback Table
  // =========================================================================
  async function loadRecentFeedback() {
    const tableBody = document.getElementById("recentFeedbackTable");
    if (!tableBody) return;

    try {
      const res = await fetch("/api/search?per_page=5");
      const data = await res.json();

      if (!data.results || data.results.length === 0) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="5" class="text-center text-muted" style="padding: 32px;">
              No feedback entries found. Submit some feedback to see details here!
            </td>
          </tr>`;
        return;
      }

      tableBody.innerHTML = data.results.map(function (fb) {
        let textTrunc = fb.feedback_text.length > 90 ? fb.feedback_text.substring(0, 90) + "..." : fb.feedback_text;
        let sentTag = fb.sentiment.toLowerCase() === "positive" ? "tag--pos" : 
                      fb.sentiment.toLowerCase() === "negative" ? "tag--neg" : "tag--neu";
        
        let dateObj = new Date(fb.created_at);
        let dateStr = dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });

        return `
          <tr onclick="window.location.href='/feedback/${fb.id}'" style="cursor: pointer;">
            <td><strong>${escapeHtml(textTrunc)}</strong></td>
            <td><span class="tag tag--cat">${escapeHtml(fb.category)}</span></td>
            <td><span class="tag ${sentTag}">${escapeHtml(fb.sentiment)}</span></td>
            <td><span class="tag tag--emotion">${escapeHtml(fb.emotion)}</span></td>
            <td><span class="text-muted">${dateStr}</span></td>
          </tr>`;
      }).join("");

    } catch (err) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="5" class="text-center text-muted" style="padding: 24px; color: var(--negative);">
            Error loading recent feedback list.
          </td>
        </tr>`;
    }
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // =========================================================================
  // Animated Counter
  // =========================================================================
  function animateCounter(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 25));
    const timer = setInterval(function () {
      current += step;
      if (current >= target) {
        current = target;
        clearInterval(timer);
      }
      el.textContent = current.toLocaleString();
    }, 25);
  }

  // =========================================================================
  // Chart Renderers (Dark/Light mode optimized)
  // =========================================================================
  function renderTrendChart(trendMap) {
    const ctx = document.getElementById("trendChart");
    if (!ctx) return;
    if (trendChart) trendChart.destroy();

    const months = Object.keys(trendMap || {}).sort();
    if (months.length === 0) return;

    trendChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: months,
        datasets: [
          {
            label: "Positive",
            data: months.map(m => trendMap[m].Positive || 0),
            borderColor: colors.positive,
            backgroundColor: "rgba(16, 185, 129, 0.08)",
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
          {
            label: "Negative",
            data: months.map(m => trendMap[m].Negative || 0),
            borderColor: colors.negative,
            backgroundColor: "rgba(239, 68, 68, 0.08)",
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
          {
            label: "Neutral",
            data: months.map(m => trendMap[m].Neutral || 0),
            borderColor: colors.neutral,
            backgroundColor: "rgba(139, 143, 163, 0.08)",
            fill: true,
            tension: 0.4,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: "index" },
        plugins: {
          legend: { position: "top", labels: { color: colors.ink, padding: 12, usePointStyle: true, boxWidth: 8 } },
          tooltip: { padding: 10, cornerRadius: 8 },
        },
        scales: {
          x: { ticks: { color: colors.inkMuted }, grid: { display: false } },
          y: { beginAtZero: true, ticks: { color: colors.inkMuted, precision: 0 }, grid: { color: colors.grid } },
        },
      },
    });
  }

  function renderCategoryChart(categories) {
    const ctx = document.getElementById("categoryChart");
    if (!ctx || !categories) return;
    if (categoryChart) categoryChart.destroy();

    const labels = Object.keys(categories);
    const values = labels.map(k => categories[k]);

    categoryChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: catColors.slice(0, labels.length),
          borderWidth: 0,
          hoverOffset: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
        plugins: {
          legend: { position: "right", labels: { color: colors.ink, padding: 12, usePointStyle: true, boxWidth: 8 } },
        },
      },
    });
  }

  function renderEmotionChart(emotions) {
    const ctx = document.getElementById("emotionChart");
    if (!ctx || !emotions) return;
    if (emotionChart) emotionChart.destroy();

    const labels = Object.keys(emotions);
    const values = labels.map(k => emotions[k]);

    emotionChart = new Chart(ctx, {
      type: "polarArea",
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: emoColors.slice(0, labels.length).map(c => c + "CC"),
          borderWidth: 1,
          borderColor: colors.surface,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "right", labels: { color: colors.ink, padding: 12, usePointStyle: true, boxWidth: 8 } },
        },
        scales: {
          r: {
            ticks: { display: false },
            grid: { color: colors.grid },
            angleLines: { color: colors.grid }
          },
        },
      },
    });
  }

  function renderPieChart(data) {
    const ctx = document.getElementById("pieChart");
    if (!ctx) return;
    if (pieChart) pieChart.destroy();
    
    pieChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Positive", "Negative", "Neutral"],
        datasets: [{
          data: [data.positive, data.negative, data.neutral],
          backgroundColor: [colors.positive, colors.negative, colors.neutral],
          borderWidth: 0,
          hoverOffset: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
        plugins: {
          legend: { position: "right", labels: { color: colors.ink, padding: 12, usePointStyle: true, boxWidth: 8 } },
        },
      },
    });
  }

  function renderBarChart(data) {
    const ctx = document.getElementById("barChart");
    if (!ctx) return;
    if (barChart) barChart.destroy();
    
    barChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: ["Positive", "Negative", "Neutral"],
        datasets: [{
          label: "Feedback Count",
          data: [data.positive, data.negative, data.neutral],
          backgroundColor: [colors.positive, colors.negative, colors.neutral],
          borderRadius: 8,
          borderSkipped: false,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: colors.inkMuted }, grid: { display: false } },
          y: { beginAtZero: true, ticks: { color: colors.inkMuted, precision: 0 }, grid: { color: colors.grid } },
        },
      },
    });
  }

  // =========================================================================
  // Keywords Grid
  // =========================================================================
  function renderKeywords(keywordFreq) {
    const grid = document.getElementById("keywordsGrid");
    if (!grid) return;

    if (!keywordFreq || keywordFreq.length === 0) {
      grid.innerHTML = '<p class="text-muted">No keyword data extracted yet.</p>';
      return;
    }

    grid.innerHTML = keywordFreq.map(function (item, i) {
      return `
        <div class="keyword-item">
          <span class="keyword-item__rank">#${i + 1}</span>
          <span class="keyword-item__word">${escapeHtml(item[0])}</span>
          <span class="keyword-item__count">${item[1]}</span>
        </div>`;
    }).join("");
  }

  // =========================================================================
  // AI Insights List
  // =========================================================================
  function renderInsights(insights) {
    const list = document.getElementById("insightsList");
    if (!list) return;

    if (!insights || insights.length === 0) {
      list.innerHTML = '<li class="text-muted">Analyzing customer reviews to compile insights...</li>';
      return;
    }

    list.innerHTML = insights.map(function (insight) {
      return `<li class="insight-item">${escapeHtml(insight)}</li>`;
    }).join("");
  }

  // Initial dashboard load
  loadDashboard();
});
