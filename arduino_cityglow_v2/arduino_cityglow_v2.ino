int ns_v = 2; int ns_g = 4; int ns_r = 6;
int ev_v = 3; int ev_g = 5; int ev_r = 7;

// Pin opțional pentru alertă vizuală (Near-Miss)
int buzzer_sau_led_alert = 8; 

char axaCurentaVerde = 'X'; 

void setup() {
  Serial.begin(9600);
  
  pinMode(ns_v, OUTPUT); pinMode(ns_g, OUTPUT); pinMode(ns_r, OUTPUT);
  pinMode(ev_v, OUTPUT); pinMode(ev_g, OUTPUT); pinMode(ev_r, OUTPUT);
  pinMode(buzzer_sau_led_alert, OUTPUT);

  // Pornim cu toate pe Rosu (Safety First)
  toateRosii();
}

void toateRosii() {
  digitalWrite(ns_v, LOW); digitalWrite(ns_g, LOW); digitalWrite(ns_r, HIGH);
  digitalWrite(ev_v, LOW); digitalWrite(ev_g, LOW); digitalWrite(ev_r, HIGH);
}

void alertaNearMiss() {
  // O secvență rapidă de flash-uri pentru a avertiza pietonii/șoferii
  for(int i=0; i<3; i++) {
    digitalWrite(buzzer_sau_led_alert, HIGH); delay(100);
    digitalWrite(buzzer_sau_led_alert, LOW); delay(100);
  }
}

void tranzitie(char deLaAxa) {
  if (deLaAxa == 'N') {
    digitalWrite(ns_v, LOW); digitalWrite(ns_g, HIGH);
    delay(1500); // Timp galben
    digitalWrite(ns_g, LOW); digitalWrite(ns_r, HIGH);
  } else if (deLaAxa == 'E') {
    digitalWrite(ev_v, LOW); digitalWrite(ev_g, HIGH);
    delay(1500);
    digitalWrite(ev_g, LOW); digitalWrite(ev_r, HIGH);
  }
  delay(500); // All-red clearance interval (Siguranță sporită)
}

void loop() {
  if (Serial.available() > 0) {
    char comanda = Serial.read();

    // Comanda N: Verde pentru Nord-Sud
    if (comanda == 'N' && axaCurentaVerde != 'N') {
      if (axaCurentaVerde != 'X') tranzitie(axaCurentaVerde);
      digitalWrite(ns_r, LOW); digitalWrite(ns_v, HIGH);
      axaCurentaVerde = 'N';
    }
    // Comanda E: Verde pentru Est-Vest
    else if (comanda == 'E' && axaCurentaVerde != 'E') {
      if (axaCurentaVerde != 'X') tranzitie(axaCurentaVerde);
      digitalWrite(ev_r, LOW); digitalWrite(ev_v, HIGH);
      axaCurentaVerde = 'E';
    }
    // Comanda B: BLOCARE (Urgență / Near-Miss detectat de Python)
    else if (comanda == 'B') {
      toateRosii();
      alertaNearMiss();
      axaCurentaVerde = 'X'; // Resetăm axa pentru a forța o tranzitie viitoare
    }
  }
}