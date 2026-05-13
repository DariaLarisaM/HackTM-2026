let type = "citizen";
    let currentUser = null;

    function scrollToSection(id){
      document.getElementById(id).scrollIntoView({behavior:"smooth", block:"start"});
    }

    function openLogin(t = "citizen"){
      selectType(t);
      document.getElementById("loginModal").classList.add("open");
    }

    function closeLogin(){
      document.getElementById("loginModal").classList.remove("open");
      showLoginForm();
    }

    function selectType(t){
      type = t;
      document.getElementById("citizenTab").classList.toggle("active", t === "citizen");
      document.getElementById("institutionTab").classList.toggle("active", t === "institution");
      document.getElementById("submitBtn").textContent = t === "citizen" ? "Intră ca cetățean" : "Intră ca instituție";
      document.getElementById("loginInfo").textContent = t === "citizen"
        ? "Cetățenii văd harta live, zonele aglomerate și rutele ocolitoare."
        : "Instituțiile văd incidente active, status echipaj și sincronizarea traficului.";

      const error = document.getElementById("loginError");
      if(error) error.classList.remove("show");

      showLoginForm();

      const createSwitch = document.getElementById("createSwitch");
      createSwitch.style.display = t === "citizen" ? "block" : "none";
    }

    const defaultCitizenUsers = [
      { email: "cetatean1@cityglow.ro", password: "city123", name: "Cetățean 1" },
      { email: "cetatean2@cityglow.ro", password: "glow123", name: "Cetățean 2" }
    ];

    const institutionUsers = [
      { email: "politie@cityglow.ro", password: "inst123", name: "Poliția Locală" },
      { email: "primarie@cityglow.ro", password: "admin123", name: "Primăria Timișoara" }
    ];

    function getCitizenUsers(){
      const saved = JSON.parse(localStorage.getItem("cityGlowCitizenUsers") || "[]");
      return [...defaultCitizenUsers, ...saved];
    }

    function saveCitizenUser(user){
      const saved = JSON.parse(localStorage.getItem("cityGlowCitizenUsers") || "[]");
      saved.push(user);
      localStorage.setItem("cityGlowCitizenUsers", JSON.stringify(saved));
    }

    function getUsersForType(selectedType){
      return selectedType === "institution" ? institutionUsers : getCitizenUsers();
    }

    function showCreateForm(){
      type = "citizen";
      document.getElementById("citizenTab").classList.add("active");
      document.getElementById("institutionTab").classList.remove("active");
      document.getElementById("loginForm").classList.add("hidden");
      document.getElementById("createForm").classList.add("show");
      document.getElementById("createSwitch").style.display = "none";
      document.getElementById("loginInfo").textContent = "Creează un cont de cetățean. Conturile de instituție sunt oferite doar de echipa City Glow.";
      document.getElementById("loginError").classList.remove("show");
      document.getElementById("createError").classList.remove("show");
    }

    function showLoginForm(){
      const loginForm = document.getElementById("loginForm");
      const createForm = document.getElementById("createForm");
      const createSwitch = document.getElementById("createSwitch");

      loginForm.classList.remove("hidden");
      createForm.classList.remove("show");
      createSwitch.style.display = type === "citizen" ? "block" : "none";

      document.getElementById("loginInfo").textContent = type === "citizen"
        ? "Cetățenii văd harta live, zonele aglomerate și rutele ocolitoare."
        : "Instituțiile văd incidente active, status echipaj și sincronizarea traficului.";
    }

    function createCitizenAccount(e){
      e.preventDefault();

      const name = document.getElementById("createName").value.trim();
      const email = document.getElementById("createEmail").value.trim().toLowerCase();
      const password = document.getElementById("createPassword").value;
      const error = document.getElementById("createError");

      const emailExists =
        getCitizenUsers().some(user => user.email === email) ||
        institutionUsers.some(user => user.email === email);

      if(emailExists){
        error.textContent = "Există deja un cont cu acest email.";
        error.classList.add("show");
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

      document.getElementById("createName").value = "";
      document.getElementById("createEmail").value = "";
      document.getElementById("createPassword").value = "";
      error.classList.remove("show");
      showLoginForm();
    }

    function fakeLogin(e){
      e.preventDefault();

      const email = document.getElementById("loginEmail").value.trim().toLowerCase();
      const password = document.getElementById("loginPassword").value;
      const error = document.getElementById("loginError");

      const user = getUsersForType(type).find(account =>
        account.email === email && account.password === password
      );

      if(!user){
        error.classList.add("show");
        error.textContent = "Email sau parolă greșită pentru contul selectat.";
        return;
      }

      error.classList.remove("show");

      currentUser = {
        email: user.email,
        name: user.name,
        role: type
      };

      updateRoleInterface();
      closeLogin();

      if(type === "institution"){
        scrollToSection("dashboard");
        showToast("Ai intrat ca instituție: " + user.name + ".");
      } else {
        scrollToSection("live-map");
        showToast("Ai intrat ca cetățean: " + user.name + ".");
      }

      document.getElementById("loginEmail").value = "";
      document.getElementById("loginPassword").value = "";
    }

    function updateRoleInterface(){
      const lockedNote = document.getElementById("lockedNote");
      const roleBadge = document.getElementById("roleBadge");
      const institutionTools = document.getElementById("institutionTools");
      const notifyButton = document.getElementById("notifyButton");

      if(!currentUser){
        lockedNote.style.display = "block";
        roleBadge.classList.remove("show");
        institutionTools.classList.remove("show");
        notifyButton.textContent = "Trimite notificare";
        return;
      }

      lockedNote.style.display = "none";
      roleBadge.classList.add("show");
      roleBadge.textContent = currentUser.role === "institution"
        ? "Conectat ca instituție: " + currentUser.name
        : "Conectat ca cetățean: " + currentUser.name;

      notifyButton.textContent = currentUser.role === "institution"
        ? "Trimite alertă către cetățeni"
        : "Primește notificare de incident";

      if(currentUser.role === "institution"){
        institutionTools.classList.add("show");
      } else {
        institutionTools.classList.remove("show");
      }
    }

    function activateGreenWave(){
      showToast("Undă verde activată pentru echipajul de intervenție.");
    }

    function showToast(text){
      const toast = document.getElementById("toast");
      toast.textContent = text;
      toast.classList.add("show");
      setTimeout(() => toast.classList.remove("show"), 3000);
    }


    async function requestWindowsNotifications(){
      if(!("Notification" in window)){
        showToast("Browserul nu suportă notificări Windows.");
        return;
      }

      if(Notification.permission === "granted"){
        showToast("Notificările Windows sunt deja activate.");
        return;
      }

      if(Notification.permission === "denied"){
        showToast("Notificările sunt blocate. Activează-le din setările browserului.");
        return;
      }

      const permission = await Notification.requestPermission();

      if(permission === "granted"){
        showToast("Notificările Windows au fost activate.");
        sendWindowsNotification();
      } else {
        showToast("Notificările nu au fost activate.");
      }
    }

    function sendWindowsNotification(){
      if(!("Notification" in window) || Notification.permission !== "granted"){
        return;
      }

      const notification = new Notification("City Glow — Incident detectat", {
        body: "Accident auto posibil pe Strada Aurora. Recomandăm rută ocolitoare.",
        tag: "city-glow-incident",
        requireInteraction: false
      });

      notification.onclick = function(){
        window.focus();
        scrollToSection("live-map");
        notification.close();
      };
    }

    async function sendIncidentNotification(){
      if(!currentUser){
        showToast("Trebuie să intri în platformă ca cetățean sau instituție pentru a trimite notificări.");
        openLogin("citizen");
        return;
      }

      if("Notification" in window && Notification.permission === "default"){
        await Notification.requestPermission();
      }

      sendWindowsNotification();

      const stack = document.getElementById("notificationStack");
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
            Accident auto posibil pe Strada Aurora. Recomandăm rută ocolitoare.
          </div>
        </div>
        <button class="wa-close" onclick="closeNotification(this)">×</button>
      `;

      stack.appendChild(notification);

      requestAnimationFrame(() => {
        notification.classList.add("show");
      });

      setTimeout(() => {
        if(notification.parentElement){
          notification.classList.remove("show");
          setTimeout(() => notification.remove(), 450);
        }
      }, 6500);
    }

    function closeNotification(button){
      const notification = button.closest(".wa-notification");
      notification.classList.remove("show");
      setTimeout(() => notification.remove(), 450);
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if(entry.isIntersecting){
          entry.target.classList.add("show");
        }
      });
    }, {threshold:.18});

    document.querySelectorAll(".reveal, .slide-text").forEach(el => observer.observe(el));

    document.addEventListener("keydown", (e) => {
      if(e.key === "Escape") closeLogin();
    });

    document.getElementById("loginModal").addEventListener("click", (e) => {
      if(e.target.id === "loginModal") closeLogin();
    });

    updateRoleInterface();
  
// === City Glow sync cu procesarea video + Arduino ===
let socket = null;
let reconnectTimer = null;
let latestVideoState = null;
let forcedMode = false;
function setConnectionStatus(online){
  const badge=document.getElementById('liveBadge');
  const status=document.getElementById('connectionStatus');
  if(!badge||!status)return;
  badge.textContent=online?'LIVE':'OFFLINE';
  badge.classList.toggle('online', online);
  status.textContent=online?'Conectat la procesarea video locală.':'WebSocket offline. Pornește intersectie_cityglow.py.';
}
function connectToVideoBridge(){
  try{
    socket=new WebSocket('ws://localhost:8765');
    socket.onopen=()=>{setConnectionStatus(true); showToast('Conectat la procesarea video.');};
    socket.onmessage=(event)=>{latestVideoState=JSON.parse(event.data); applyVideoState(latestVideoState);};
    socket.onclose=()=>{setConnectionStatus(false); clearTimeout(reconnectTimer); reconnectTimer=setTimeout(connectToVideoBridge,2500);};
    socket.onerror=()=>setConnectionStatus(false);
  }catch(e){setConnectionStatus(false); clearTimeout(reconnectTimer); reconnectTimer=setTimeout(connectToVideoBridge,2500);}
}
function applyVideoState(data){
  if(forcedMode)return;
  const green=data.state==='V';
  const count=Number(data.objects_in_zone||0);
  const incident=count>=2 || data.incident===true;
  updateLights(green);
  updateIncident(incident,count,data);
}
function updateLights(mainGreen){
  const hr=document.querySelector('[data-hero-red]');
  const hg=document.querySelector('[data-hero-green]');
  if(hr)hr.classList.toggle('active', !mainGreen);
  if(hg)hg.classList.toggle('active', mainGreen);
  setMapLight('mapLightA', mainGreen);
  setMapLight('mapLightB', !mainGreen);
}
function setMapLight(id, green){
  const el=document.getElementById(id); if(!el)return;
  el.querySelector('.red').classList.toggle('active', !green);
  el.querySelector('.green').classList.toggle('active', green);
}
function updateIncident(active,count,data){
  const text=document.getElementById('incidentText');
  const alert=document.getElementById('alertStatus');
  const crew=document.getElementById('crewStatus');
  const loc=document.getElementById('incidentLocation');
  const pin=document.getElementById('incidentPin');
  if(active){
    text.textContent='Trafic ridicat detectat în intersecție. Semaforul a fost actualizat automat pe baza procesării video.';
    alert.textContent='Alertă activă'; crew.textContent='Status echipaj: în drum';
    loc.textContent='Intersecție monitorizată — Bd. Take Ionescu × Str. Michelangelo';
    if(pin)pin.style.display='grid';
  }else{
    text.textContent='Trafic normal detectat. Intersecția rămâne sincronizată cu procesarea video și cu Arduino.';
    alert.textContent='Monitorizare activă'; crew.textContent='Status echipaj: standby';
    loc.textContent='Intersecție monitorizată — Timișoara';
    if(pin)pin.style.display='none';
  }
  const a=document.getElementById('activeIncidents'); if(a)a.textContent=active?'1':'0';
  const c=document.getElementById('crewMini'); if(c)c.textContent=active?'în drum':'standby';
  const l=document.getElementById('logicMini'); if(l)l.textContent=data.state==='V'?'verde':'roșu';
}
function forceGreenWave(){
  if(!currentUser || currentUser.role!=='institution'){showToast('Doar instituția poate controla logica de trafic.'); openLogin('institution'); return;}
  forcedMode=true; updateLights(true); showToast('Verde forțat din dashboard.');
}
function releaseAutoMode(){
  if(!currentUser || currentUser.role!=='institution'){showToast('Doar instituția poate controla logica de trafic.'); openLogin('institution'); return;}
  forcedMode=false; if(latestVideoState)applyVideoState(latestVideoState); showToast('Mod automat activ.');
}
setConnectionStatus(false);
connectToVideoBridge();
