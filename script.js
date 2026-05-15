/**
 * CITY GLOW - Logică Centrală Dashboard
 * Integrează: WebSocket Bridge, Hartă Leaflet și UI Dinamic
 */

// --- 1. CONFIGURARE WEBSOCKET ---
const socket = new WebSocket('ws://localhost:8000/ws/city-data');

socket.onopen = () => {
    console.log("✅ Conectat la City Glow Bridge");
    updateConnectionStatus(true);
};

socket.onclose = () => {
    console.log("❌ Deconectat de la Bridge");
    updateConnectionStatus(false);
};

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log("Date primite din sistem:", data);

    switch(data.type) {
        case 'TRAFFIC_STATS':
            handleTrafficUpdate(data.payload);
            break;
        case 'NEAR_MISS':
            handleNearMiss(data.payload);
            break;
        case 'AUDIO_THREAT':
            handleAudioThreat(data.payload);
            break;
        case 'EMERGENCY_STATUS':
            showToast(data.message);
            break;
    }
};

// --- 2. GESTIONARE DATE LIVE ---

function handleTrafficUpdate(payload) {
    // Actualizăm contoarele din Dashboard Instituție
    const totalCars = payload.b1 + payload.b2;
    document.getElementById('activeIncidents').innerText = totalCars;
    
    // Status Logică
    const logicLabel = document.getElementById('logicMini');
    if (totalCars > 6) {
        logicLabel.innerText = "Congestie";
        logicLabel.style.color = "#ff4d4d";
    } else {
        logicLabel.innerText = "Fluid";
        logicLabel.style.color = "#00ff88";
    }

    // Sincronizăm semafoarele de pe harta desenată (CSS)
    updateMapLights(payload.state);
}

function handleNearMiss(payload) {
    // Alerta vizuală pe hartă
    const pin = document.getElementById('incidentPin');
    pin.style.display = 'flex';
    
    // Actualizăm panoul de incidente
    document.getElementById('incidentText').innerHTML = 
        `<strong>🚨 NEAR-MISS DETECTAT!</strong><br>Frânare violentă detectată (V: ${Math.round(payload.v_init)}km/h). Sistemul a securizat intersecția.`;
    
    showToast("⚠️ INCIDENT PREVENIT DE AI");
    
    // Adăugăm un cerc pe harta Leaflet dacă e inițializată
    if (window.leafletMap) {
        L.circle([45.7537, 21.2257], { color: 'red', radius: 30 }).addTo(window.leafletMap)
            .bindPopup("Near-Miss detectat acum!").openPopup();
    }

    setTimeout(() => { pin.style.display = 'none'; }, 7000);
}

function handleAudioThreat(payload) {
    showToast("🔊 ALERTĂ AUDIO: Impact detectat!");
    document.getElementById('incidentText').innerHTML = 
        `<strong>🔊 SENZOR ACUSTIC:</strong><br>Sunet de impact detectat (Volum: ${Math.round(payload.volume * 100)}%). Echipaj în alertă.`;
}

// --- 3. UI HELPER FUNCTIONS ---

function updateConnectionStatus(isConnected) {
    const badge = document.getElementById('liveBadge');
    const statusText = document.getElementById('connectionStatus');
    
    if (isConnected) {
        badge.innerText = "LIVE";
        badge.style.background = "#00ff88";
        statusText.innerText = "Conexiune activă cu senzorii urbani";
    } else {
        badge.innerText = "OFFLINE";
        badge.style.background = "#ff4d4d";
        statusText.innerText = "Sistemul AI este deconectat...";
    }
}

function updateMapLights(state) {
    const lightA = document.getElementById('mapLightA');
    const lightB = document.getElementById('mapLightB');

    if (state === '1') { // Nord-Sud Verde
        setLightColor(lightA, 'green');
        setLightColor(lightB, 'red');
    } else if (state === '2') { // Est-Vest Verde
        setLightColor(lightA, 'red');
        setLightColor(lightB, 'green');
    } else { // Mod Blocat sau Urgență
        setLightColor(lightA, 'red');
        setLightColor(lightB, 'red');
    }
}

function setLightColor(container, color) {
    if (!container) return;
    const bulbs = container.querySelectorAll('.mini');
    bulbs.forEach(b => b.classList.remove('active'));
    const target = container.querySelector('.' + color);
    if (target) target.classList.add('active');
}

// --- 4. INIȚIALIZARE HARTĂ LEAFLET ---
window.onload = () => {
    if (document.getElementById('map')) {
        window.leafletMap = L.map('map').setView([45.7537, 21.2257], 15);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: 'City Glow &copy; OpenStreetMap'
        }).addTo(window.leafletMap);
        
        // Marker simulat pentru intersecția noastră (Take Ionescu x Michelangelo)
        L.marker([45.7537, 21.2257]).addTo(window.leafletMap)
            .bindPopup("<b>Intersecție Proactivă 01</b><br>Monitorizare Video/Audio Activă.");
    }
};

// --- 5. COMNEZI MANUALE (B2G) ---
function forceGreenWave() {
    fetch('http://localhost:8000/control/emergency', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction: 'manual', state: 'B' })
    })
    .then(r => r.json())
    .then(data => {
        showToast("Undă verde activată!");
        document.getElementById('crewMini').innerText = "IN ROUTE";
    })
    .catch(err => console.error("Eroare comandă:", err));
}

// --- 6. FUNCȚII EXISTENTE (PĂSTRATE) ---
function showToast(msg) {
    const t = document.getElementById('toast');
    t.innerText = msg;
    t.classList.add('active');
    setTimeout(() => t.classList.remove('active'), 3000);
}

function scrollToSection(id) {
    document.getElementById(id).scrollIntoView({ behavior: 'smooth' });
}