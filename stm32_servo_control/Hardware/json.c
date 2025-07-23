//
// Created by Buer_vakabauta on 2025/7/19.
//
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include "Laser.h"
#include "PWM.h"
#include "OLED.h"
#include "UART.H"
void parse_json_manual(char *json) {

	    float angle=0;
		uint8_t laser_on=0;
		sscanf(uart_buffer,"(%f,%d)",&angle,&laser_on);
		if(angle>=-60&&angle<=60){
		Servo_setAngle(70-angle,70-angle);
		}
        //舵机控制接口实现
        if(laser_on==1){Laser_set(1);}
        else {Laser_set(0);}
    
}
