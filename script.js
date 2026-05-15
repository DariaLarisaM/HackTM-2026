/**
 * CITY GLOW - Debug Divas Logică Centrală Bridge
 * Utilizat pentru depanarea și centralizarea stărilor WebSocket globale.
 */
console.log("🚀 City Glow unificat cu succes de către Debug Divas!");

function showNotificationToast(message, isUrgent = false) {
    const toast = document.createElement('div');
    toast.className = 'step-card';
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.backgroundColor = isUrgent ? 'var(--danger)' : 'var(--pink)';
    toast.style.color = 'white';
    toast.style.padding = '15px 25px';
    toast.style.borderRadius = '12px';
    toast.style.boxShadow = '0 10px 30px rgba(0,0,0,0.3)';
    toast.innerHTML = `<strong>Notificare:</strong> ${message}`;

    document.body.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 4000);
}