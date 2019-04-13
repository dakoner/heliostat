
#include <AccelStepper.h>

// Define a stepper and the pins it will use
AccelStepper steppers[] = {AccelStepper(1, 2, 5 ), AccelStepper(1, 4, 7)};
int endstopPin = 9;
volatile bool state;

String line;
long t = millis();

bool lastState;
long lastTransition;
void checkState() {
  bool newState = digitalRead(endstopPin);
  t = millis();
  if (newState != lastState) {
    if (t - lastTransition > 10) {

      Serial.print("Endstrop transition to: ");
      Serial.println(newState);
      if (newState == LOW) {
        Serial.println("stopping");
        steppers[0].stop();
        steppers[1].stop();
        steppers[0].setCurrentPosition(0);
      }
      state = newState;
      lastTransition = t;
      lastState = newState;
    }
  }
}

void home() {
  Serial.println("homing");

  while (true) {
    checkState();
    if (state == HIGH) {
      steppers[0].move(1);
      while (steppers[0].run());
    } else {
      break;
    }
  }
  Serial.println("Endstop hit");
  while (true) {
    checkState();
    if (state == LOW) {
      steppers[0].move(-1);
      while (steppers[0].run());
    } else {
      break;
    }
  }
  Serial.println("Homed");
  steppers[0].setCurrentPosition(0);
}

void setup()
{
  Serial.begin(115200);
  while (!Serial) {}

  Serial.println("#MOTOR TOOL");
  steppers[0].setMaxSpeed(1000);
  steppers[0].setAcceleration(1000);
  steppers[1].setMaxSpeed(100);
  steppers[1].setAcceleration(100);
  steppers[0].setPinsInverted(true);
  
  pinMode(endstopPin, INPUT_PULLUP);
  checkState();
}


void output() {
  Serial.print("^P0: ");
  Serial.print(steppers[0].currentPosition());
  Serial.print(" D0: ");
  Serial.print(steppers[0].distanceToGo());
  Serial.print(" S0: ");
  Serial.print(steppers[0].speed());
  Serial.print(" P1: ");
  Serial.print(steppers[1].currentPosition());
  Serial.print(" D1: ");
  Serial.print(steppers[1].distanceToGo());
  Serial.print(" S1: ");
  Serial.print(steppers[1].speed());
  Serial.print(" E0: ");
  Serial.print(state);
  Serial.println();
}


int getMotor(String s) {
  if (s.length() < 2) {
    Serial.print("No motor in string: ");
    Serial.println(s);
    abort();
  }

  String val = s.substring(1, 2);
  int motor = val.toInt();

  return motor;
}

long getPosition(String s) {
  if (s.length() < 4) {
    Serial.print("No position in string: ");
    Serial.println(s);
    abort();
  }

  String val = s.substring(3);
  long position = val.toInt();

  return position;
}


float getSpeed(String s) {
  if (s.length() < 4) {
    Serial.print("No position in string: ");
    Serial.println(s);
    abort();
  }

  String val = s.substring(3);
  float speed = val.toFloat();
  return speed;
}
void process(String s) {
  Serial.print("Process: ");
  Serial.println(s);
  if (s.length() > 0) {
    char cmd = s[0];
    if (cmd == 'M') {
      if (state == LOW && getPosition(s) > steppers[getMotor(s)].currentPosition() )
        Serial.println("Ignore move because stopped.");
      else {
        Serial.print("Move "); Serial.print(getMotor(s)); Serial.print(" to "); Serial.println(getPosition(s));
        steppers[getMotor(s)].moveTo(getPosition(s));
      }
    }
    else if (cmd == 'A') {
      steppers[getMotor(s)].setAcceleration(getPosition(s));
      Serial.print("Acceleration: ");
      Serial.println(getPosition(s));
    }
    else if (cmd == 'S') {
      steppers[getMotor(s)].setMaxSpeed(getSpeed(s));
      Serial.print("Max speed: ");
      Serial.println(getSpeed(s));
    }
    else if (cmd == 'P') {
      output();
    }
    else if (cmd == 'R') {
        steppers[getMotor(s)].setCurrentPosition(0);
    }
    else if (cmd == 'H') {
      home();
    }
    else {
      Serial.print("Unknown command: ");
      Serial.println(s);
    }
  }
}


unsigned long print_t = millis();
void loop() {
  checkState();

  while (Serial.available()) {
    int c = Serial.read();
    if (c == '\'') {
      if (state == HIGH) {
        steppers[0].moveTo(steppers[0].currentPosition() + 1);
        output();
      } else {
        Serial.println("Can't move while endstop tripped");
      }
    }
    else if (c == ';') {
      steppers[0].moveTo(steppers[0].currentPosition() - 1);
      output();
    }
    else if (c == ']') {
      steppers[1].moveTo(steppers[1].currentPosition() + 1);
      output();
    }
    else if (c == '[') {
      steppers[1].moveTo(steppers[1].currentPosition() - 1);
      output();
    }
    else if (c == 'Z') {
      steppers[0].stop();
      steppers[1].stop();
      output();
      line = "";
    }
    else if (c == '\n' || c == '\r') {

      process(line);
      line = "";
    } else {
      line += (char) c;
    }

  }
  steppers[0].run();
  steppers[1].run();

  long t1 = millis();
  if (t1 - print_t > 1000 && (steppers[0].isRunning() || steppers[1].isRunning())) {
    output();
    print_t = t1;
  }
}

