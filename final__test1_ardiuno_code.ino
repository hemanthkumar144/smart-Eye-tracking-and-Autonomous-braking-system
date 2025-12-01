// ---------- PIN CONFIGURATION ----------
int buzzer = 8;     
int leftLED = 9;    
int rightLED = 10;  

// Motor A (Left Motor)
int ENA = 5;
int IN1 = 6;
int IN2 = 7;

// Motor B (Right Motor)
int ENB = 3;
int IN3 = 11;
int IN4 = 12;

// ---------- SPEED LEVELS ----------
int SPEED_NORMAL = 255;
int SPEED_STAGE_A = 200;
int SPEED_STAGE_B = 150;

// ---------- SYSTEM STATE ----------
bool systemStarted = false;   // new flag for start command

// ---------- SETUP ----------
void setup() {
  Serial.begin(9600);

  pinMode(buzzer, OUTPUT);
  pinMode(leftLED, OUTPUT);
  pinMode(rightLED, OUTPUT);

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // Motors forward direction but do NOT start yet
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);

  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
}

// ---------- MAIN LOOP ----------
void loop() {

  if (Serial.available()) {
    char stage = Serial.read();

    // ---------- SYSTEM START ----------
    if (stage == 'S') {
      systemStarted = true;
      analogWrite(ENA, SPEED_NORMAL);
      analogWrite(ENB, SPEED_NORMAL);
      noTone(buzzer);

      Serial.println("System Started: Motors ON");
    }

    // Do nothing unless system started
    if (!systemStarted) return;

    // ---------- Stage A: First Warning ----------
    if (stage == 'A') {
      tone(buzzer, 3000, 2000);

      analogWrite(ENA, SPEED_STAGE_A);
      analogWrite(ENB, SPEED_STAGE_A);
    }

    // ---------- Stage B: Hazards + Buzzer ----------
    else if (stage == 'B') {
      tone(buzzer, 3000, 500);

      digitalWrite(leftLED, HIGH);
      digitalWrite(rightLED, HIGH);
      delay(3000);
      digitalWrite(leftLED, LOW);
      digitalWrite(rightLED, LOW);

      analogWrite(ENA, SPEED_STAGE_B);
      analogWrite(ENB, SPEED_STAGE_B);
    }

    // ---------- Stage C: Full Brake + Hazards ----------
    else if (stage == 'C') {

      tone(buzzer, 2000);  // continuous alarm

      // Gradual braking
      for (int speed = SPEED_STAGE_B; speed >= 0; speed -= 20) {

        analogWrite(ENA, speed);
        analogWrite(ENB, speed);

        digitalWrite(leftLED, HIGH);
        digitalWrite(rightLED, HIGH);
        delay(500);

        digitalWrite(leftLED, LOW);
        digitalWrite(rightLED, LOW);
        delay(500);
      }

      analogWrite(ENA, 0);
      analogWrite(ENB, 0);
    }

    // ---------- Normal Mode (eyes open) ----------
    else if (stage == 'N') {
      noTone(buzzer);
      digitalWrite(leftLED, LOW);
      digitalWrite(rightLED, LOW);

      analogWrite(ENA, SPEED_NORMAL);
      analogWrite(ENB, SPEED_NORMAL);
    }
  }
}
