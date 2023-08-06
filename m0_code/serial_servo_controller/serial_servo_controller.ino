#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

#define NR_PWM_DRIVERS 3
// pwm drivers
Adafruit_PWMServoDriver pwm[] = {
  Adafruit_PWMServoDriver(0x40),
  Adafruit_PWMServoDriver(0x60),
  Adafruit_PWMServoDriver(0x41)
};

#define SERVO_NEUTRAL 600  // This is the initial 'neutral' pulse length count (out of 4096)
#define SERVO_FREQ 100     // Analog servos run at ~50 Hz updates

// target servo #
uint8_t servonum = 3;

void setup() {
  Serial.begin(115200);
  Serial.println("Starting serial servo controller...");

  for (int n = 0; n < NR_PWM_DRIVERS; n++) {
    pwm[n].begin();
    pwm[n].setOscillatorFrequency(25000000);
    pwm[n].setPWMFreq(SERVO_FREQ);

    delay(10);
  }
}

bool parseTokens(int token_array[], int size) {
  for (int i = 0; i < size; i++) {
    char *chptr = strtok(NULL, " ");
    if (chptr == NULL) {
      return false;
    }
    token_array[i] = atoi(chptr);
  }
  return true;
}

void loop() {

  while (Serial.available() > 0) {
    String line = Serial.readStringUntil('\r');
    int line_length = line.length() + 1;
    char buf[line_length];
    line.toCharArray(buf, line_length);

    // parse command
    char *chptr = strtok(buf, " ");
    int opcode = atoi(chptr);
    switch (opcode) {

      // 0x0FF - Reset all pwm channels
      case 0xFF:
        {
          Serial.println("[0xFF] Reset");
          for (int n = 0; n < NR_PWM_DRIVERS; n++) {
            for (int i = 0; i < 8; i++) {
              pwm[n].setPWM(i, 0, 0);
              delay(10);
            }
          }
          break;
        }

      // 0x00 - Set oscillator frequency: {board, frequency}
      case 0x00:
        {
          int tokens = 2;
          int comarray[tokens];
          int board, freq = 0;
          if (parseTokens(comarray, tokens)) {
            board = comarray[0];
            freq = comarray[1];
            Serial.print("[0x00] board=");
            Serial.print(board, DEC);
            Serial.print(", freq=");
            Serial.print(freq, DEC);
            Serial.println();

            // set pulse
            if (board < NR_PWM_DRIVERS) {
              //pwm[board].begin();
              pwm[board].reset();
              pwm[board].begin();
              pwm[board].setOscillatorFrequency(freq);
              pwm[board].setPWMFreq(SERVO_FREQ);
            }

          } else {
            Serial.println("Error in opcode (0x00)");
          }
          break;
        }

      // 0x01 - Set servo pwm and release: {board, servo, pulse}
      case 0x01:
        {
          int tokens = 3;
          int comarray[tokens];
          int board, servo, pulse = 0;
          if (parseTokens(comarray, tokens)) {
            board = comarray[0];
            servo = comarray[1];
            pulse = comarray[2];
            Serial.print("[0x01] board=");
            Serial.print(board, DEC);
            Serial.print(", servo=");
            Serial.print(servo, DEC);
            Serial.print(", pulse=");
            Serial.print(pulse, DEC);
            Serial.println();

            // set pulse
            if (board < NR_PWM_DRIVERS) {
              pwm[board].setPWM(servo, 0, pulse);
              delay(100);
              pwm[board].setPWM(servo, 0, 0);
            }

          } else {
            Serial.println("Error in opcode (0x01)");
          }
          break;
        }

      // 0x02 - Set servo pwm and keep position: {board, servo, pulse}
      case 0x02:
        {
          int tokens = 3;
          int comarray[tokens];
          int board, servo, pulse = 0;
          if (parseTokens(comarray, tokens)) {
            board = comarray[0];
            servo = comarray[1];
            pulse = comarray[2];
            Serial.print("[0x02] board=");
            Serial.print(board, DEC);
            Serial.print(", servo=");
            Serial.print(servo, DEC);
            Serial.print(", pulse=");
            Serial.print(pulse, DEC);
            //Serial.print(", freq=");
            //int freq = pwm[board].getOscillatorFrequency();
            //Serial.print(freq, DEC);
            Serial.println();

            // set pulse
            if (board < NR_PWM_DRIVERS) {
              pwm[board].setPWM(servo, 0, pulse);
              delay(100);
            }

          } else {
            Serial.println("Error in opcode (0x01)");
          }
          break;
        }

      default:
        Serial.println("Unknown opcode");
        break;
    }
  }
}
