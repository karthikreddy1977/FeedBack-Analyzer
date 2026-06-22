/**
 * Pulse — Feedback Page JavaScript
 * Handles the feedback submission form with AJAX, character counter,
 * and result display.
 */

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("feedbackForm");
  if (!form) return;

  const textarea = document.getElementById("feedback_text");
  const charCount = document.getElementById("charCount");
  const formError = document.getElementById("formError");
  const submitBtn = document.getElementById("submitBtn");
  const resultPanel = document.getElementById("resultPanel");
  const category = document.getElementById("category");

  // Live character counter
  if (textarea && charCount) {
    textarea.addEventListener("input", function () {
      charCount.textContent = textarea.value.length + " / 2000";
    });
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    if (formError) formError.textContent = "";

    const text = textarea.value.trim();
    if (!text) {
      if (formError) formError.textContent = "Please enter feedback before submitting.";
      textarea.focus();
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';

    try {
      const response = await fetch("/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          feedback_text: text,
          category: category ? category.value : "Other",
        }),
      });
      const data = await response.json();

      if (!response.ok || !data.success) {
        if (formError) formError.textContent = data.error || "Something went wrong.";
        return;
      }

      // Display results
      const sentimentColors = {
        Positive: "var(--positive)",
        Negative: "var(--negative)",
        Neutral: "var(--neutral)",
      };

      document.getElementById("resSentiment").textContent = data.sentiment;
      document.getElementById("resSentiment").style.color = sentimentColors[data.sentiment] || "";
      document.getElementById("resPolarity").textContent = data.polarity_score.toFixed(4);
      document.getElementById("resSubjectivity").textContent = data.subjectivity_score.toFixed(4);
      document.getElementById("resEmotion").textContent = data.emotion;
      document.getElementById("resCategory").textContent = data.category;
      document.getElementById("resEcho").textContent = '"' + data.feedback_text + '"';

      // Keywords
      const kwWrap = document.getElementById("resKeywordsWrap");
      const kwContainer = document.getElementById("resKeywords");
      if (data.keywords && kwContainer) {
        kwContainer.innerHTML = data.keywords.split(", ").map(function (kw) {
          return '<span class="keyword-tag">' + kw + "</span>";
        }).join("");
        kwWrap.hidden = false;
      }

      resultPanel.hidden = false;
      resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });

      // Reset form
      form.reset();
      if (charCount) charCount.textContent = "0 / 2000";

      window.showToast && window.showToast("Feedback analyzed successfully!", "success");

    } catch (err) {
      if (formError) formError.textContent = "Network error — please try again.";
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="fas fa-magic"></i> Analyze Sentiment';
    }
  });
});
