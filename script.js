document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const themeToggle = document.getElementById("themeToggle");
  const notificationToggle = document.getElementById("notificationToggle");
  const themeIcon = document.getElementById("themeIcon");

  function applyTheme(theme) {
    root.dataset.theme = theme;
    if (themeIcon) themeIcon.textContent = theme === "dark" ? "☀" : "☾";
    const label = themeToggle?.querySelector(".toggle-label");
    if (label) label.textContent = theme === "dark" ? "Light mode" : "Dark mode";
  }
  let savedTheme = "light";
  try { savedTheme = localStorage.getItem("taskflow-theme") || "light"; } catch (e) {}
  applyTheme(savedTheme);
  themeToggle?.addEventListener("click", () => {
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(next);
    try { localStorage.setItem("taskflow-theme", next); } catch (e) {}
  });

  const modal = document.getElementById("taskModal");
  const open = document.getElementById("openTaskModal");
  const close = document.getElementById("closeTaskModal");
  if (open && modal) open.addEventListener("click", () => modal.classList.add("open"));
  if (close && modal) close.addEventListener("click", () => modal.classList.remove("open"));
  if (modal) modal.addEventListener("click", e => { if (e.target === modal) modal.classList.remove("open"); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") modal?.classList.remove("open"); });

  const search = document.getElementById("taskSearch");
  const status = document.getElementById("statusFilter");
  const priority = document.getElementById("priorityFilter");
  const due = document.getElementById("dueFilter");
  const items = [...document.querySelectorAll(".task-item")];
  const noResults = document.getElementById("noResults");
  function filterTasks() {
    let visible = 0;
    items.forEach(item => {
      const matchesSearch = (item.dataset.search || "").includes((search?.value || "").toLowerCase());
      const matchesStatus = !status?.value || item.dataset.status === status.value;
      const matchesPriority = !priority?.value || item.dataset.priority === priority.value;
      const matchesDue = !due?.value || (due.value === "overdue" ? item.dataset.overdue === "yes" : item.dataset.overdue === "no");
      const show = matchesSearch && matchesStatus && matchesPriority && matchesDue;
      item.classList.toggle("hidden", !show);
      if (show) visible++;
    });
    if (noResults) noResults.classList.toggle("hidden", visible !== 0);
  }
  [search, status, priority, due].forEach(control => control?.addEventListener("input", filterTasks));

  const toastRegion = document.getElementById("toastRegion");
  const flash = document.querySelector("[data-toast]");
  function showToast(message) {
    if (!toastRegion || !message) return;
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    toastRegion.appendChild(toast);
    window.setTimeout(() => toast.remove(), 3600);
  }
  if (flash) {
    showToast(flash.textContent.trim());
    flash.remove();
  }

  const overdueCount = Number(document.body.dataset.overdueCount || 0);
  notificationToggle?.addEventListener("click", async () => {
    if (!("Notification" in window)) {
      showToast("Browser notifications are not supported here.");
      return;
    }
    if (Notification.permission === "granted") {
      showToast("Task reminders are already enabled.");
      return;
    }
    const permission = await Notification.requestPermission();
    showToast(permission === "granted" ? "Task reminders enabled." : "Notifications were not enabled.");
    if (permission === "granted" && overdueCount > 0) {
      new Notification("TaskFlow reminder", { body: `You have ${overdueCount} overdue task(s).` });
    }
  });

  // Browser notification reminders for overdue tasks (only after permission is granted).
  if (overdueCount > 0 && "Notification" in window && Notification.permission === "granted") {
    new Notification("TaskFlow reminder", { body: `You have ${overdueCount} overdue task(s).` });
  }
});
