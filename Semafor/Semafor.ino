int led1v = 2;
int led1g = 4;
int led1r = 6;

int led2v = 3;
int led2g = 5;
int led2r = 7;


char stareCurenta = 'B'; 

void SetareBanda1(int stareRosu, int stareGalben, int stareVerde) {
  digitalWrite(led1r, stareRosu);
  digitalWrite(led1g, stareGalben);
  digitalWrite(led1v, stareVerde);
}

void SetareBanda2(int stareRosu, int stareGalben, int stareVerde) {
  digitalWrite(led2r, stareRosu);
  digitalWrite(led2g, stareGalben);
  digitalWrite(led2v, stareVerde);
}

void setup() {
  Serial.begin(9600); 
  
  pinMode(led1v, OUTPUT); pinMode(led2v, OUTPUT);
  pinMode(led1g, OUTPUT); pinMode(led2g, OUTPUT);
  pinMode(led1r, OUTPUT); pinMode(led2r, OUTPUT);
  
  // Pornim pe modul SIGURANTA (Totul Rosu)
  SetareBanda1(HIGH, LOW, LOW); 
  SetareBanda2(HIGH, LOW, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    char comanda = Serial.read();

    // ---------------------------------------------------------
    // COMANDA 'N' -> BANDA 1 VERDE, BANDA 2 ROSU
    // ---------------------------------------------------------
    if (comanda == 'N' && stareCurenta != 'N') {
      
      // 1. Daca Banda 2 avea Verde, o oprim elegant
      if (stareCurenta == 'E') {
        SetareBanda2(LOW, HIGH, LOW); // Galben B2
        delay(2000);                  
        SetareBanda2(HIGH, LOW, LOW); // Rosu B2
        delay(500); // Pauza scurta de siguranta (toata lumea sta)
      }
      
      // 2. Ne asiguram ca B2 este inghetata pe Rosu
      SetareBanda2(HIGH, LOW, LOW);

      // 3. Pregatim Banda 1 pentru plecare (Rosu + Galben ca in realitate)
      SetareBanda1(HIGH, HIGH, LOW); 
      delay(1000); // Asteptam 1 secunda
      
      // 4. Start curat pe Banda 1 (Verde)
      SetareBanda1(LOW, LOW, HIGH); 
      stareCurenta = 'N';
    }
    
    // ---------------------------------------------------------
    // COMANDA 'E' -> BANDA 1 ROSU, BANDA 2 VERDE
    // ---------------------------------------------------------
    else if (comanda == 'E' && stareCurenta != 'E') {
      
      // 1. Daca Banda 1 avea Verde, o oprim elegant
      if (stareCurenta == 'N') {
        SetareBanda1(LOW, HIGH, LOW); // Galben B1
        delay(2000);                  
        SetareBanda1(HIGH, LOW, LOW); // Rosu B1
        delay(500); 
      }

      // 2. Ne asiguram ca B1 este inghetata pe Rosu
      SetareBanda1(HIGH, LOW, LOW);
      
      // 3. Pregatim Banda 2 pentru plecare (Rosu + Galben)
      SetareBanda2(HIGH, HIGH, LOW);
      delay(1000);
      
      // 4. Start curat pe Banda 2 (Verde)
      SetareBanda2(LOW, LOW, HIGH);
      stareCurenta = 'E';
    }

    // ---------------------------------------------------------
    // COMANDA 'B' -> BLOCAJ URGENTA (AMBELE ROSU INSTANTANEU)
    // ---------------------------------------------------------
    else if (comanda == 'B' && stareCurenta != 'B') {
      
      // Trecere BRUSCA pe Rosu absolut pentru toata lumea, fara delay-uri
      SetareBanda1(HIGH, LOW, LOW); 
      SetareBanda2(HIGH, LOW, LOW); 
      
      stareCurenta = 'B';
    }
  }
}