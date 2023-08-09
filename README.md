# sferobot
A robot that can walk and roll and is trained with RL

## Calibration

### Oscillator
The internal oscillator of the PCA9865 chip on the Servo FeatherWing varies from board to board. Therefore the precise frequency needs to be measured and taken into account for generating accurate PWM control signals. To measure the oscillator frequency, the ```calibration_gui``` can be used. This GUI requires the ```serial_servo_controller``` firmware to be loaded. Furthermore an oscilloscope is needed to measure a dependent metric such as the PWM frequency for example.

1. Load the ```serial_servo_controller``` firmware
2. Run ```calibration_gui.py```
3. Select the COM port and start the serial communication
4. Connect a probe to one of the PWM outputs and set the corresponding channel and board in the GUI
5. Enter a pulse value and hit enter, you should see the PWM signal on the scope
6. Add a measurement for the PWM frequency on the scope. This corresponds to the servo frequency (Hz) and should be close to 100Hz.
7. Change the frequency value in the GUI and observe the measured servo frequency on the scope
8. Calibration data points can be added by hitting the enter key on the frequency edit field
9. Hit 'Calibrate' to run get a linear fit on the data points
10. Get an estimate of the real oscillator frequency 'X' by entering the servo frequency (100Hz) into the 'Y' field and hitting enter.

![Calibration GUI](/doc/img/osc_calib_gui.png)
![Oscillator calibration plot](/doc/img/osc_calib_plot.png)

### Servo
Servos positions are controlled proportionally to the input pulse width where a duration of ~1.5ms usually depicts the neutral position. However, gain aand offset vary in each servo and therefore need to be calibrated. We use a 3d printed calibration tool with known angular positions and measure the pulse durations that move the servo to the according positions. A linear regression is then applied to the data points which yields the gain and offset. The procedure is similar to the oscillator calibration but we don't need the oscilloscope. Instead we manually change the servo position (by using up and down arrow keys on the pulse edit field) until it matches with one of the known angular positions of the calibration target.

![Servo calibration](/doc/img/servo_calib_img.jpg)
Calibration measurements should be taken over the entire range of the servos operaiton. In the image above, the joint collides with the calibration target for positions on the lower circle. In that case, a separate calibration target (mirrored version) can be used to acquire the missing measurements. This may introduce an additional error since there might be a small angular offset between the targets. It is currently assumed that this error is not significant.

![Calibration GUI](/doc/img/osc_calib_gui.png)
![Servo calibration plot](/doc/img/servo_calib_plot.png)

With an RSE~=1.7° the linear fit suggests that the model is good for the example shown above (RSS=40, n=16, RSE=sqrt(RSS/n-2)~=1.7). There is noticable backlash from the gears which probably is responsible for the largest part of the error. To get the best model, each data point should be measured twice by approaching it from both directions (CW and CCW).