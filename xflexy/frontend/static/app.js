const root = document.documentElement;
const themeToggle = document.querySelector("#themeToggle");
const operators = document.querySelectorAll(".operator");
const amount = document.querySelector("#amount");
const phone = document.querySelector("#phone");
const summary = document.querySelector("#summary");
const notice = document.querySelector("#notice");
const modal = document.querySelector("#successModal");
const closeModalButton = document.querySelector("#closeModal");
let selectedOperator = "Mobilis";

function setTheme(mode) {
  root.classList.toggle("dark", mode === "dark");
  localStorage.setItem("xflexy-theme", mode);
  if (themeToggle) themeToggle.textContent = mode === "dark" ? "☀" : "☾";
}

function refreshSummary() {
  summary.textContent = `${selectedOperator} · ${Number(amount.value).toLocaleString("fr-DZ")} دج`;
}

function openSuccessModal() {
  modal.hidden = false;
  modal.setAttribute("aria-hidden", "false");
  closeModalButton?.focus();
}

function closeSuccessModal() {
  modal.hidden = true;
  modal.setAttribute("aria-hidden", "true");
}

setTheme(localStorage.getItem("xflexy-theme") || "light");
closeSuccessModal();
themeToggle?.addEventListener("click", () => setTheme(root.classList.contains("dark") ? "light" : "dark"));
operators.forEach((button) => {
  button.addEventListener("click", () => {
    operators.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    selectedOperator = button.dataset.operator;
    refreshSummary();
  });
});
amount.addEventListener("change", refreshSummary);

document.querySelector("#chargeForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  notice.className = "notice";
  notice.textContent = "جاري إنشاء الطلب...";
  try {
    const telegram_user_id = Number(localStorage.getItem("xflexy-demo-user") || Date.now().toString().slice(-8));
    localStorage.setItem("xflexy-demo-user", String(telegram_user_id));
    await fetch("/users/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ telegram_user_id, username: "web_demo", full_name: "عميل Xflexy Demo" }),
    });
    const response = await fetch("/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ telegram_user_id, phone_number: phone.value.trim(), amount: Number(amount.value) }),
    });
    const order = await response.json();
    if (!response.ok) throw new Error(order.detail || "تعذر إنشاء الطلب");
    document.querySelector("#orderId").textContent = order.order_id;
    openSuccessModal();
    notice.textContent = "تم إنشاء طلب الشحن التجريبي بنجاح.";
  } catch (error) {
    notice.className = "notice error";
    notice.textContent = error.message;
  }
});

closeModalButton?.addEventListener("click", closeSuccessModal);
modal?.addEventListener("click", (event) => {
  if (event.target === modal) closeSuccessModal();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !modal.hidden) closeSuccessModal();
});
