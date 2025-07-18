//
// Created by Buer_vakabauta on 2024/11/1.
//

#ifndef CLIONSTM32DEMO_NODEBUG_H
#define CLIONSTM32DEMO_NODEBUG_H
#include "stm32f10x.h"
char uart_buffer[1]={'\0'};

void UART_Init(uint32_t baud_rate);
void UART_SendChar(char c);
void UART_SendString(const char* str);
char UART_ReceiveChar(void);
void UART_Send_num(int16_t num,uint8_t length);
void ClearBuffer(void);
void ESP_Send(const char* str);
void ESP_Connect();
void ESP_Transport_Mode_Open();
void ESP_Transport_Mode_Close();

int sprintf(char *str, const char *format, ...);
int sscanf(const char *str, const char *format, ...);

#endif //CLIONSTM32DEMO_NODEBUG_H
