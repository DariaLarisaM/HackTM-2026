int led1v=2;
int led2v=3;
int led3v=4;
int led1g=5;
int led2g=6;
int led3g=7;
int led1r=8;
int led2r=9;
int led3r=10;

// Adaugam o variabila ca sa tinem minte in ce stare e semaforul
char stareCurenta = 'R'; 

void AprindeVerde()
{
  digitalWrite(led1r, LOW);
  digitalWrite(led2r, LOW);
  digitalWrite(led3r, LOW);
  digitalWrite(led1g, LOW);
  digitalWrite(led2g, LOW);
  digitalWrite(led3g, LOW);
  digitalWrite(led1v, HIGH);
  digitalWrite(led2v, HIGH);
  digitalWrite(led3v, HIGH);
}

void AprindeGalben()
{
  digitalWrite(led1r, LOW);
  digitalWrite(led2r, LOW);
  digitalWrite(led3r, LOW);
  digitalWrite(led1v, LOW);
  digitalWrite(led2v, LOW);
  digitalWrite(led3v, LOW);
  digitalWrite(led1g, HIGH);
  digitalWrite(led2g, HIGH);
  digitalWrite(led3g, HIGH);
}

void AprindeRosu()
{
  digitalWrite(led1v, LOW);
  digitalWrite(led2v, LOW);
  digitalWrite(led3v, LOW);
  digitalWrite(led1g, LOW);
  digitalWrite(led2g, LOW);
  digitalWrite(led3g, LOW);
  digitalWrite(led1r, HIGH);
  digitalWrite(led2r, HIGH);
  digitalWrite(led3r, HIGH);
}

void setup() {
  Serial.begin(9600); // Initiem comunicarea cu laptopul
  pinMode(led1v, OUTPUT);
  pinMode(led2v, OUTPUT);
  pinMode(led3v, OUTPUT);
  pinMode(led1g, OUTPUT);
  pinMode(led2g, OUTPUT);
  pinMode(led3g, OUTPUT);
  pinMode(led1r, OUTPUT);
  pinMode(led2r, OUTPUT);
  pinMode(led3r, OUTPUT);
  
  // La inceput, pornim macheta pe Rosu
  AprindeRosu(); 
}

void loop() {
  // Verificam daca AI-ul de pe laptop ne-a trimis vreun mesaj prin cablul USB
  if (Serial.available() > 0) {
    char comanda = Serial.read(); // Citim litera primita ('V' sau 'R')

    // Daca AI-ul zice VERDE si noi suntem pe ROSU:
    if (comanda == 'V' && stareCurenta != 'V') {
      AprindeVerde();
      stareCurenta = 'V'; // Actualizam starea
    }
    // Daca AI-ul zice ROSU si noi suntem pe VERDE:
    else if (comanda == 'R' && stareCurenta != 'R') {
      // Facem tranzitia eleganta ca la un semafor real
      AprindeGalben();
      delay(2000); // Tine galbenul aprins 2 secunde
      AprindeRosu();
      stareCurenta = 'R'; // Actualizam starea
    }
  }
}
