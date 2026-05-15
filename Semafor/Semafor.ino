// Pinii pentru Semaforul 1 (Banda 1)
int led1v = 2;
int led1g = 5;
int led1r = 8;

// Pinii pentru Semaforul 2 (Banda 2)
int led2v = 3;
int led2g = 6;
int led2r = 9;

// Pinii pentru Semaforul 3 (Tot Banda 2 - sens opus)
int led3v = 4;
int led3g = 7;
int led3r = 10;

// Starea initiala a sistemului ('B' = Ambele Rosu)
char stareCurenta = 'B'; 

// --- FUNCTII AJUTATOARE PENTRU CONTROLUL BENZILOR ---

// Functie pentru a controla rapid Banda 1
void SetareBanda1(int stareRosu, int stareGalben, int stareVerde) {
  digitalWrite(led1r, stareRosu);
  digitalWrite(led1g, stareGalben);
  digitalWrite(led1v, stareVerde);
}

// Functie pentru a controla rapid Banda 2 (Semaforul 2 si 3 in paralel)
void SetareBanda2(int stareRosu, int stareGalben, int stareVerde) {
  digitalWrite(led2r, stareRosu);
  digitalWrite(led2g, stareGalben);
  digitalWrite(led2v, stareVerde);
  
  digitalWrite(led3r, stareRosu);
  digitalWrite(led3g, stareGalben);
  digitalWrite(led3v, stareVerde);
}

void setup() {
  Serial.begin(9600); // Initiem comunicarea cu Python
  
  // Setam pinii ca OUTPUT
  pinMode(led1v, OUTPUT); pinMode(led2v, OUTPUT); pinMode(led3v, OUTPUT);
  pinMode(led1g, OUTPUT); pinMode(led2g, OUTPUT); pinMode(led3g, OUTPUT);
  pinMode(led1r, OUTPUT); pinMode(led2r, OUTPUT); pinMode(led3r, OUTPUT);
  
  // La inceput, pornim macheta pe ROSU COMPLET (Siguranta)
  SetareBanda1(HIGH, LOW, LOW); 
  SetareBanda2(HIGH, LOW, LOW);
}

void loop() {
  // Verificam daca laptopul (AI-ul) ne trimite comenzi
  if (Serial.available() > 0) {
    char comanda = Serial.read();

    // ---------------------------------------------------------
    // COMANDA 'N' -> BANDA 1 VERDE, BANDA 2 ROSU
    // ---------------------------------------------------------
    if (comanda == 'N' && stareCurenta != 'N') {
      
      // Daca inainte aveam verde pe Banda 2, o oprim elegant
      if (stareCurenta == 'E') {
        SetareBanda2(LOW, HIGH, LOW); // Galben Banda 2
        delay(2000);                  // Asteptam 2 secunde
        SetareBanda2(HIGH, LOW, LOW); // Rosu Banda 2
        delay(500);                   // Pauza de siguranta (toata lumea sta)
      }
      
      // Dam verde la Banda 1
      SetareBanda1(LOW, LOW, HIGH); 
      stareCurenta = 'N';
    }
    
    // ---------------------------------------------------------
    // COMANDA 'E' -> BANDA 1 ROSU, BANDA 2 VERDE
    // ---------------------------------------------------------
    else if (comanda == 'E' && stareCurenta != 'E') {
      
      // Daca inainte aveam verde pe Banda 1, o oprim elegant
      if (stareCurenta == 'N') {
        SetareBanda1(LOW, HIGH, LOW); // Galben Banda 1
        delay(2000);                  // Asteptam 2 secunde
        SetareBanda1(HIGH, LOW, LOW); // Rosu Banda 1
        delay(500);                   // Pauza de siguranta
      }
      
      // Dam verde la Banda 2
      SetareBanda2(LOW, LOW, HIGH);
      stareCurenta = 'E';
    }

    // ---------------------------------------------------------
    // COMANDA 'B' -> BLOCAJ INTERSECTIE (AMBELE ROSU)
    // ---------------------------------------------------------
    else if (comanda == 'B' && stareCurenta != 'B') {
      
      // Oprim elegant oricare banda care are verde in acest moment
      if (stareCurenta == 'N') {
        SetareBanda1(LOW, HIGH, LOW); 
        delay(2000);
        SetareBanda1(HIGH, LOW, LOW); 
      } 
      else if (stareCurenta == 'E') {
        SetareBanda2(LOW, HIGH, LOW); 
        delay(2000);
        SetareBanda2(HIGH, LOW, LOW); 
      }
      
      // Acum totul este Rosu si asteptam eliberarea centrului
      stareCurenta = 'B';
    }
  }
}