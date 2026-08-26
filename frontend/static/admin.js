const root = document.documentElement;
const themeToggle = document.querySelector("#themeToggle");
const keyInput = document.querySelector("#adminKey");
const notice = document.querySelector("#adminNotice");

function setTheme(mode) {
  root.classList.toggle("dark", mode === "dark");
  localStorage.setItem("xflexy-theme", mode);
  if (themeToggle) themeToggle.textContent = mode === "dark" ? "☀" : "☾";
}

function pill(status) {
  return `<span class="pill ${status}">${status}</span>`;
}

function metric(label, value) {
  return `<article class="metric"><span>${label}</span><strong>${value}</strong></article>`;
}

function render(data) {
  const orders = data.orders || [];
  const today = new Date().toISOString().slice(0, 10);
  const todayOrders = orders.filter((order) => String(order.created_at).slice(0, 10) === today);
  const completed = orders.filter((order) => order.status === "completed");
  const pending = orders.filter((order) => ["pending", "awaiting_payment", "paid", "processing"].includes(order.status));
  const total = completed.reduce((sum, order) => sum + Number(order.amount || 0), 0);
  document.querySelector("#metrics").innerHTML = [
    metric("عمليات اليوم", todayOrders.length),
    metric("مكتملة", completed.length),
    metric("معلقة", pending.length),
    metric("إجمالي المبالغ", `${total.toLocaleString("fr-DZ")} دج`),
  ].join("");
  document.querySelector("#tableCount").textContent = `${orders.length} عملية`;
  document.querySelector("#ordersTable").innerHTML = orders.map((order) => `
    <tr>
      <td>${order.order_id}</td>
      <td>${order.phone_number}</td>
      <td>${Number(order.amount).toLocaleString("fr-DZ")} دج</td>
      <td>${pill(order.status)}</td>
      <td>${order.created_at}</td>
    </tr>
  `).join("") || `<tr><td colspan="5">لا توجد عمليات بعد.</td></tr>`;
  document.querySelector("#simList").innerHTML = [
    ["Mobilis SIM-01", "جاهزة", "completed"],
    ["Djezzy SIM-02", "قيد المتابعة", "pending"],
    ["Ooredoo SIM-03", "بانتظار الدفع", "awaiting_payment"],
  ].map(([name, state, cls]) => `<div class="sim-item"><strong>${name}</strong><div>${pill(cls)} ${state}</div></div>`).join("");
  const max = Math.max(orders.length, 1);
  const rows = [
    ["معدل النجاح", completed.length],
    ["طلبات معلقة", pending.length],
    ["طلبات فاشلة", orders.filter((order) => order.status === "failed").length],
  ];
  document.querySelector("#reportBars").innerHTML = rows.map(([label, value]) => `
    <div class="bar-row"><strong>${label}</strong><div class="bar"><i style="width:${Math.round((value / max) * 100)}%"></i></div></div>
  `).join("");
}

setTheme(localStorage.getItem("xflexy-theme") || "light");
themeToggle?.addEventListener("click", () => setTheme(root.classList.contains("dark") ? "light" : "dark"));
keyInput.value = localStorage.getItem("xflexy-admin-key") || "";

document.querySelector("#adminKeyForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  notice.className = "notice";
  notice.textContent = "جاري تحميل لوحة الإدارة...";
  try {
    const key = keyInput.value.trim();
    const response = await fetch("/admin/demo-dashboard", { headers: { "x-admin-api-key": key } });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "مفتاح الإدارة غير صحيح");
    localStorage.setItem("xflexy-admin-key", key);
    render(data);
    notice.textContent = "تم تحديث البيانات.";
  } catch (error) {
    notice.className = "notice error";
    notice.textContent = error.message;
  }
});
