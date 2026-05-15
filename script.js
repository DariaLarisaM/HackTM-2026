// City Glow — script.js
// Funcționează cu site-ul actual și ascultă date live prin WebSocket.
// IMPORTANT:
// Frontend-ul NU se conectează direct la baza de date.
// Baza de date trebuie citită în backend / Python / server,
// iar serverul trimite către site JSON prin WebSocket, inclusiv data.history.

let type = "citizen";
let currentUser = null;

let socket = null;
let reconnectTimer = null;
let latestVideoState = null;
let forcedMode = false;

const WS_URL = "ws://localhost:8765";

// =====================
// Helper sigur pentru DOM
// =====================
function $(id) {
  return document.getElementById(id);
}

function safeText(id, value) {
  const el = $(id);
  if (el) el.textContent = value;
}

function safeHTML(id, value) {
  const el = $(id);
  if (el) el.innerHTML = value;
}

function safeDisplay(id, value) {
  const el = $(id);
  if (el) el.style.display = value;
}

// =====================
// Navigare / UI general
// =====================
function scrollToSection(id) {
  const section = $(id);
  if (section) {
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function showToast(text) {
  const toast = $("toast");
  if (!toast) return;

  toast.textContent = text;
  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}

// =====================
// Login vechi, dacă pagina încă are modal login
// =====================
function openLogin(t = "citizen") {
  selectType(t);

  const modal = $("loginModal");
  if (modal) modal.classList.add("open");
}

function closeLogin() {
  const modal = $("loginModal");
  if (modal) modal.classList.remove("open");

  if (typeof showLoginForm === "function") {
    showLoginForm();
  }
}

function selectType(t) {
  type = t;

  const citizenTab = $("citizenTab");
  const institutionTab = $("institutionTab");
  const submitBtn = $("submitBtn");
  const loginInfo = $("loginInfo");
  const loginError = $("loginError");
  const createSwitch = $("createSwitch");

  if (citizenTab) citizenTab.classList.toggle("active", t === "citizen");
  if (institutionTab) institutionTab.classList.toggle("active", t === "institution");

  if (submitBtn) {
    submitBtn.textContent = t === "citizen" ? "Intră ca cetățean" : "Intră ca instituție";
  }

  if (loginInfo) {
    loginInfo.textContent = t === "citizen"
      ? "Cetățenii văd harta live, zonele aglomerate și rutele ocolitoare."
      : "Instituțiile văd incidente active, status echipaj și sincronizarea traficului.";
  }

  if (loginError) loginError.classList.remove("show");
  if (createSwitch) createSwitch.style.display = t === "citizen" ? "block" : "none";

  if (typeof showLoginForm === "function") {
    showLoginForm();
  }
}

const defaultCitizenUsers = [
  { email: "cetatean1@cityglow.ro", password: "city123", name: "Cetățean 1" },
  { email: "cetatean2@cityglow.ro", password: "glow123", name: "Cetățean 2" }
];

const institutionUsers = [
  { email: "politie@cityglow.ro", password: "inst123", name: "Poliția Locală" },
  { email: "primarie@cityglow.ro", password: "admin123", name: "Primăria Timișoara" }
];

function getCitizenUsers() {
  const saved = JSON.parse(localStorage.getItem("cityGlowCitizenUsers") || "[]");
  return [...defaultCitizenUsers, ...saved];
}

function saveCitizenUser(user) {
  const saved = JSON.parse(localStorage.getItem("cityGlowCitizenUsers") || "[]");
  saved.push(user);
  localStorage.setItem("cityGlowCitizenUsers", JSON.stringify(saved));
}

function getUsersForType(selectedType) {
  return selectedType === "institution" ? institutionUsers : getCitizenUsers();
}

function showCreateForm() {
  type = "citizen";

  $("citizenTab")?.classList.add("active");
  $("institutionTab")?.classList.remove("active");
  $("loginForm")?.classList.add("hidden");
  $("createForm")?.classList.add("show");

  const createSwitch = $("createSwitch");
  if (createSwitch) createSwitch.style.display = "none";

  safeText("loginInfo", "Creează un cont de cetățean. Conturile de instituție sunt oferite doar de echipa City Glow.");

  $("loginError")?.classList.remove("show");
  $("createError")?.classList.remove("show");
}

function showLoginForm() {
  const loginForm = $("loginForm");
  const createForm = $("createForm");
  const createSwitch = $("createSwitch");

  if (loginForm) loginForm.classList.remove("hidden");
  if (createForm) createForm.classList.remove("show");
  if (createSwitch) createSwitch.style.display = type === "citizen" ? "block" : "none";

  safeText(
    "loginInfo",
    type === "citizen"
      ? "Cetățenii văd harta live, zonele aglomerate și rutele ocolitoare."
      : "Instituțiile văd incidente active, status echipaj și sincronizarea traficului."
  );
}

function createCitizenAccount(e) {
  e.preventDefault();

  const name = $("createName")?.value.trim();
  const email = $("createEmail")?.value.trim().toLowerCase();
  const password = $("createPassword")?.value;
  const error = $("createError");

  if (!name || !email || !password) return;

  const emailExists =
    getCitizenUsers().some(user => user.email === email) ||
    institutionUsers.some(user => user.email === email);

  if (emailExists) {
    if (error) {
      error.textContent = "Există deja un cont cu acest email.";
      error.classList.add("show");
    }
    return;
  }

  const newUser = { name, email, password };
  saveCitizenUser(newUser);

  currentUser = {
    email: newUser.email,
    name: newUser.name,
    role: "citizen"
  };

  updateRoleInterface();
  closeLogin();
  scrollToSection("live-map");
  showToast("Cont cetățean creat. Ai intrat ca " + newUser.name + ".");

  if ($("createName")) $("createName").value = "";
  if ($("createEmail")) $("createEmail").value = "";
  if ($("createPassword")) $("createPassword").value = "";
  if (error) error.classList.remove("show");
}

function fakeLogin(e) {
  e.preventDefault();

  const email = $("loginEmail")?.value.trim().toLowerCase();
  const password = $("loginPassword")?.value;
  const error = $("loginError");

  const user = getUsersForType(type).find(account =>
    account.email === email && account.password === password
  );

  if (!user) {
    if (error) {
      error.classList.add("show");
      error.textContent = "Email sau parolă greșită pentru contul selectat.";
    }
    return;
  }

  if (error) error.classList.remove("show");

  currentUser = {
    email: user.email,
    name: user.name,
    role: type
  };

  updateRoleInterface();
  closeLogin();

  if (type === "institution") {
    scrollToSection("dashboard");
    showToast("Ai intrat ca instituție: " + user.name + ".");
  } else {
    scrollToSection("live-map");
    showToast("Ai intrat ca cetățean: " + user.name + ".");
  }

  if ($("loginEmail")) $("loginEmail").value = "";
  if ($("loginPassword")) $("loginPassword").value = "";
}

function updateRoleInterface() {
  const lockedNote = $("lockedNote");
  const roleBadge = $("roleBadge");
  const institutionTools = $("institutionTools");
  const notifyButton = $("notifyButton");

  if (!currentUser) {
    if (lockedNote) lockedNote.style.display = "block";
    if (roleBadge) roleBadge.classList.remove("show");
    if (institutionTools) institutionTools.classList.remove("show");
    if (notifyButton) notifyButton.textContent = "Trimite notificare";
    return;
  }

  if (lockedNote) lockedNote.style.display = "none";

  if (roleBadge) {
    roleBadge.classList.add("show");
    roleBadge.textContent = currentUser.role === "institution"
      ? "Conectat ca instituție: " + currentUser.name
      : "Conectat ca cetățean: " + currentUser.name;
  }

  if (notifyButton) {
    notifyButton.textContent = currentUser.role === "institution"
      ? "Trimite alertă către cetățeni"
      : "Primește notificare de incident";
  }

  if (institutionTools) {
    institutionTools.classList.toggle("show", currentUser.role === "institution");
  }
}

// =====================
// Notificări
// =====================
async function requestWindowsNotifications() {
  if (!("Notification" in window)) {
    showToast("Browserul nu suportă notificări Windows.");
    return;
  }

  if (Notification.permission === "granted") {
    showToast("Notificările Windows sunt deja activate.");
    return;
  }

  if (Notification.permission === "denied") {
    showToast("Notificările sunt blocate. Activează-le din setările browserului.");
    return;
  }

  const permission = await Notification.requestPermission();

  if (permission === "granted") {
    showToast("Notificările Windows au fost activate.");
    sendWindowsNotification();
  } else {
    showToast("Notificările nu au fost activate.");
  }
}

function sendWindowsNotification() {
  if (!("Notification" in window) || Notification.permission !== "granted") {
    return;
  }

  const notification = new Notification("City Glow — Incident detectat", {
    body: "Trafic ridicat detectat. Recomandăm rută ocolitoare.",
    tag: "city-glow-incident",
    requireInteraction: false
  });

  notification.onclick = function () {
    window.focus();
    scrollToSection("live-map");
    notification.close();
  };
}

async function sendIncidentNotification() {
  if (!currentUser && $("loginModal")) {
    showToast("Trebuie să intri în platformă ca cetățean sau instituție pentru a trimite notificări.");
    openLogin("citizen");
    return;
  }

  if ("Notification" in window && Notification.permission === "default") {
    await Notification.requestPermission();
  }

  sendWindowsNotification();
  showInSiteNotification();
}

function showInSiteNotification() {
  const stack = $("notificationStack");
  if (!stack) return;

  const notification = document.createElement("div");
  notification.className = "wa-notification";

  const now = new Date();
  const time = now.toLocaleTimeString("ro-RO", { hour: "2-digit", minute: "2-digit" });

  notification.innerHTML = `
    <div class="wa-avatar">CG</div>
    <div class="wa-content">
      <div class="wa-top">
        <div class="wa-name">City Glow</div>
        <div class="wa-time">${time}</div>
      </div>
      <div class="wa-message">
        <b>Incident detectat</b><br>
        Trafic ridicat detectat. Recomandăm rută ocolitoare.
      </div>
    </div>
    <button class="wa-close" onclick="closeNotification(this)">×</button>
  `;

  stack.appendChild(notification);

  requestAnimationFrame(() => {
    notification.classList.add("show");
  });

  setTimeout(() => {
    if (notification.parentElement) {
      notification.classList.remove("show");
      setTimeout(() => notification.remove(), 450);
    }
  }, 6500);
}

function closeNotification(button) {
  const notification = button.closest(".wa-notification");
  notification.classList.remove("show");
  setTimeout(() => notification.remove(), 450);
}

// =====================
// WebSocket + procesare video + baza de date prin backend
// =====================
function setConnectionStatus(online) {
  const badge = $("liveBadge");
  const status = $("connectionStatus");

  if (badge) {
    badge.textContent = online ? "LIVE" : "OFFLINE";
    badge.classList.toggle("online", online);

    // Pentru indexInstitutie.html, unde liveBadge are stil inline
    if (online) {
      badge.innerText = "Sistem AI Live";
      badge.style.backgroundColor = "rgba(0, 230, 118, 0.2)";
      badge.style.borderColor = "rgba(0, 230, 118, 0.4)";
      badge.style.color = "#00e676";
    } else {
      badge.innerText = "AI Offline";
      badge.style.backgroundColor = "rgba(255, 77, 77, 0.2)";
      badge.style.borderColor = "rgba(255, 77, 77, 0.4)";
      badge.style.color = "#ff4d4d";
    }
  }

  if (status) {
    status.textContent = online
      ? "Conectat la procesarea video locală."
      : "WebSocket offline. Pornește cityglow_bridge.py / serverul local.";
  }
}

function connectToVideoBridge() {
  try {
    socket = new WebSocket(WS_URL);

    socket.onopen = function () {
      setConnectionStatus(true);
      showToast("Conectat la procesarea video.");
    };

    socket.onmessage = function (event) {
      const data = JSON.parse(event.data);
      latestVideoState = data;

      // 1. Logica existentă pentru semafoare și alerte live
      applyVideoState(data);

      // 2. LOGICA NOUĂ PENTRU ISTORIC / Baza de Date
      // Serverul trebuie să trimită data.history în JSON.
      // Exemplu:
      // {
      //   "state": "V",
      //   "objects_in_zone": 3,
      //   "incident": true,
      //   "history": [
      //     {"ora": "20:45", "text": "Accident detectat pe Strada Aurora", "scor": 92}
      //   ]
      // }
      renderIncidentHistory(data.history);
    };

    socket.onclose = function () {
      setConnectionStatus(false);
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connectToVideoBridge, 2500);
    };

    socket.onerror = function () {
      setConnectionStatus(false);
    };
  } catch (error) {
    setConnectionStatus(false);
    clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(connectToVideoBridge, 2500);
  }
}

function applyVideoState(data) {
  if (forcedMode) return;

  const state = data.state;
  const green = state === "V" || state === "1" || state === 1 || data.main_light === "green";

  const count = Number(
    data.objects_in_zone ??
    data.objects_b1 ??
    data.count ??
    0
  );

  const incident = typeof data.incident === "boolean"
    ? data.incident
    : count >= 2 || green;

  updateLights(green);
  updateIncident(incident, count, data);
  updateLeafletMapIfExists(green, incident);
}

function updateLights(mainGreen) {
  const heroRed = document.querySelector("[data-hero-red]");
  const heroGreen = document.querySelector("[data-hero-green]");

  if (heroRed) heroRed.classList.toggle("active", !mainGreen);
  if (heroGreen) heroGreen.classList.toggle("active", mainGreen);

  setMapLight("mapLightA", mainGreen);
  setMapLight("mapLightB", !mainGreen);

  // Pentru semafoarele din indexInstitutie.html care au innerHTML cu .dot
  setInstitutionLight("mapLightA", mainGreen);
  setInstitutionLight("mapLightB", !mainGreen);
}

function setMapLight(id, green) {
  const el = $(id);
  if (!el) return;

  const red = el.querySelector(".red");
  const greenBulb = el.querySelector(".green");

  if (red) red.classList.toggle("active", !green);
  if (greenBulb) greenBulb.classList.toggle("active", green);
}

function setInstitutionLight(id, green) {
  const el = $(id);
  if (!el || !el.classList.contains("light-container")) return;

  el.innerHTML = green
    ? '<i class="dot red"></i><i class="dot yellow"></i><i class="dot green active"></i>'
    : '<i class="dot red active"></i><i class="dot yellow"></i><i class="dot green"></i>';
}

function updateIncident(active, count, data) {
  const text = $("incidentText");
  const alert = $("alertStatus");
  const crew = $("crewStatus");
  const loc = $("incidentLocation");
  const pin = $("incidentPin");

  const intersection = data.intersection || "Bd. Take Ionescu × Str. Michelangelo";
  const crewStatus = data.crew_status || data.crewStatus || (active ? "în drum" : "standby");

  if (text) {
    if (text.tagName && text.tagName.toLowerCase() === "div" && text.closest(".glass-card")) {
      text.innerHTML = `
        Obiecte detectate în zona ROI:
        <span style="color:#00e676; font-weight:bold">${count}</span><br>
        Stare incident:
        <span style="color:${active ? "#ff6b6b" : "#00e676"}; font-weight:bold">${active ? "ACTIV" : "NORMAL"}</span>
      `;
    } else {
      text.textContent = active
        ? "Trafic ridicat detectat în intersecție. Semaforul a fost actualizat automat pe baza procesării video."
        : "Trafic normal detectat. Intersecția rămâne sincronizată cu procesarea video și cu Arduino.";
    }
  }

  if (alert) alert.textContent = active ? "Alertă activă" : "Monitorizare activă";
  if (crew) crew.textContent = active ? "Status echipaj: " + crewStatus : "Status echipaj: standby";
  if (loc) loc.textContent = active ? "Intersecție monitorizată — " + intersection : "Intersecție monitorizată — Timișoara";

  if (pin) {
    pin.style.display = active ? "grid" : "none";
    if (pin.classList.contains("glass-card") || pin.tagName.toLowerCase() === "div") {
      pin.style.display = active ? "block" : "none";
    }
  }

  safeText("activeIncidents", active ? "1" : "0");
  safeText("crewMini", active ? crewStatus : "standby");
  safeText("logicMini", data.state === "V" || data.state === "1" ? "verde" : "roșu");

  const crewMini = $("crewMini");
  if (crewMini) {
    crewMini.style.color = active ? "#ff4d4d" : "white";
  }

  updateCitizenAlertList(active, intersection);
}

function updateCitizenAlertList(active, intersection) {
  const list = $("alertList");
  if (!list) return;

  if (!active) {
    list.innerHTML = '<div class="empty-state">Momentan nu există incidente active.</div>';
    return;
  }

  list.innerHTML = `
    <div class="alert-item">
      <b>Incident detectat — intersecție monitorizată</b>
      <span>Trafic ridicat detectat în zona ${intersection}. Recomandăm evitarea zonei.</span>
    </div>
    <div class="alert-item">
      <b>Rută ocolitoare activă</b>
      <span>Folosește Str. Pestalozzi pentru a evita zona aglomerată.</span>
    </div>
  `;
}

function renderIncidentHistory(history) {
  const historyContainer = $("incidentHistory");

  if (!historyContainer) return;

  if (!Array.isArray(history) || history.length === 0) {
    historyContainer.innerHTML = `
      <div class="history-item">
        <small>—</small>
        <p>Nu există incidente salvate în istoric.</p>
      </div>
    `;
    return;
  }

  historyContainer.innerHTML = "";

  history.forEach(item => {
    const entry = document.createElement("div");
    entry.className = "history-item";

    const ora = item.ora || item.time || item.timestamp || "—";
    const text = item.text || item.message || "Incident detectat";
    const scor = item.scor ?? item.score ?? item.confidence ?? "-";

    entry.innerHTML = `
      <small>${ora}</small>
      <p>${text} (Scor: ${scor}%)</p>
    `;

    historyContainer.appendChild(entry);
  });
}

function updateLeafletMapIfExists(green, incident) {
  // Dacă pagina instituției are variabila globală intersectionMarker, o actualizăm.
  if (typeof intersectionMarker === "undefined" || !intersectionMarker?.setStyle) {
    return;
  }

  if (incident) {
    intersectionMarker.setStyle({
      color: "#ff4d4d",
      fillColor: "#ff4d4d",
      fillOpacity: 0.6
    });
  } else if (green) {
    intersectionMarker.setStyle({
      color: "#00e676",
      fillColor: "#00e676",
      fillOpacity: 0.4
    });
  } else {
    intersectionMarker.setStyle({
      color: "#ffea00",
      fillColor: "#ffea00",
      fillOpacity: 0.4
    });
  }
}

function forceGreenWave() {
  if (currentUser && currentUser.role !== "institution") {
    showToast("Doar instituția poate controla logica de trafic.");
    return;
  }

  forcedMode = true;
  updateLights(true);
  showToast("Verde forțat din dashboard.");
}

function releaseAutoMode() {
  if (currentUser && currentUser.role !== "institution") {
    showToast("Doar instituția poate controla logica de trafic.");
    return;
  }

  forcedMode = false;

  if (latestVideoState) {
    applyVideoState(latestVideoState);
  }

  showToast("Mod automat activ.");
}

function activateGreenWave() {
  forceGreenWave();
}

// =====================
// Init
// =====================
document.addEventListener("DOMContentLoaded", function () {
  const observerElements = document.querySelectorAll(".reveal, .slide-text");

  if ("IntersectionObserver" in window && observerElements.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("show");
        }
      });
    }, { threshold: 0.18 });

    observerElements.forEach(el => observer.observe(el));
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeLogin();
  });

  const loginModal = $("loginModal");
  if (loginModal) {
    loginModal.addEventListener("click", (e) => {
      if (e.target.id === "loginModal") closeLogin();
    });
  }

  updateRoleInterface();
  setConnectionStatus(false);
  connectToVideoBridge();
});
