int led1v=2;
int led2v=3;
int led3v=4;
int led1g=5;
int led2g=6;
int led3g=7;
int led1r=8;
int led2r=9;
int led3r=10;

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
  pinMode(led1v, OUTPUT);
  pinMode(led2v, OUTPUT);
  pinMode(led3v, OUTPUT);
  pinMode(led1g, OUTPUT);
  pinMode(led2g, OUTPUT);
  pinMode(led3g, OUTPUT);
  pinMode(led1r, OUTPUT);
  pinMode(led2r, OUTPUT);
  pinMode(led3r, OUTPUT);
}

void loop() {
  
}
