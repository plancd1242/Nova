import { apiGet, apiPost } from "./api.js";

const state = { status: null, events: null, chat: [] };
const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", async () => {
  registerServiceWorker();
  bindNavigation();
  bindAuth();
  bindTalk();
  bindActions();
  const session = await apiGet("/api/session").catch(() => ({ authenticated: false }));
  setAuthenticated(session.authenticated);
  if (session.authenticated) startLiveUpdates();
});

function bindAuth() {
  $("loginForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await apiPost("/api/login", { password: $("passwordInput").value });
      $("loginMessage").textContent = "";
      setAuthenticated(true);
      startLiveUpdates();
    } catch {
      $("loginMessage").textContent = "Login failed";
    }
  });
  $("logoutButton").addEventListener("click", async () => {
    await apiPost("/api/logout").catch(() => {});
    stopLiveUpdates();
    setAuthenticated(false);
  });
}

function bindNavigation() {
  document.querySelectorAll("[data-page]").forEach((button) => {
    if (button.tagName !== "BUTTON") return;
    button.addEventListener("click", () => {
      const page = button.dataset.page;
      document.querySelectorAll(".tabs button").forEach((item) => item.classList.toggle("active", item === button));
      document.querySelectorAll(".page").forEach((item) => item.classList.toggle("active", item.dataset.page === page));
    });
  });
}

function bindTalk() {
  $("commandForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const command = $("commandInput").value.trim();
    if (!command) return;
    $("commandInput").value = "";
    addChat("you", command);
    try {
      const result = await apiPost("/api/command", { command });
      addChat("nova", result.response);
      updateStatus(result.status);
    } catch {
      addChat("nova", "I could not reach Nova.");
    }
  });
  $("voiceButton").addEventListener("click", () => addChat("nova", "Voice input is optional and not available in this browser session."));
}

function bindActions() {
  $("manualBackupButton").addEventListener("click", async () => {
    const result = await apiPost("/api/backup/manual").catch(() => ({ response: "Backup failed." }));
    addChat("nova", result.response);
    if (result.status) updateStatus(result.status);
  });
}

function setAuthenticated(authenticated) {
  $("loginView").classList.toggle("hidden", authenticated);
  $("appView").classList.toggle("hidden", !authenticated);
}

function startLiveUpdates() {
  stopLiveUpdates();
  $("connectionState").textContent = "Live";
  state.events = new EventSource("/api/events", { withCredentials: true });
  state.events.addEventListener("status", (event) => updateStatus(JSON.parse(event.data)));
  state.events.onerror = () => {
    $("connectionState").textContent = "Reconnecting";
    fallbackRefresh();
  };
  apiGet("/api/status").then(updateStatus).catch(() => {});
}

function stopLiveUpdates() {
  if (state.events) state.events.close();
  state.events = null;
}

let fallbackTimer = null;
function fallbackRefresh() {
  if (fallbackTimer) return;
  fallbackTimer = setInterval(async () => {
    if (state.events && state.events.readyState === EventSource.OPEN) {
      clearInterval(fallbackTimer);
      fallbackTimer = null;
      return;
    }
    const status = await apiGet("/api/status").catch(() => null);
    if (status) updateStatus(status);
  }, 8000);
}

function updateStatus(status) {
  state.status = status;
  const sensors = status.sensors || {};
  $("novaFace").textContent = status.nova?.face || ":)";
  $("novaMode").textContent = status.nova?.mode || "Ready";
  $("novaStatus").textContent = status.nova?.online ? "Nova is online" : "Nova is offline";
  $("timeValue").textContent = status.time || "N/A";
  $("temperatureValue").textContent = sensors.temperature || "N/A";
  $("humidityValue").textContent = sensors.humidity || "N/A";
  $("lightValue").textContent = sensors.light || "N/A";
  $("voltageValue").textContent = sensors.voltage || "N/A";
  $("wifiValue").textContent = sensors.wifi || "N/A";
  $("backupValue").textContent = status.backup?.latest || "N/A";
  $("batteryValue").textContent = status.battery?.level || "Future";
  $("volumeValue").textContent = status.volume?.display || "N/A";
  renderOled(status.oled || {});
  renderCamera(status.camera || {});
  renderLockdown(status);
  renderBackup(status.backup || {});
  renderHardware(status.hardware || []);
  renderAccounts(status.accounts || {});
  renderSettings(status.settings || {});
  renderNotifications(status.notifications || []);
}

function renderOled(oled) {
  $("oledFace").textContent = oled.face || ":)";
  $("oledTime").textContent = oled.time || "N/A";
  $("oledTemp").textContent = oled.temperature || "N/A";
  $("oledHumidity").textContent = oled.humidity || "N/A";
  $("oledWifi").textContent = oled.wifi || "N/A";
  $("oledVolt").textContent = oled.voltage || "N/A";
  $("oledMode").textContent = oled.mode || "Ready";
}

function renderCamera(camera) {
  $("cameraStatus").textContent = camera.status === "Available" ? "Camera Ready" : "Camera Offline";
}

function renderLockdown(status) {
  $("lockdownStatus").textContent = status.lockdown?.active ? "LOCKDOWN MODE" : "Lockdown Ready";
  $("lockdownCamera").textContent = status.camera?.status || "N/A";
  $("lockdownMotion").textContent = status.motion?.detected === true ? "Motion Detected" : status.motion?.status || "N/A";
  $("lockdownDistance").textContent = status.ultrasonic?.distance_cm ? `${status.ultrasonic.distance_cm.toFixed(1)} cm` : "N/A";
  renderList("alertHistory", status.lockdown?.alerts || [], (item) => item.title || "No alerts");
}

function renderBackup(backup) {
  $("lastBackup").textContent = backup.latest || "N/A";
  $("nextBackup").textContent = backup.next || "N/A";
  renderList("backupHistory", backup.history || [], (item) => item);
}

function renderHardware(items) {
  const list = $("hardwareList");
  list.innerHTML = "";
  items.forEach((item) => {
    const row = document.createElement("article");
    row.className = "hardware-item";
    row.innerHTML = `<span>${statusDot(item.status)}</span><b>${item.name}</b><em>${item.status}</em>`;
    list.append(row);
  });
}

function renderAccounts(accounts) {
  $("currentAccount").textContent = accounts.current || "N/A";
  $("accountAvatar").textContent = (accounts.current || "N").slice(0, 1).toUpperCase();
  const list = $("accountList");
  list.innerHTML = "";
  (accounts.users || []).forEach((account) => {
    const row = document.createElement("article");
    row.className = "account-card";
    row.innerHTML = `<span>${account.avatar}</span><b>${account.name}</b><small>Voice profile future</small>`;
    list.append(row);
  });
}

function renderSettings(settings) {
  renderList("settingsList", Object.entries(settings), ([key, value]) => `${title(key)}: ${value}`);
}

function renderNotifications(items) {
  renderList("notificationList", items, (item) => `${item.title || "Alert"} · ${item.message || ""}`);
}

function renderList(id, items, label) {
  const list = $(id);
  list.innerHTML = "";
  if (!items.length) {
    const empty = document.createElement("article");
    empty.textContent = "Nothing yet";
    list.append(empty);
    return;
  }
  items.forEach((item) => {
    const row = document.createElement("article");
    row.textContent = label(item);
    list.append(row);
  });
}

function addChat(sender, text) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${sender}`;
  bubble.textContent = text;
  $("chatLog").append(bubble);
  $("chatLog").scrollTop = $("chatLog").scrollHeight;
}

function statusDot(status) {
  if (status === "Enabled" || status === "Available" || status === "Connected") return "🟢";
  if (status === "Disabled") return "🟡";
  return "🔴";
}

function title(value) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function registerServiceWorker() {
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/service-worker.js").catch(() => {});
}
