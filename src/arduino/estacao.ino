void setup() {
  Serial.begin(9600);
}

void loop() {
  // TMP36 (temperatura)
  int leituraTemp = analogRead(A0);
  float tensao = leituraTemp * (5.0 / 1023.0);
  float temperatura = (tensao - 0.5) * 100;

  // Potenciômetro (umidade)
  int leituraUmid = analogRead(A1);
  float umidade = map(leituraUmid, 0, 1023, 0, 100);

  // Envia JSON
  Serial.print("{");
  Serial.print("\"temperatura\":");
  Serial.print(temperatura);
  Serial.print(",\"umidade\":");
  Serial.print(umidade);
  Serial.println("}");

  delay(5000);
}