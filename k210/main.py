from board import board_info  # 获取开发板信息
from fpioa_manager import fm
from maix import GPIO,I2S
import time, sensor, image, lcd, gc, math
from machine import UART, SPI
import struct
import json
import touchscreen as ts

# 全局变量------------------------------------
# 系统状态
system_state = {
    'locating': False,
    'tracking': False,
    'laser_on': False,
    'distance': 0.0,
    'angle': 0.0,
    'target_x': 0.0,
    'target_y': 0.0
}

# 麦克风阵列配置
mic_array_config = {
    'sample_rate': 16000,
    'channels': 6,
    'buffer_size': 1024,
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
fm.register(1, fm.fpioa.UART1_TX)
fm.register(0, fm.fpioa.UART1_RX)

# 麦克风阵列引脚
fm.register(2, fm.fpioa.I2S0_OUT_D0)    # MIC_D0
fm.register(3, fm.fpioa.I2S0_OUT_D1)    # MIC_D1
fm.register(4, fm.fpioa.I2S0_OUT_D2)    # MIC_D2
fm.register(5, fm.fpioa.I2S0_OUT_D3)    # MIC_D3
fm.register(6, fm.fpioa.I2S0_WS)        # MIC_WS
fm.register(7, fm.fpioa.I2S0_SCLK)      # MIC_CK

# LED指示灯
fm.register(8, fm.fpioa.SPI1_SCLK)      # LED_CK
fm.register(9, fm.fpioa.SPI1_D0)        # LED_DA

# 触摸屏
fm.register(10, fm.fpioa.SPI0_SCLK)     # 触摸屏时钟
fm.register(11, fm.fpioa.SPI0_D0)       # 触摸屏数据
fm.register(12, fm.fpioa.SPI0_D1)       # 触摸屏数据

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
    print("I2S初始化失败")

# LED指示灯初始化
spi_led = SPI(SPI.SPI1, mode=SPI.MODE_MASTER, baudrate=1000000, polarity=0, phase=0)

# 函数定义------------------------------------

def boot_key_irq(key):
    """按键中断处理"""
    global last_press_time, system_state
    current_time = time.ticks_ms()

    if current_time - last_press_time > 200:  # 防抖动
        if key.value() == 0:  # 按下
            system_state['locating'] = not system_state['locating']
            if system_state['locating']:
                print("开始声源定位")
                set_led_color(0, 255, 0)  # 绿色
            else:
                print("停止声源定位")
                set_led_color(255, 0, 0)  # 红色
                system_state['laser_on'] = False
                send_laser_control(False)
        last_press_time = current_time

def touch_irq(pin):
    """触摸屏中断处理"""
    global touch_config
    # 读取触摸坐标
    touch_data = read_touch_position()
    if touch_data:
        touch_config['x_last'] = touch_data[0]
        touch_config['y_last'] = touch_data[1]
        handle_touch_event(touch_config['x_last'], touch_config['y_last'])

def read_touch_position():
    """读取触摸屏位置"""
    global touch_config

    try:
        (status, x, y) = ts.read()

        if status != touch_config['status_last']:
            touch_config['status_last'] = status
            if status == ts.STATUS_PRESS:
                return (x, y)

        return None
    except:
        return None

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
    set_led_color(0, 0, 255)  # 蓝色表示重置

def set_led_color(r, g, b):
    """设置LED颜色"""
    try:
        # SK9822 LED控制协议
        start_frame = bytearray([0x00, 0x00, 0x00, 0x00])
        led_frame = bytearray([0xFF, b, g, r])  # 亮度+BGR
        end_frame = bytearray([0xFF, 0xFF, 0xFF, 0xFF])

        spi_led.write(start_frame)
        spi_led.write(led_frame)
        spi_led.write(end_frame)
    except:
        pass

def read_microphone_array():
    """读取麦克风阵列数据"""
    global audio_buffer

    try:
        # 读取I2S音频数据
        audio_data = i2s_mic.record(mic_array_config['buffer_size'])
        if audio_data:
            # 将数据转换为6通道音频
            samples = struct.unpack('<' + 'h' * (len(audio_data) // 2), audio_data)

            # 按通道分离数据
            channels = [[] for _ in range(6)]
            for i in range(0, len(samples), 6):
                for ch in range(6):
                    if i + ch < len(samples):
                        channels[ch].append(samples[i + ch])

            return channels
    except:
        pass

    return None

def calculate_sound_source_location(audio_channels):
    """计算声源位置"""
    if not audio_channels or len(audio_channels) < 6:
        return None, None

    # 这里是声源定位算法的接口
    # 实际实现需要使用TDOA（时差定位）或波束形成等算法

    # 简化的定位算法示例
    try:
        # 计算各通道间的时间差
        time_delays = calculate_time_delays(audio_channels)

        # 根据时间差计算位置
        distance, angle = tdoa_localization(time_delays)

        return distance, angle
    except:
        return None, None

def calculate_time_delays(channels):
    """计算各通道间的时间差"""
    # 简化的互相关算法
    time_delays = []

    for i in range(1, len(channels)):
        # 计算第i个通道相对于第0个通道的时间差
        delay = cross_correlation_delay(channels[0], channels[i])
        time_delays.append(delay)

    return time_delays

def cross_correlation_delay(sig1, sig2):
    """计算两个信号的互相关时间差"""
    # 简化实现，返回随机时间差用于演示
    # 实际需要实现完整的互相关算法
    return 0.001 * (hash(str(sig1[:10])) % 100 - 50)

def tdoa_localization(time_delays):
    """基于时间差的定位算法"""
    # 简化的TDOA定位算法
    # 实际需要解非线性方程组

    if not time_delays:
        return 0, 0

    # 简化计算
    avg_delay = sum(time_delays) / len(time_delays)
    distance = abs(avg_delay) * localization_params['sound_speed'] * 100  # 转换为cm

    # 限制距离范围
    distance = max(localization_params['min_distance'] * 100,
                  min(distance, localization_params['max_distance'] * 100))

    # 计算角度
    angle = math.atan2(time_delays[0], time_delays[1] if len(time_delays) > 1 else 0.001)
    angle = math.degrees(angle)

    return distance, angle

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
        print("串口发送失败: " + str(e))

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
        print("激光控制失败: " + str(e))

def draw_interface():
    """绘制用户界面"""
    global system_state, display_img

    # 清除图像
    display_img.clear()

    # 绘制标题
    display_img.draw_string(10, 10, "Sound Source Localization", color=(255, 255, 255), scale=1)

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
    color = (0, 255, 0) if system_state['laser_on'] else (255, 0, 0)
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

    # 绘制定位示意图
    center_x, center_y = 160, 150
    radius = 50

    # 绘制圆圈表示检测范围
    for r in range(10, radius, 10):
        display_img.draw_circle(center_x, center_y, r, color=(128, 128, 128))

    # 绘制声源位置
    if system_state['distance'] > 0:
        angle_rad = math.radians(system_state['angle'])
        target_x = center_x + int(system_state['distance'] * math.cos(angle_rad) * 0.5)
        target_y = center_y + int(system_state['distance'] * math.sin(angle_rad) * 0.5)
        display_img.draw_circle(target_x, target_y, 3, color=(255, 0, 0), fill=True)

    # 绘制原点
    display_img.draw_circle(center_x, center_y, 2, color=(0, 255, 0), fill=True)

    # 状态指示
    status_y = 200
    if system_state['locating']:
        display_img.draw_string(10, status_y, "Status: Locating...", color=(0, 255, 0), scale=1)
    elif system_state['tracking']:
        display_img.draw_string(10, status_y, "Status: Tracking...", color=(255, 255, 0), scale=1)
    else:
        display_img.draw_string(10, status_y, "Status: Standby", color=(255, 255, 255), scale=1)

    # 显示到屏幕
    lcd.display(display_img)

def main_loop():
    """主循环"""
    global system_state, last_location_time, touch_config

    print("声源定位系统启动")
    set_led_color(0, 0, 255)  # 蓝色表示启动

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
                audio_channels = read_microphone_array()

                if audio_channels:
                    # 计算声源位置
                    distance, angle = calculate_sound_source_location(audio_channels)

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
    except KeyboardInterrupt:
        print("程序停止")
        set_led_color(255, 0, 0)  # 红色表示停止
    except Exception as e:
        print("程序错误: " + str(e))
        set_led_color(255, 255, 0)  # 黄色表示错误
