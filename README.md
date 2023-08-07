# sferobot
A robot that can walk and roll and is trained with RL

## Calibration

### Oscillator
The internal oscillator of the PCA9865 chip on the Servo FeatherWing varies from board to board. Therefore the precise frequency needs to be measured and taken into account for generating accurate PWM control signals. To measure the oscillaotr frequency, the ```calibration_gui``` can be used. This GUI requires the ```serial_servo_controller``` firmware to be loaded.

![Calibration GUI](/doc/img/osc_calib_gui.png "Optional title")