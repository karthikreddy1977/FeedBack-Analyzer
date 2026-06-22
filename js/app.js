/**
 * Pulse — Global Application JavaScript
 * Handles sidebar toggle, dark/light theme, toast notifications,
 * notification bell dropdown, and user dropdown.
 */

document.addEventListener("DOMContentLoaded", function () {

  // =========================================================================
  // Dark / Light Theme (Default: Dark Mode)
  // =========================================================================
  const root = document.documentElement;
  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");
  const savedTheme = localStorage.getItem("pulse-theme");

  // Default behavior is Dark Mode. If 'light' is saved, add 'theme-light' class.
  const isLight = (savedTheme === "light");

  if (isLight) {
    root.classList.add("theme-light");
    if (themeIcon) themeIcon.className = "fas fa-moon";
  } else {
    root.classList.remove("theme-light");
    if (themeIcon) themeIcon.className = "fas fa-sun";
  }

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      root.classList.toggle("theme-light");
      const isLightActive = root.classList.contains("theme-light");
      localStorage.setItem("pulse-theme", isLightActive ? "light" : "dark");
      if (themeIcon) themeIcon.className = isLightActive ? "fas fa-moon" : "fas fa-sun";
    });
  }

  // =========================================================================
  // Sidebar Toggle (mobile)
  // =========================================================================
  const sidebar = document.getElementById("sidebar");
  const sidebarToggle = document.getElementById("sidebarToggle");

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", function (e) {
      e.stopPropagation();
      sidebar.classList.toggle("is-open");
    });

    // Close sidebar on outside click (mobile)
    document.addEventListener("click", function (e) {
      if (sidebar.classList.contains("is-open") &&
          !sidebar.contains(e.target) &&
          !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove("is-open");
      }
    });
  }

  // =========================================================================
  // Toast Notifications
  // =========================================================================
  const toastContainer = document.getElementById("toastContainer");

  // Auto-dismiss flash-based toasts
  document.querySelectorAll("[data-auto-dismiss]").forEach(function (toast) {
    setTimeout(function () { dismissToast(toast); }, 5000);
  });

  // Close button on toasts
  document.querySelectorAll(".toast__close").forEach(function (btn) {
    btn.addEventListener("click", function () {
      dismissToast(btn.closest(".toast"));
    });
  });

  function dismissToast(toast) {
    if (!toast) return;
    toast.classList.add("toast--exiting");
    setTimeout(function () { toast.remove(); }, 300);
  }

  // Global toast function
  window.showToast = function (message, type) {
    type = type || "info";
    var icons = {
      success: "fa-check-circle",
      error: "fa-exclamation-circle",
      info: "fa-info-circle",
    };
    var toast = document.createElement("div");
    toast.className = "toast toast--" + type;
    toast.setAttribute("data-auto-dismiss", "");
    toast.innerHTML =
      '<div class="toast__icon"><i class="fas ' + (icons[type] || icons.info) + '"></i></div>' +
      '<span class="toast__message">' + message + "</span>" +
      '<button class="toast__close" type="button" aria-label="Dismiss">&times;</button>';
    if (toastContainer) toastContainer.appendChild(toast);

    toast.querySelector(".toast__close").addEventListener("click", function () {
      dismissToast(toast);
    });
    setTimeout(function () { dismissToast(toast); }, 5000);
  };

  // =========================================================================
  // Notification Bell Dropdown
  // =========================================================================
  const notifBell = document.getElementById("notifBell");
  const notifDropdown = document.getElementById("notifDropdown");
  const notifBadge = document.getElementById("notifBadge");
  const notifList = document.getElementById("notifList");
  const markAllRead = document.getElementById("markAllRead");

  if (notifBell) {
    notifBell.querySelector(".notif-bell__btn").addEventListener("click", function (e) {
      e.stopPropagation();
      notifDropdown.hidden = !notifDropdown.hidden;
      if (!notifDropdown.hidden) loadNotifications();
      // Close user dropdown
      var udm = document.getElementById("userDropdownMenu");
      if (udm) udm.hidden = true;
    });

    document.addEventListener("click", function (e) {
      if (!notifBell.contains(e.target)) notifDropdown.hidden = true;
    });
  }

  async function loadNotifications() {
    try {
      const res = await fetch("/api/notifications");
      const data = await res.json();

      // Update badge
      if (notifBadge) {
        if (data.unread_count > 0) {
          notifBadge.textContent = data.unread_count > 99 ? "99+" : data.unread_count;
          notifBadge.hidden = false;
        } else {
          notifBadge.hidden = true;
        }
      }

      // Render list
      if (notifList) {
        if (data.notifications.length === 0) {
          notifList.innerHTML = '<p class="notif-dropdown__empty">No notifications</p>';
          return;
        }
        notifList.innerHTML = data.notifications.slice(0, 10).map(function (n) {
          return '<div class="notif-item ' + (n.is_read ? "" : "is-unread") + '" data-id="' + n.id + '">' +
            '<p class="notif-item__msg">' + n.message + "</p>" +
            '<span class="notif-item__time">' + n.created_at + "</span>" +
            "</div>";
        }).join("");

        // Click to mark read
        notifList.querySelectorAll(".notif-item.is-unread").forEach(function (item) {
          item.addEventListener("click", async function () {
            await fetch("/api/notifications/" + item.dataset.id + "/read", { method: "POST" });
            item.classList.remove("is-unread");
            pollBadge();
          });
        });
      }
    } catch (err) {
      // silently fail
    }
  }

  if (markAllRead) {
    markAllRead.addEventListener("click", async function () {
      await fetch("/api/notifications/read-all", { method: "POST" });
      loadNotifications();
    });
  }

  // Poll notification badge count periodically
  async function pollBadge() {
    try {
      const res = await fetch("/api/notifications");
      const data = await res.json();
      if (notifBadge) {
        if (data.unread_count > 0) {
          notifBadge.textContent = data.unread_count > 99 ? "99+" : data.unread_count;
          notifBadge.hidden = false;
        } else {
          notifBadge.hidden = true;
        }
      }
    } catch (e) { /* silent */ }
  }

  // Poll every 30 seconds for new notifications
  if (notifBadge) {
    pollBadge();
    setInterval(pollBadge, 30000);
  }

  // =========================================================================
  // User Dropdown
  // =========================================================================
  const userDropdown = document.getElementById("userDropdown");
  const userDropdownMenu = document.getElementById("userDropdownMenu");

  if (userDropdown) {
    userDropdown.querySelector(".user-dropdown__btn").addEventListener("click", function (e) {
      e.stopPropagation();
      userDropdownMenu.hidden = !userDropdownMenu.hidden;
      // Close notif dropdown
      if (notifDropdown) notifDropdown.hidden = true;
    });

    document.addEventListener("click", function (e) {
      if (!userDropdown.contains(e.target)) userDropdownMenu.hidden = true;
    });
  }
});
