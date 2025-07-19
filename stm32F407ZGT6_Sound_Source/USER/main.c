//引用库
#include "stm32f4xx.h"
#include "OLED.h"
#include "DAC_sound.h"
//全局变量
#define WAVE_TABLE_SIZE 256
uint16_t sine_wave[WAVE_TABLE_SIZE];
//定义宏
void main_loop(void);
void main_init(void);
//初始化
void main_init(void){
	//MX_USB_DEVICE_Init();
	SystemInit();
	OLED_Init();
    DAC_Init_Sound();
}
//主函数
int main(void)
{
	main_init();
	main_loop();
}
void main_loop(void) {
	 GenerateSineWave(sine_wave, WAVE_TABLE_SIZE, 1000);
    while (1) {
     
    }
}
