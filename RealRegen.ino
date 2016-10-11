int currentValue = 0;

void setup(){
  Serial.begin(9600);
  pinMode(A6, INPUT);
}
void loop(){
  currentValue = analogRead(A6);
  Serial.println(currentValue);
  delay(100);
}
