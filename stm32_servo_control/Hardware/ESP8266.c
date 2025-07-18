//
// Created by Buer_vakabauta on 2024/10/27.
//
//AT+CWJAP_DEF="Buer_vakabautas","66666666"
//#define single_esp8266 //单esp使用透传模式
//#define esp_now//双esp使用esp_now协议通信
#include "UART.h"
#include "ESP8266.h"
#include "OLED.h"
#ifdef esp_now
#define BUFFER_MAX_SIZE 64
#include <stdio.h>
#include <stdarg.h>
void esp_printf(const char* format,...){
    char buffer[BUFFER_MAX_SIZE];
    va_list args;
    va_start(args, format);
    vsnprintf(buffer, BUFFER_MAX_SIZE, format, args);
    va_end(args);
    UART_SendString(buffer);
}
#endif



#ifdef single_esp8266
#include "Delay.h"


void ESP_Send(const char* str){
    UART_SendString("AT+CIPMODE=1\r\n");
    UART_SendString("AT+CIPSEND\r\n");
    UART_SendString(str);
    UART_SendString("AT+CIPMODE=0\r\n");
}

void ESP_Connect(){
    //UART_SendString("AT+RST");
    //UART_SendString("AT+CWMODE=1");
    //UART_SendString("AT+CIPMUX=0");
    UART_SendString("AT\r\n");//避免行首吞字
    Delay_ms(1000);
    UART_SendString("AT+CIPSTART=\"TCP\",\"192.168.85.21\",1347\r\n");
    Delay_ms(1000);
}


void ESP_Transport_Mode_Open(){
    UART_SendString("AT+CIPMODE=1\r\n");
    Delay_ms(1000);
    UART_SendString("AT+CIPSEND\r\n");
    Delay_ms(1000);


}

void ESP_Transport_Mode_Close(){
    UART_SendString("AT+CIPMODE=0\r\n");
}

void ESP_Reset(){
    UART_SendString("AT+RST\r\n");

}
#endif