//
// Created by Buer_vakabauta on 2024/10/27.
//

#ifndef CLIONSTM32DEMO_ESP8266_H
#define CLIONSTM32DEMO_ESP8266_H
//#define single_esp8266 //单esp使用透传模式
#define esp_now//双esp使用esp_now协议通信
#ifdef esp_now
void esp_printf(const char* format,...);
#endif
#ifdef single_esp8266
#include "stm32f10x.h"
void ESP_Send(const char* str);
void ESP_Connect();
void ESP_Transport_Mode_Open();
void ESP_Transport_Mode_Close();
#endif

#endif //CLIONSTM32DEMO_ESP8266_H
