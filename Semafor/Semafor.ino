int ns_v = 2; int ns_g = 4; int ns_r = 6;
int ev_v = 3; int ev_g = 5; int ev_r = 7;

// Lasam starea goala ca sa forțăm semaforul să asculte de Python din prima secundă
char axaCurentaVerde = 'X'; 

void setup() {
  Serial.begin(9600);
  
  pinMode(ns_v, OUTPUT); pinMode(ns_g, OUTPUT); pinMode(ns_r, OUTPUT);
  pinMode(ev_v, OUTPUT); pinMode(ev_g, OUTPUT); pinMode(ev_r, OUTPUT);

  // La pornire, stingem tot pana ne zice AI-ul ce sa facem
  digitalWrite(ns_v, LOW); digitalWrite(ns_g, LOW); digitalWrite(ns_r, LOW);
  digitalWrite(ev_v, LOW); digitalWrite(ev_g, LOW); digitalWrite(ev_r, LOW);
}

void VerdePentruNordSud() {
  if (axaCurentaVerde == 'E') { // Daca celalalt era verde, facem tranzitia corecta
    digitalWrite(ev_v, LOW); digitalWrite(ev_g, HIGH); delay(2000);
    digitalWrite(ev_g, LOW); digitalWrite(ev_r, HIGH); delay(1000);
  }
  // Aprindem Nord-Sud
  digitalWrite(ns_r, LOW); digitalWrite(ns_v, HIGH);
  digitalWrite(ev_v, LOW); digitalWrite(ev_g, LOW); digitalWrite(ev_r, HIGH);
}

void VerdePentruEstVest() {
  if (axaCurentaVerde == 'N') { // Daca celalalt era verde, facem tranzitia
    digitalWrite(ns_v, LOW); digitalWrite(ns_g, HIGH); delay(2000);
    digitalWrite(ns_g, LOW); digitalWrite(ns_r, HIGH); delay(1000);
  }
  // Aprindem Est-Vest
  digitalWrite(ev_r, LOW); digitalWrite(ev_v, HIGH);
  digitalWrite(ns_v, LOW); digitalWrite(ns_g, LOW); digitalWrite(ns_r, HIGH);
}

void loop() {
  if (Serial.available() > 0) {
    char comanda = Serial.read();

    if (comanda == 'N' && axaCurentaVerde != 'N') {
      VerdePentruNordSud();
      axaCurentaVerde = 'N';
    }
    else if (comanda == 'E' && axaCurentaVerde != 'E') {
      VerdePentruEstVest();
      axaCurentaVerde = 'E';
    }
  }
}
