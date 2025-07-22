//
// Created by Buer_vakabauta on 2025/7/19.
//
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include "Laser.h"
#include "PWM.h"
void parse_json_manual(char *json) {
    if (strstr(json, "\"angle\"")) {
        char *p = strstr(json, "\"angle\"");
        int angle = atoi(strchr(p, ':') + 1);
		
        //舵机控制接口实现
    }

    if (strstr(json, "\"laser\"")) {
        char *p = strstr(json, "\"laser\"");
        bool laser_on = strstr(p, "true") != NULL;
        if(laser_on){Laser_set(1);}
        else {Laser_set(0);}
    }

}
