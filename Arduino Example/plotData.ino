void setup() {
  Serial.begin(115200);
  randomSeed(analogRead(0));  
}

void loop() {
    
  float v1 = random(200, 300) / 10.0;  
  float v2 = random(300, 400) / 10.0;  
  float v3 = random(400, 500) / 10.0;  
  float v4 = random(500, 600) / 10.0;  
  float v5 = random(600, 700) / 10.0;  
    
  Serial.print(v1, 1);
  Serial.print(",");
  Serial.print(v2, 1);
  Serial.print(",");
  Serial.print(v3, 1);
  Serial.print(",");
  Serial.print(v4, 1);
  Serial.print(",");
  Serial.println(v5, 1);


  delay(50);  
}
