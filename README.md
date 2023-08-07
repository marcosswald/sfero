# sferobot
A robot that can walk and roll and is trained with RL

## Calibration

### Oscillator
The internal oscillator of the PCA9865 chip on the Servo FeatherWing varies from board to board. Therefore the precise frequency needs to be measured and taken into account for generating accurate PWM control signals. To measure the oscillaotr frequency, the ```calibration_gui``` can be used. This GUI requires the ```serial_servo_controller``` firmware to be loaded. Furthermore an oscilloscope is needed to measure a dependent metric such as the PWM frequency for example.

1. Load the ```serial_servo_controller``` firmware
2. Run ```calibration_gui.py```
3. Select the COM port and start the serial communication
4. Connect the probe to one of the PWM outputs and set the according channel and board in the GUI
5. Enter a pulse value and hit enter, you should see the PWM signal on the scope
6. Add a measurement for the PWM frequency on the scope. This corresponds to the servo frequency (Hz) and should be close to 100Hz.
7. Change the frequency value in the GUI and observe the measured servo frequency on the scope
8. Calibration data points can be added by hitting the enter key on the frequency edit field
9. Hit 'Calibrate' to run get a linear fit on the data points
10. Get an estimate of the real oscillator frequency 'X' by entering the servo frequency (100Hz) into the 'Y' field and hitting enter.

![Calibration GUI](/doc/img/osc_calib_gui.png)
![Oscillator calibration plot](/doc/img/osc_calib_plot.png)