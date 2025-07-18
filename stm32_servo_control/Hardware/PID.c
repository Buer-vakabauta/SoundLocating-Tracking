#include "PID.h"
#include "stm32f10x.h"
#include "Motor.h"
#include "stdio.h"
#include "UART.h"
#include "Delay.h"

#define MAX_PWM 1999
#define MIN_PWM -1999

extern int16_t Speedrate;
extern int8_t flag;
void PID_init(PID_structer* PID_){
    PID_->error=0;
    PID_->last_error=0;
    PID_->error_sum=0;
}

int16_t Cal_Speed(PID_structer* _PID ,int16_t Target_value,int16_t Current_value){

    _PID->last_error=_PID->error;
    _PID->error=Target_value-Current_value;
    _PID->error_sum+=_PID->error;
    if(_PID->error_sum>100) _PID->error_sum=100;
    else if(_PID->error_sum<-100) _PID->error_sum=-100;
    int16_t result=0;
    result=_PID->KP*_PID->error+(_PID->KI*_PID->error_sum)/10-_PID->KD*(_PID->error-_PID->last_error);
    //char buffer[16];
    //sprintf(buffer,"PWM:%d\n",result);
    //UART_SendString(buffer);
    if(result>=1999) return 1999;
    else if(result<=-1999) return -1999;
    return result;

}


float Angle_PID(int16_t angle){
    int8_t KP = 20,KI = 0,KD = 0;
    float output;
    float Bias,lastBias=0,sumBias,dBias;
    Bias =angle - ZHONGZHI; //误差等于理想值减去实际值
    sumBias += Bias;
    dBias = Bias - lastBias;
    output = KP*Bias + KI*sumBias + KD*dBias;
    lastBias = Bias; //更新误差
    return output;//输出PWM值
}

float Position_PID(PID_structer *_PID1,int16_t speed,int16_t aim_P){
    _PID1->last_error = _PID1->error;
    _PID1->error=aim_P-speed;
    _PID1->error_sum += _PID1->error;
    if(_PID1->error_sum>500) _PID1->error_sum=500;
    else if(_PID1->error_sum<-500) _PID1->error_sum=-500;

    float result = _PID1->error*0.2*_PID1->KP + _PID1->error_sum*_PID1->KI*0.01 + _PID1->KD*0.1*(_PID1->error-_PID1->last_error);
    if(result>=1999) return 1999;
    else if(result<=-1999) return -1999;
    return  result;
}



