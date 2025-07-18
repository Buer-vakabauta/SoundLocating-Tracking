#ifndef TCR__H
#define TCR__H
void TCR_Init();
uint8_t Read_TCR_Middle();  // 读取中传感器的状态
uint8_t Read_TCR_Right();   // 读取右传感器的状态
uint8_t Read_TCR_Left();    // 读取左传感器的状态
int8_t readsensor(); //读取传感器的状态
#endif
