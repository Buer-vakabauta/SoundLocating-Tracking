from board import board_info  # 获取开发板信息
from fpioa_manager import fm
from maix import GPIO,I2S
from maix import mic_array as mic
import time, sensor, image, lcd, gc, math
from machine import UART, SPI
import struct
import json
import touchscreen as ts

# 全局变量------------------------------------
flag=0
# 系统状态
system_state = {
    'locating': False,#定位模式
    'tracking': False,#追踪模式
    'laser_on': False,#激光状态
    'distance': 0.0,#距离
    'angle': 0.0,#角度
    'target_x': 0.0,#目标位置X
    'target_y': 0.0,#目标位置y
}

# 麦克风阵列配置
mic_array_config = {
    'sample_rate': 16000,#采样率
    'channels': 6,#通道数
    'buffer_size': 1024,#采样缓冲区大小
    'positions': [  # 麦克风相对位置 (x, y) cm
        (0, 0),     # M0
        (2, 0),     # M1
        (4, 0),     # M2
        (6, 0),     # M3
        (8, 0),     # M4
        (10, 0)     # M5
    ]
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

last_press_time = 0
last_location_time = 0
audio_buffer = []
#------------------------------------------

# 引脚配置------------------------------------
# 串口通信
fm.register(1, fm.fpioa.UART1_TX)#10
fm.register(0, fm.fpioa.UART1_RX)#8

# 麦克风阵列引脚
#fm.register(43, fm.fpioa.I2S0_WS)        # MIC_WS#21
#fm.register(11, fm.fpioa.I2S0_SCLK)      # MIC_CK#22
#fm.register(44, fm.fpioa.I2S0_OUT_D0)    # MIC_D0#23
#fm.register(46, fm.fpioa.I2S0_OUT_D1)    # MIC_D1#24
#fm.register(45, fm.fpioa.I2S0_OUT_D2)    # MIC_D2#25
#fm.register(47, fm.fpioa.I2S0_OUT_D3)    # MIC_D3#26
mic.init(i2s_d0=44, i2s_d1=46, i2s_d2=45, i2s_d3=47, i2s_ws=43, i2s_sclk=11, sk9822_dat=39,  sk9822_clk=40)
# 按键
fm.register(board_info.BOOT_KEY, fm.fpioa.GPIOHS0, force=True)
#------------------------------------------

# 初始化-------------------------------------
# 构造UART对象
uart1 = UART(UART.UART1, 115200)

# 屏幕初始化
lcd.init()
ts.init()
lcd.clear()

# 摄像头（用于调试显示）
sensor.reset(dual_buff=True)
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_windowing((224, 224))
sensor.skip_frames(time=2000)

# 按键中断初始化
boot_key = GPIO(GPIO.GPIOHS0, GPIO.IN, GPIO.PULL_UP)

# 显示图像对象
display_img = image.Image()

# I2S麦克风阵列初始化
try:
    i2s_mic = I2S(I2S.DEVICE_0)
    i2s_mic.channel_config(I2S.CHANNEL_0, I2S.RECEIVER, resolution=I2S.RESOLUTION_16_BIT,
                          cycles=I2S.SCLK_CYCLES_32, align_mode=I2S.STANDARD_MODE)
    i2s_mic.set_sample_rate(mic_array_config['sample_rate'])
except:
    print('I2S Init Faild')



# 函数定义------------------------------------

def get_direction_and_distance():
    """获取声源方向和距离信息"""
    try:
        # 获取距离映射信息
        distance_map = mic.get_map()
        return distance_map

    except Exception as e:
        print("获取方向距离数据时出错:",str(e))
        return None

def calculate_distance_estimate(distance_map):
        """
        基于距离映射估算距离
        distance_map包含各个方向的强度信息，用于估算距离
        """
        if distance_map is None:
            return None

        try:
            # 计算平均强度
            total_intensity = sum(distance_map)
            avg_intensity = total_intensity / len(distance_map)

            # 根据强度估算距离
            if avg_intensity > 0:
                estimated_distance = 1000 / avg_intensity
                return min(estimated_distance, 500)  # 限制最大距离为500cm
            else:
                return None

        except Exception as e:
            print("计算距离估算时出错:",str(e))
            return None

def boot_key_irq(key):
    """按键中断处理"""
    global last_press_time, system_state
    current_time = time.ticks_ms()

    if current_time - last_press_time > 200:  # 防抖动
        if key.value() == 0:  # 按下
            system_state['locating'] = not system_state['locating']
            if system_state['locating']:
                print("开始声源定位")

            else:
                print("停止声源定位")

                system_state['laser_on'] = False
                send_laser_control(False)
        last_press_time = current_time


def handle_touch_event(x, y):
    """处理触摸事件"""
    global system_state

    # 定义触摸区域
    if y < 60:  # 顶部控制区域
        if x < 80:  # 定位按钮
            system_state['locating'] = not system_state['locating']
        elif x < 160:  # 跟踪按钮
            system_state['tracking'] = not system_state['tracking']
        elif x < 240:  # 激光按钮
            system_state['laser_on'] = not system_state['laser_on']
            send_laser_control(system_state['laser_on'])
        else:  # 重置按钮
            reset_system()

def reset_system():
    """重置系统"""
    global system_state
    system_state['locating'] = False
    system_state['tracking'] = False
    system_state['laser_on'] = False
    system_state['distance'] = 0.0
    system_state['angle'] = 0.0
    send_laser_control(False)




def send_uart_data(distance, angle, laser_on=False):
    """发送数据到STM32"""
    try:
        data = {
            'distance': round(distance, 2),
            'angle': round(angle, 2),
            'laser': laser_on,
            'timestamp': time.ticks_ms()
        }

        json_str = json.dumps(data) + '\n'
        uart1.write(json_str.encode())

    except Exception as e:
        print('Uart:'+'str(e)')

def send_laser_control(laser_on):
    """发送激光控制命令"""
    try:
        cmd = {
            'cmd': 'laser',
            'state': laser_on,
            'timestamp': time.ticks_ms()
        }

        json_str = json.dumps(cmd) + '\n'
        uart1.write(json_str.encode())

    except Exception as e:
        print('Laser:'+str(e))

def draw_interface():
    """绘制用户界面"""
    global system_state, display_img

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
        target_x = center_x + int(system_state['distance'] * math.cos(angle_rad) * 0.5)
        target_y = center_y + int(system_state['distance'] * math.sin(angle_rad) * 0.5)
        display_img.draw_circle(target_x, target_y, 3, color=(255, 0, 0), fill=True)

    # 绘制原点
    display_img.draw_circle(center_x, center_y, 2, color=(0, 255, 0), fill=True)

    # 状态指示

    # 显示到屏幕
    lcd.display(display_img)

def main_loop():
    """主循环"""
    global system_state, last_location_time, touch_config

    print("声源定位系统启动")

    while True:
        current_time = time.ticks_ms()
        # 检测触摸事件
        try:
            (status, x, y) = ts.read()

            if status != touch_config['status_last']:
                touch_config['status_last'] = status
                if status == ts.STATUS_PRESS:
                    handle_touch_event(x, y)

            touch_config['x_last'] = x
            touch_config['y_last'] = y
        except:
            pass

        # 绘制界面
        draw_interface()

        # 如果启用定位或跟踪
        if system_state['locating'] or system_state['tracking']:
            if current_time - last_location_time > localization_params['update_interval'] * 1000:
                # 读取麦克风阵列数据
                direction_map=get_direction_and_distance()

                if direction_map:
                    # 计算声源位置
                    angle=mic.get_dir(direction_map)
                    distance= calculate_distance_estimate(direction_map)
                    if distance is not None and angle is not None:
                        system_state['distance'] = distance
                        system_state['angle'] = angle

                        # 发送数据到STM32
                        send_uart_data(distance, angle, system_state['laser_on'])

                        # 如果启用跟踪，自动开启激光
                        if system_state['tracking']:
                            system_state['laser_on'] = True
                            send_laser_control(True)
                        print("距离: " + str(round(distance, 2)) + "cm, 角度: " + str(round(angle, 1)) + "°")
                last_location_time = current_time
        # 检查串口接收
        if uart1.any():
            try:
                received = uart1.read()
                if received:
                    print("收到: " + received.decode())
            except:
                pass

        # 短暂延时
        time.sleep(0.05)

# 中断初始化
boot_key.irq(boot_key_irq, GPIO.IRQ_BOTH, GPIO.WAKEUP_NOT_SUPPORT, 7)
# 启动主程序
if __name__ == "__main__":
    try:
        main_loop()
        mic.deinit()
    except Exception as e:
        print("程序错误: " + str(e))
