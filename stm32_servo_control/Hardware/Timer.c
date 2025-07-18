//
// Created by Buer_vakabauta on 2024/10/27.
//
#include "stm32f10x.h"
//#include "Encoder.h"
//#include "UART.h"


void Timer_Init_TIM4() {
    //开启时钟
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM4, ENABLE);
    //选择TIM2为内部时钟，若不调用此函数，TIM默认也为内部时钟
    TIM_InternalClockConfig(TIM4);

    /*时基单元初始化*/
    TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure;				//定义结构体变量
    TIM_TimeBaseInitStructure.TIM_ClockDivision = TIM_CKD_DIV1;		//时钟分频，选择不分频，此参数用于配置滤波器时钟，不影响时基单元功能
    TIM_TimeBaseInitStructure.TIM_CounterMode = TIM_CounterMode_Up;	//计数器模式，选择向上计数
    TIM_TimeBaseInitStructure.TIM_Period = 50000 - 1;				//计数周期，即ARR的值
    TIM_TimeBaseInitStructure.TIM_Prescaler = 72 - 1;				//预分频器，即PSC的值
    TIM_TimeBaseInitStructure.TIM_RepetitionCounter = 0;			//重复计数器，高级定时器才会用到
    TIM_TimeBaseInit(TIM4, &TIM_TimeBaseInitStructure);				//将结构体变量交给TIM_TimeBaseInit，配置TIM2的时基单元
    /*中断输出配置*/
    TIM_ClearFlag(TIM4, TIM_FLAG_Update);						//清除定时器更新标志位
    //TIM_TimeBaseInit函数末尾，手动产生了更新事件
    //若不清除此标志位，则开启中断后，会立刻进入一次中断
    //如果不介意此问题，则不清除此标志位也可

    TIM_ITConfig(TIM4, TIM_IT_Update, ENABLE);					//开启TIM4的更新中断

    /*NVIC中断分组*/
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);				//配置NVIC为分组2
    //即抢占优先级范围：0~3，响应优先级范围：0~3
    //此分组配置在整个工程中仅需调用一次
    //若有多个中断，可以把此代码放在main函数内，while循环之前
    //若调用多次配置分组的代码，则后执行的配置会覆盖先执行的配置

    /*NVIC配置*/
    NVIC_InitTypeDef NVIC_InitStructure;						//定义结构体变量
    NVIC_InitStructure.NVIC_IRQChannel = TIM4_IRQn;				//选择配置NVIC的TIM2线
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;				//指定NVIC线路使能
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 0;	//指定NVIC线路的抢占优先级为2
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;			//指定NVIC线路的响应优先级为1
    NVIC_Init(&NVIC_InitStructure);								//将结构体变量交给NVIC_Init，配置NVIC外设

    /*TIM使能*/
    TIM_Cmd(TIM4, ENABLE);			//使能TIM4，定时器开始运行
}

void Timer_Init_TIM1() {
    TIM_TimeBaseInitTypeDef  TIM_TimeBaseStructure;
    NVIC_InitTypeDef NVIC_InitStructure;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM1, ENABLE); //时钟使能

    TIM_TimeBaseStructure.TIM_Period = 50000-1; //设置自动重装载寄存器周期值
    TIM_TimeBaseStructure.TIM_Prescaler =72-1;//设置预分频值
    TIM_TimeBaseStructure.TIM_ClockDivision = 0; //设置时钟分割
    TIM_TimeBaseStructure.TIM_CounterMode = TIM_CounterMode_Up;//向上计数模式
    TIM_TimeBaseStructure.TIM_RepetitionCounter = 0;//重复计数设置
    TIM_TimeBaseInit(TIM1, &TIM_TimeBaseStructure); //参数初始化
    TIM_ClearFlag(TIM1, TIM_FLAG_Update);//清中断标志位

    TIM_ITConfig(      //使能或者失能指定的TIM中断
            TIM1,            //TIM1
            TIM_IT_Update  | //TIM 更新中断源
            TIM_IT_Trigger,  //TIM 触发中断源
            ENABLE  	     //使能
    );

    //设置优先级
    NVIC_InitStructure.NVIC_IRQChannel = TIM1_UP_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 0;//先占优先级0级
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 0;  	   //从优先级0级
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);

    TIM_Cmd(TIM1, ENABLE);  //使能TIMx外设

}

// 定时器中断函数，可以复制到使用它的地方



/*
void TIM4_IRQHandler(void)
{

	if (TIM_GetITStatus(TIM4, TIM_IT_Update) == SET){
        Speedrate=Encoder_Get();

		TIM_ClearITPendingBit(TIM4, TIM_IT_Update);
	}
}

*/