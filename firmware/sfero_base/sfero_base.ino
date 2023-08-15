#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

#define NR_LEGS 6
#define NR_JOINTS_PER_LEG 3

#define NR_PWM_DRIVERS 3
#define NR_PWM_CHANNELS 8
// pwm drivers
Adafruit_PWMServoDriver pwm[] = {
  Adafruit_PWMServoDriver(0x40),
  Adafruit_PWMServoDriver(0x60),
  Adafruit_PWMServoDriver(0x41)
};
// calibrated oscillator frequencies
int pwm_osc_frequency[] = {
  24400000,
  26800000,
  26500000
};

#define SERVO_FREQ 100

// servo id: {board id, channel}
struct ServoId {
  int board_id_;
  int channel_;
  ServoId(int _board_id, int _channel)
    : board_id_(_board_id), channel_(_channel) {}
};
// leg with three joints: {upper, mid, lower}
struct Leg {
  ServoId upper_;
  ServoId mid_;
  ServoId lower_;
  Leg(ServoId _upper, ServoId _mid, ServoId _lower)
    : upper_(_upper), mid_(_mid), lower_(_lower) {}
};
// map that stores which servos are connected to which leg
Leg legs[NR_LEGS] = {
  Leg(ServoId(0, 4), ServoId(0, 5), ServoId(0, 6)),  // leg 0
  Leg(ServoId(1, 4), ServoId(1, 5), ServoId(1, 6)),  // leg 1
  Leg(ServoId(2, 4), ServoId(2, 5), ServoId(2, 6)),  // leg 2
  Leg(ServoId(2, 3), ServoId(2, 2), ServoId(2, 1)),  // leg 3
  Leg(ServoId(1, 3), ServoId(1, 2), ServoId(1, 1)),  // leg 4
  Leg(ServoId(0, 3), ServoId(0, 2), ServoId(0, 1))   // leg 5
};

// servo calibration data: {coefficients, input limits} - Todo: add other data such as freq and check during setup
struct ServoCalibData {
  float p_[2];
  int range_[2];
};
// calibration data array, can be directly accessed with (board_id, channel) tuple
ServoCalibData servo_calib[NR_PWM_DRIVERS][NR_PWM_CHANNELS] = {
  {
    // board 0
    { { 0, 0 }, { 0, 0 } },                                          // channel 0
    { { 0.22038958388737884, -133.12952792656432 }, { 240, 730 } },  // channel 1: servo_002
    { { 0, 0 }, { 0, 0 } },                                          // channel 2
    { { 0.23449376803585678, -138.55650518818686 }, { 203, 979 } },  // channel 3: servo_007
    { { 0.21992095465228753, -128.46132763626753 }, { 170, 990 } },  // channel 4: servo_000
    { { 0, 0 }, { 0, 0 } },                                          // channel 5
    { { 0.2303063107632615, -133.1347936897926 }, { 450, 920 } },    // channel 6: servo_001
    { { 0, 0 }, { 0, 0 } },                                          // channel 7
  },
  {
    // board 1
    { { 0, 0 }, { 0, 0 } },                                           // channel 0
    { { 0.22681920393793628, -130.74061375922105 }, { 450, 920 } },   // channel 1: servo_003
    { { 0, 0 }, { 0, 0 } },                                           // channel 2
    { { 0.22193106819848468, -141.25912490833542 }, { 231, 1050 } },  // channel 3: servo_008
    { { 0.22425182147501013, -139.77896347314223 }, { 228, 1033 } },  // channel 4: servo_009
    { { 0, 0 }, { 0, 0 } },                                           // channel 5
    { { 0.21839724669355384, -127.53966890476079 }, { 227, 727 } },   // channel 6: servo_005
    { { 0, 0 }, { 0, 0 } },                                           // channel 7
  },
  {
    // board 2
    { { 0, 0 }, { 0, 0 } },                                          // channel 0
    { { 0.21647982117824974, -128.12972126000102 }, { 241, 735 } },  // channel 1: servo_004
    { { 0, 0 }, { 0, 0 } },                                          // channel 2
    { { 0.23258186926909744, -142.3982494600049 }, { 227, 1013 } },  // channel 3: servo_010
    { { 0.22418884578124926, -134.0789415800484 }, { 184, 989 } },   // channel 4: servo_011
    { { 0, 0 }, { 0, 0 } },                                          // channel 5
    { { 0.2276297794523975, -133.7713253536511 }, { 453, 924 } },    // channel 6: servo_006
    { { 0, 0 }, { 0, 0 } },                                          // channel 7
  },
};

int angleToPulse(float angle_deg, ServoId servo) {
  ServoCalibData &calib_data = servo_calib[servo.board_id_][servo.channel_];
  return int((angle_deg - calib_data.p_[1]) / calib_data.p_[0]);
}

bool setPWM(ServoId servo, int pulse) {
  ServoCalibData &calib_data = servo_calib[servo.board_id_][servo.channel_];
  pulse = (pulse < calib_data.range_[0]) ? calib_data.range_[0] : pulse;
  pulse = (pulse > calib_data.range_[1]) ? calib_data.range_[1] : pulse;
  pwm[servo.board_id_].setPWM(servo.channel_, 0, pulse);

  Serial.print("\tSetting servo (");
  Serial.print(servo.board_id_);
  Serial.print(".");
  Serial.print(servo.channel_);
  Serial.print(") pulse to ");
  Serial.println(pulse);
  return true;
}

void setup() {
  Serial.begin(115200);
  Serial.println("Starting sfero base...");

  for (int n = 0; n < NR_PWM_DRIVERS; n++) {
    pwm[n].begin();
    pwm[n].setOscillatorFrequency(pwm_osc_frequency[n]);
    pwm[n].setPWMFreq(SERVO_FREQ);
    delay(10);
  }
}

void loop() {

  delay(5000);

  // move legs
  for (int i = 0; i < NR_LEGS; i++) {
    Serial.print("Moving leg[");
    Serial.print(i);
    Serial.println("]");

    // move upper joint to neutral position
    int pulse = angleToPulse(0, legs[i].upper_);
    setPWM(legs[i].upper_, pulse);

    // move mid joint to neutral position
    pulse = angleToPulse(0, legs[i].mid_);
    setPWM(legs[i].mid_, pulse);

    // move lower joint to neutral position
    pulse = angleToPulse(0, legs[i].lower_);
    setPWM(legs[i].lower_, pulse);
  }

  while (1) {
    delay(100);
  }
}
