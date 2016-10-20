void setup(){
  Serial.begin(9600); //Serieller Port mit Baudrate: 9600
  pinMode(A6, INPUT); // InputPin für Regensensor
}
void loop(){
  if(Serial.read() == 65) //Warten auf "A" vom RasPI
  Serial.println(analogRead(A6)); //Übertragen des Wertes vom Regensensor and RasPI
}
