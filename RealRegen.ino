int currentValue = 0;
int sentValue = 0;

void setup(){
  Serial.begin(9600);
  pinMode(A6, INPUT);
}
void loop(){
  currentValue = analogRead(A6);
  //sentValue = map(currentValue, 0, 1023, 0, 255);
  Serial.println(currentValue);
  delay(100);
}
