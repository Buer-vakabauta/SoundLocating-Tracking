#ifndef _MADGWICK_AHRS_H_
#define _MADGWICK_AHRS_H_

void MadgwickAHRSupdateIMU(float gx, float gy, float gz, float ax, float ay, float az);
void MadgwickAHRSinit(float sampleFreq, float beta);

float GetRoll(void);
float GetPitch(void);
float GetYaw(void);

#endif