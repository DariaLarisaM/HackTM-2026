// ==========================================
// 1. INIȚIALIZAREA HĂRȚII INTERACTIVE (LEAFLET)
// ==========================================
// Setăm harta pe Timișoara (Bd. Take Ionescu)
const map = L.map('map').setView([45.753, 21.232], 16);

// Adăugăm designul vizual al hărții
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap UrbanPulse'
}).addTo(map);

// Creăm cercul care reprezintă intersecția pe hartă
const intersectionMarker = L.circle([45.753, 21.232], {
    color: 'red',
    fillColor: '#f03',
    fillOpacity: 0.6,
    radius: 30
}).addTo(map);

intersectionMarker.bindPopup("<b>Intersecție Take Ionescu</b><br>Semafor: Așteptare date...");

// ==========================================
// 2. CONEXIUNEA WEBSOCKET CU AI-UL (Codul tău)
// ==========================================
const socket = new WebSocket('ws://localhost:8765');

// Când conexiunea reușește
socket.onopen = function(e) {
    console.log("[City Glow] Conectat cu succes la AI-ul Video!");
    document.getElementById("liveBadge").innerText = "LIVE (Conectat)";
    document.getElementById("liveBadge").style.backgroundColor = "#00e676";
};

// Când primim date în timp real de la Python
socket.onmessage = function(event) {
    const dateLive = JSON.parse(event.data);
    console.log("Date primite: ", dateLive);

    // --- A. ACTUALIZĂM UI-UL TĂU EXISTENT ---
    
    // a. Aglomerația pe benzi
    document.getElementById("incidentText").innerText = 
        `Banda 1 (Take Ionescu): ${dateLive.objects_b1} mașini.\n` + 
        `Banda 2 (Michelangelo): ${dateLive.objects_b2} mașini.`;

    // b. Schimbăm semafoarele în text/iconițe
    if (dateLive.state === "1") {
        document.getElementById("mapLightA").innerHTML = '<i class="mini red"></i><i class="mini yellow"></i><i class="mini green active"></i>';
        document.getElementById("mapLightB").innerHTML = '<i class="mini red active"></i><i class="mini yellow"></i><i class="mini green"></i>';
    } else {
        document.getElementById("mapLightA").innerHTML = '<i class="mini red active"></i><i class="mini yellow"></i><i class="mini green"></i>';
        document.getElementById("mapLightB").innerHTML = '<i class="mini red"></i><i class="mini yellow"></i><i class="mini green active"></i>';
    }

    // c. Sistemul de Incidente / Blocaje
    if (dateLive.incident === true) {
        document.getElementById("incidentPin").style.display = "block";
        document.getElementById("activeIncidents").innerText = "1";
        document.getElementById("crewMini").innerText = dateLive.crew_status;
        document.getElementById("crewMini").style.color = "#ff4d4d";
    } else {
        document.getElementById("incidentPin").style.display = "none";
        document.getElementById("activeIncidents").innerText = "0";
        document.getElementById("crewMini").innerText = "standby";
        document.getElementById("crewMini").style.color = "white";
    }

    // --- B. ACTUALIZĂM HARTA INTERACTIVĂ ---
    
    // Ne folosim de 'dateLive.state' ca să schimbăm și culoarea cercului de pe hartă
    if (dateLive.state === "1") {
        intersectionMarker.setStyle({color: 'green', fillColor: '#0f3'});
        intersectionMarker.setPopupContent("<b>Intersecție Take Ionescu</b><br>Semafor: VERDE (Trafic prioritizat pe Banda 1)");
    } else {
        intersectionMarker.setStyle({color: 'red', fillColor: '#f03'});
        intersectionMarker.setPopupContent("<b>Intersecție Take Ionescu</b><br>Semafor: ROȘU");
    }
};

// Dacă pică conexiunea
socket.onclose = function(event) {
    console.log("[City Glow] Conexiunea cu AI-ul s-a întrerupt.");
    document.getElementById("liveBadge").innerText = "OFFLINE";
    document.getElementById("liveBadge").style.backgroundColor = "#ff4d4d";
    
    // Facem cercul gri pe hartă dacă pică sistemul
    intersectionMarker.setStyle({color: 'gray', fillColor: '#888'});
    intersectionMarker.setPopupContent("<b>Intersecție Take Ionescu</b><br>Sistem OFFLINE");
};