//模板工程
//
#include <settings.h>
#include <Delay.h>
#include <Timer.h>
#include "PWM.h"
#include "Laser.h"
#include "OLED.h"
#define APP_VECTOR_ADDR 0x08004000
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
	OLED_Init();
    Laser_Init();
    Timer_Init_TIM1();
    PWM_Init(19999, 71);
    UART_Init(115200);
}
int main()
{	SCB->VTOR = APP_VECTOR_ADDR;
    init();
	Laser_set(0);
	Servo_setAngle(70,70);//70 190
	main_loop();
}


void main_loop(void)
{
		
    while (1){
		
		OLED_ShowString(1,1,"Tracking      ");
		Delay_ms(500);
		OLED_ShowString(1,1,"Tracking.");
		Delay_ms(500);
		OLED_ShowString(1,1,"Tracking..");
		Delay_ms(500);
		OLED_ShowString(1,1,"Tracking...");
		Delay_ms(500);
    }
}


//TIM1中断
void TIM1_UP_IRQHandler(void)
{
    if (TIM_GetITStatus(TIM1, TIM_IT_Update) == SET){
        TIM_ClearITPendingBit(TIM1, TIM_IT_Update);
    }
}