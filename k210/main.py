from board import board_info  # 获取开发板信息
from fpioa_manager import fm
from maix import GPIO,I2S
from maix import mic_array as mic
import time,image, lcd, gc, math
from machine import UART, SPI
import struct
import json
import math
import touchscreen as ts

# 全局变量------------------------------------

# 系统状态
system_state = {
    'locating': False,#定位模式
    'tracking': False,#追踪模式
    'laser_on': False,#激光状态
    'distance': 0.0,#距离
    'angle': 0.0,#角度
    'target_x': 0.0,#目标位置X
    'target_y': 0.0,#目标位置y
    'display':False #显示声强图
}

# 错误状态管理
error_state = {
    'last_error': '',           # 最后一个错误信息
    'error_time': 0,            # 错误发生时间
    'error_count': 0,           # 错误计数
    'show_error': False,        # 是否显示错误
    'error_timeout': 5000       # 错误显示超时时间(ms)
}

# 触摸屏参数
touch_config = {
    'width': 320,
    'height': 240,
    'status_last': ts.STATUS_IDLE,
    'x_last': 0,
    'y_last': 0
}

# 声源定位参数
localization_params = {
    'sound_speed': 343.0,  # 声速 m/s
    'max_distance': 5.0,   # 最大检测距离 m
    'min_distance': 0.5,   # 最小检测距离 m
    'angle_range': 180,    # 角度范围 度
    'update_interval': 0.1 # 更新间隔 s
}
flag=0
last_press_time = 0
last_location_time = 0
audio_buffer = []
#------------------------------------------

# 错误处理函数------------------------------------
def log_error(error_msg, exception=None):
    """记录和显示错误信息"""
    global error_state

    current_time = time.ticks_ms()
    error_state['error_count'] += 1

    if exception:
        full_error = "["+str(error_state['error_count'])+"]"+str(error_msg)+":" +str(exception)
    else:
        full_error = "["+str(error_state['error_count'])+"]"+ str(error_msg)

    error_state['last_error'] = full_error
    error_state['error_time'] = current_time
    error_state['show_error'] = True

    # 打印详细错误信息
    print("=" * 50)
    print("ERROR OCCURRED:")
    print("Time:", current_time)
    print("Count:", error_state['error_count'])
    print("Message:", full_error)
    if exception:
        print("Exception Type:", type(exception).__name__)
    print("=" * 50)

def clear_error_if_timeout():
    """如果错误超时则清除错误显示"""
    global error_state
    current_time = time.ticks_ms()

    if error_state['show_error'] and (current_time - error_state['error_time'] > error_state['error_timeout']):
        error_state['show_error'] = False
        print("错误信息已清除")

def clear_error_manual():
    """手动清除错误显示"""
    global error_state
    error_state['show_error'] = False
    print("错误信息手动清除")

#------------------------------------------

# 引脚配置------------------------------------
try:
    # 麦克风阵列引脚
    #fm.register(43, fm.fpioa.I2S0_WS)        # MIC_WS#21
    #fm.register(11, fm.fpioa.I2S0_SCLK)      # MIC_CK#22
    #fm.register(44, fm.fpioa.I2S0_OUT_D0)    # MIC_D0#23
    #fm.register(46, fm.fpioa.I2S0_OUT_D1)    # MIC_D1#24
    #fm.register(45, fm.fpioa.I2S0_OUT_D2)    # MIC_D2#25
    #fm.register(47, fm.fpioa.I2S0_OUT_D3)    # MIC_D3#26
    print("初始化麦克风阵列...")
    mic.init(i2s_d0=44, i2s_d1=46, i2s_d2=45, i2s_d3=47, i2s_ws=43, i2s_sclk=11, sk9822_dat=39,  sk9822_clk=40)
    print("麦克风阵列初始化成功")
except Exception as e:
    log_error("麦克风阵列初始化失败", e)

try:
    # 串口通信
    print("初始化串口通信...")
    fm.register(1, fm.fpioa.UART1_TX)#10
    fm.register(0, fm.fpioa.UART1_RX)#8
    print("串口引脚配置成功")
except Exception as e:
    log_error("串口引脚配置失败", e)

try:
    # 按键
    print("初始化按键...")
    fm.register(board_info.BOOT_KEY, fm.fpioa.GPIOHS0, force=True)
    print("按键配置成功")
except Exception as e:
    log_error("按键配置失败", e)

#------------------------------------------
# 初始化-------------------------------------
try:
    # 构造UART对象
    print("创建UART对象...")
    uart1 = UART(UART.UART1, 115200)
    print("UART对象创建成功")
except Exception as e:
    log_error("UART对象创建失败", e)
    uart1 = None

try:
    # 屏幕初始化
    print("初始化屏幕...")
    lcd.init()
    ts.init()
    lcd.clear()
    print("屏幕初始化成功")
except Exception as e:
    log_error("屏幕初始化失败", e)

try:
    # 按键中断初始化
    print("初始化按键中断...")
    boot_key = GPIO(GPIO.GPIOHS0, GPIO.IN, GPIO.PULL_UP)
    print("按键中断初始化成功")
except Exception as e:
    log_error("按键中断初始化失败", e)
    boot_key = None

try:
    # 显示图像对象
    print("创建显示图像对象...")
    display_img = image.Image()
    print("显示图像对象创建成功")
except Exception as e:
    log_error("显示图像对象创建失败", e)

#类定义--------------------------------------
class MicDirectionProcessor:
    """
    MicDirectionProcessor 类用于处理麦克风阵列的方向数据，
    包括：方向角估计、低通滤波、卡尔曼滤波平滑和距离估算。

    参数:
        kalman_q (float): 卡尔曼滤波器过程噪声协方差 Q
        kalman_r (float): 卡尔曼滤波器观测噪声协方差 R
        lb_level (int): 低通滤波器的缓存长度
        use_kalman (bool): 是否启用卡尔曼滤波
    """

    def __init__(self, kalman_q=0.0, kalman_r=0.01, lb_level=3, use_kalman=True):
        try:
            # 卡尔曼滤波器变量
            self.kalman_prev_cov = 0.1       # 上一时刻协方差 P(k-1)
            self.kalman_curr_cov = 0         # 当前时刻协方差 P(k)
            self.kalman_state = 0            # 当前估计值 x(k)
            self.kalman_gain = 0             # 卡尔曼增益 K(k)
            self.kalman_Q = kalman_q         # 过程噪声 Q
            self.kalman_R = kalman_r         # 观测噪声 R
            self.use_kalman = use_kalman     # 是否启用卡尔曼滤波

            # 低通滤波器变量
            self.lp_buffer = [0] * lb_level  # 存储最近的角度值
            self.lp_index = 0                # 当前写入下标
            self.lp_max_index = 0            # 当前最大值下标
            self.lp_min_index = 0            # 当前最小值下标
            self.lp_level = lb_level         # 滤波窗口长度

            self.last_angle = 0              # 上一帧计算出的方向角
            print("MicDirectionProcessor初始化成功")
        except Exception as e:
            log_error("MicDirectionProcessor初始化失败", e)

    def kalman_filter(self, value):
        """
        卡尔曼滤波器：用于平滑输入值

        参数:
            value (float): 当前观测值
        返回:
            float: 滤波后的估计值
        """
        try:
            self.kalman_curr_cov = self.kalman_prev_cov + self.kalman_Q
            self.kalman_gain = self.kalman_curr_cov / (self.kalman_curr_cov + self.kalman_R)
            output = self.kalman_state + self.kalman_gain * (value - self.kalman_state)
            self.kalman_state = output
            self.kalman_prev_cov = (1 - self.kalman_gain) * self.kalman_curr_cov
            return output
        except Exception as e:
            log_error("卡尔曼滤波器处理失败", e)
            return value

    def low_pass_filter(self, value):
        """
        简单低通滤波器：滤除最大最小值后取平均值

        参数:
            value (float): 当前输入角度
        返回:
            float | None: 平滑后的角度，如果未满窗口则返回 None
        """
        try:
            self.lp_buffer[self.lp_index] = value

            if value > self.lp_buffer[self.lp_max_index]:
                self.lp_max_index = self.lp_index
            if value < self.lp_buffer[self.lp_min_index]:
                self.lp_min_index = self.lp_index

            if self.lp_index == self.lp_level-1:
                # 丢弃最大和最小值再求平均
                self.lp_buffer[self.lp_max_index] = 0
                self.lp_buffer[self.lp_min_index] = 0
                avg = sum(self.lp_buffer) / (self.lp_level - 2)

                # 重置索引
                self.lp_index = 0
                self.lp_max_index = 0
                self.lp_min_index = 0
                return avg
            else:
                self.lp_index += 1
                return None
        except Exception as e:
            log_error("低通滤波器处理失败", e)
            return None

    def process_direction(self, imga,levels):
        """
        从麦克风阵列获取方向角并进行平滑处理，输出角度与估算距离。

        参数:
            imga: 麦克风声强图(mic.get_map获取)，
            levels:每个方向的声源强度值（12 个方向）(mic.get_dir(imga)获取)
        返回:
            dict | None: {'angle': 平滑方向角, 'distance': 估算距离}，若无方向信息则返回 None
        """
        try:
            if imga is None:
                return None,None

            angle_x = 0
            angle_y = 0

            if levels is None or len(levels) == 0:
                return None, None

            for i in range(len(levels)):
                if levels[i] >= 0:
                    angle_x += levels[i] * math.sin(i * math.pi / 6)   # 水平方向加权
                    angle_y += levels[i] * math.cos(i * math.pi / 6)   # 垂直方向加权

            if angle_x == 0 and angle_y == 0:
                return None,None  # 无声源方向

            # 计算角度（处理象限）
            angle = math.degrees(math.atan2(angle_x,angle_y))
            if -60<=angle<=60:
                angle = self.last_angle * 0.1 + angle * 0.9  # 快速响应但带记忆
                filtered = self.low_pass_filter(angle)
                if filtered is not None:
                    filtered = max(min(filtered, 90), -90)  # 限制角度范围
                    if self.use_kalman:
                        filtered = self.kalman_filter(filtered)
                    self.last_angle = filtered
                    # 简易距离估计（经验公式）
                    distance = 275 / math.cos(filtered * math.pi / 180)
                    return round(filtered, 2),round(distance, 2)##保留两位小数

            return None,None
        except Exception as e:
            log_error("方向处理失败", e)
            return None, None

# 函数定义------------------------------------

def boot_key_irq(key):
    """按键中断处理"""
    global last_press_time, system_state
    try:
        current_time = time.ticks_ms()
        if current_time - last_press_time > 200:  # 防抖动
            if key.value()==0:
#                print("按键按下")
                if system_state['display']:
                    system_state['display']=False
                else:
                    system_state['display']=True
                clear_error_manual()  # 清除错误显示
            last_press_time = current_time
        """
            if key.value() == 0:  # 按下
                system_state['locating'] = not system_state['locating']
                if system_state['locating']:
                    print("开始声源定位")
                    clear_error_manual()  # 清除错误显示
                else:
                    print("停止声源定位")
                    system_state['laser_on'] = False
                    send_laser_control(False)
            last_press_time = current_time
         """
    except Exception as e:
        log_error("按键中断处理失败", e)


def handle_touch_event(x, y):
    """处理触摸事件"""
    global system_state

    try:
        # 定义触摸区域
        if y < 60:  # 顶部控制区域
            if x < 80:  # 定位按钮
                system_state['locating'] = not system_state['locating']
                clear_error_manual()  # 清除错误显示
            elif x < 160:  # 跟踪按钮
                system_state['tracking'] = not system_state['tracking']
            elif x < 240:  # 激光按钮
                system_state['laser_on'] = not system_state['laser_on']
                send_laser_control(system_state['laser_on'])
            else:  # 重置按钮
                reset_system()
        elif y > 200:  # 底部错误区域，点击清除错误
            clear_error_manual()
    except Exception as e:
        log_error("触摸事件处理失败", e)

def reset_system():
    """重置系统"""
    global system_state
    try:
        system_state['locating'] = False
        system_state['tracking'] = False
        system_state['laser_on'] = False
        system_state['distance'] = 0.0
        system_state['angle'] = 0.0
        send_laser_control(False)
        clear_error_manual()  # 清除错误显示
        print("系统已重置")
    except Exception as e:
        log_error("系统重置失败", e)


def send_uart_data(distance, angle, laser_on=False):
    """发送数据到STM32"""
    global uart1
    laser=0
    try:
        if uart1 is None:
            log_error("UART对象未初始化")
            return
        if laser_on:
            laser=1
        else:
            laser=0
        json_str = '('+str(angle)+','+str(laser)+')' + '\n'
        uart1.write(json_str.encode())

    except Exception as e:
        log_error("UART数据发送失败", e)
def send_laser_control(state):
    send_uart_data(0,-180,state)
def draw_interface():
    """绘制用户界面"""
    global system_state, display_img, error_state
    try:
        # 清除图像
        display_img.clear()
        # 绘制标题
        display_img.draw_string(10, 10, "Sound Source Localization&Tracking", color=(255, 255, 255), scale=1)

        # 绘制控制按钮
        button_y = 40
        button_width = 70
        button_height = 30

        # 定位按钮
        color = (0, 255, 0) if system_state['locating'] else (255, 0, 0)
        display_img.draw_rectangle(10, button_y, button_width, button_height, color=color, fill=True)
        display_img.draw_string(15, button_y + 10, "Locate", color=(255, 255, 255), scale=1)

        # 跟踪按钮
        color = (0, 255, 0) if system_state['tracking'] else (255, 0, 0)
        display_img.draw_rectangle(90, button_y, button_width, button_height, color=color, fill=True)
        display_img.draw_string(95, button_y + 10, "Track", color=(255, 255, 255), scale=1)

        # 激光按钮
        color = (0, 255, 0) if system_state['laser_on'] or system_state['tracking'] else (255, 0, 0)
        display_img.draw_rectangle(170, button_y, button_width, button_height, color=color, fill=True)
        display_img.draw_string(175, button_y + 10, "Laser", color=(255, 255, 255), scale=1)

        # 重置按钮
        display_img.draw_rectangle(250, button_y, 60, button_height, color=(0, 0, 255), fill=True)
        display_img.draw_string(255, button_y + 10, "Reset", color=(255, 255, 255), scale=1)

        # 显示测量结果
        result_y = 80
        distance_text = "Distance: " + str(round(system_state['distance'], 2)) + " cm"
        angle_text = "Angle: " + str(round(system_state['angle'], 1)) + " deg"
        display_img.draw_string(10, result_y, distance_text, color=(255, 255, 255), scale=1)
        display_img.draw_string(10, result_y + 20, angle_text, color=(255, 255, 255), scale=1)

        global flag
        # 绘制定位示意图
        center_x, center_y = 160, 150
        if flag>19:
            flag=0
        radius = 50+10*int(flag/5)
        # 绘制圆圈表示检测范围
        for r in range(10+10*int(flag/5), radius, 10):
            display_img.draw_circle(center_x, center_y, r, color=(128, 128, 128))
        if system_state['locating']:
            flag+=2
        else:
            flag=0
        # 绘制声源位置
        if system_state['distance'] > 0:
            angle_rad = math.radians(system_state['angle'])
            target_y = center_y - int(system_state['distance'] * math.cos(angle_rad) * 0.2)
            target_x = center_x + int(system_state['distance'] * math.sin(angle_rad) * 0.2)
            display_img.draw_circle(target_x, target_y, 6, color=(255, 0, 0), fill=True)

        # 绘制原点
        display_img.draw_circle(center_x, center_y, 2, color=(0, 255, 0), fill=True)

        # 在屏幕底部显示错误信息
        if error_state['show_error']:
            error_text = error_state['last_error']
            # 限制错误文本长度以适应屏幕宽度
            if len(error_text) > 45:
                error_text = error_text[:42] + "..."

            # 绘制错误背景
            display_img.draw_rectangle(0, 220, 320, 20, color=(128, 0, 0), fill=True)
            # 绘制错误文本
            display_img.draw_string(5, 225, error_text, color=(255, 255, 255), scale=1)

            # 显示错误计数
            count_text = "Err:" + str(error_state['error_count'])
            display_img.draw_string(270, 225, count_text, color=(255, 255, 0), scale=1)

        # 显示到屏幕
        display_img = display_img.rotation_corr(z_rotation=180)
        lcd.display(display_img)

    except Exception as e:
        log_error("界面绘制失败", e)

def main_loop():
    """主循环"""
    global system_state, last_location_time, touch_config

    print("声源定位系统启动")
    print("错误处理系统已启用")

    while True:
        try:
            current_time = time.ticks_ms()

            # 检查错误超时
            clear_error_if_timeout()

            # 检测触摸事件
            try:
                (status, x, y) = ts.read()
                if status != touch_config['status_last']:
                    touch_config['status_last'] = status
                    if status == ts.STATUS_PRESS:
                        handle_touch_event(x, y)

                touch_config['x_last'] = x
                touch_config['y_last'] = y
            except Exception as e:
                log_error("触摸检测失败", e)
#            print(system_state['display'])
            # 绘制界面
            if system_state['display']:
                    #获取原始的声源黑白位图，尺寸 16*16
                imga = mic.get_map()
                #获取声源方向并设置LED显示
                b = mic.get_dir(imga)
                a = mic.set_led(b,(0,0,255))
                #将声源地图重置成正方形，彩虹色
                imgb = imga.resize(160,160)
                imgc = imgb.to_rainbow(1)
                #显示声源图
                lcd.display(imgc)
                continue
            draw_interface()
            # 如果启用定位或跟踪
            if system_state['locating'] or system_state['tracking']:
                try:
                    # 读取麦克风阵列数据
                    imga = mic.get_map()         # 获取麦克风当前的声强图
                    if imga:
                        levels = mic.get_dir(imga)   # 获取每个方向的声源强度值（12 个方向）
                        angle,distance=processor.process_direction(imga,levels)
                        # 计算声源位置
                        if distance is not None and angle is not None:
                            system_state['distance'] = distance
                            system_state['angle'] = angle
                            # 如果启用跟踪，自动开启激光,并发送串口
                            if system_state['tracking']:
                                system_state['laser_on'] = True
                                send_uart_data(distance, angle, system_state['laser_on'])
                            print("距离: " + str(round(distance, 2)) + "cm, 角度: " + str(round(angle, 1)) + "°")
                    last_location_time = current_time
                except Exception as e:
                    log_error("声源定位处理失败", e)

            # 检查串口接收
            """"

            try:
                if uart1 and uart1.any():
                    received = uart1.read()
                    if received:
                        print("收到: " + received.decode())
            except Exception as e:
                log_error("串口接收失败", e)
            """
        except KeyboardInterrupt:
            print("程序被用户中断")
            break
        except Exception as e:
            log_error("主循环异常", e)
            time.sleep(0.1)  # 发生异常时稍长延时

# 初始化处理器和中断
try:
    print("初始化方向处理器...")
    processor = MicDirectionProcessor(kalman_q=0.01, kalman_r=0.1, lb_level=5, use_kalman=False)
    print("方向处理器初始化成功")
except Exception as e:
    log_error("方向处理器初始化失败", e)

# 中断初始化
try:
    if boot_key:
        print("设置按键中断...")
        boot_key.irq(boot_key_irq, GPIO.IRQ_BOTH, GPIO.WAKEUP_NOT_SUPPORT, 7)
        print("按键中断设置成功")
except Exception as e:
    log_error("按键中断设置失败", e)

# 启动主程序
if __name__ == "__main__":
    try:
        print("开始运行主循环...")
        main_loop()
    except KeyboardInterrupt:
        print("程序被用户中断")
        mic.deinit()
    except Exception as e:
        log_error("程序运行失败", e)
        mic.deinit()
    finally:
        try:
            print("清理资源...")
            mic.deinit()
            print("资源清理完成")
        except Exception as e:
            print("资源清理失败:", str(e))
