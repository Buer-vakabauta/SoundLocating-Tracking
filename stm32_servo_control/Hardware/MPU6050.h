#ifndef __MPU6050_H
#define __MPU6050_H
#include "stm32f10x.h"
#include "settings.h"

void MPU6050_WriteReg(uint8_t RegAddress, uint8_t Data);
uint8_t MPU6050_ReadReg(uint8_t RegAddress);

void MPU6050_Init(void);
uint8_t MPU6050_GetID(void);
void MPU6050_GetData(int16_t *AccX, int16_t *AccY, int16_t *AccZ, 
						int16_t *GyroX, int16_t *GyroY, int16_t *GyroZ);
#if MPU6050_MODE==0
void update_yaw(float gyro_z);
void Cal_Zero_offset();
#endif
#if MPU6050_MODE==1
void IMU_Init(void);
void IMU_Update(void);
float Get_Yaw_Angle(void);

#endif



#endif
