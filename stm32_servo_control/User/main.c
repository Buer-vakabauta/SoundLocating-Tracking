//模板工程
//
#include <settings.h>
#include <Delay.h>
#include <Timer.h>
#include "PWM.h"
//全局变量
uint8_t flag=0;
float v_angle=190;
float h_angle=70;

// 定义宏
void main_loop(void);
void init();

//初始化
void init()
{
    Timer_Init_TIM1();
    PWM_Init(19999, 71);
#if ENABLE_UART
    UART_Init(9600);
#endif
}
int main()
{
    init();
	Servo_setAngle(190,70);
	main_loop();
}


void main_loop(void)
{
		
    while (1){

#if ENABLE_UART
        if(uart_buffer[0]=='#'){
            if(sscanf(uart_buffer,"#%f,%f",&v_angle,&h_angle)!=2) continue;
            Servo_setAngle(v_angle,h_angle);
            esp_printf("ACK");
            UART_clearBuffer();
        }
#endif
    }
}


//TIM1中断
void TIM1_UP_IRQHandler(void)
{
    if (TIM_GetITStatus(TIM1, TIM_IT_Update) == SET){
    #if ENABLE_UART
    #endif
        TIM_ClearITPendingBit(TIM1, TIM_IT_Update);
    }
}