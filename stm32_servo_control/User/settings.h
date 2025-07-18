#ifndef __Settings_H
#define __Settings_H
//启动项

#define ENABLE_UART 1
#define MPU6050_MODE 0//1:使用Madgwick算法,0:使用陀螺仪积分
//

//---------------------调试
#if ENABLE_UART
#include <ESP8266.h>
#include <UART.h>
#include "string.h"
#include "stdio.h"
#endif

//----------------------调试


#endif

