from board import board_info
from fpioa_manager import fm
from maix import GPIO, I2S
from maix import mic_array as mic
import time, sensor, image, lcd, math
from machine import UART
import json
import touchscreen as ts

# 系统状态
system_state = {
    'locating': False,
    'tracking': False,
    'laser_on': False,
    'distance': 0.0,
    'angle': 0.0
}

mic_array_config = {
    'sample_rate': 16000,
    'channels': 6,
    'buffer_size': 1024
}

touch_config = {
    'width': 320,
    'height': 240,
    'status_last': ts.STATUS_IDLE,
    'x_last': 0,
    'y_last': 0
}

localization_params = {
    'update_interval': 0.1
}

last_press_time = 0
last_location_time = 0
flag = 0

# 引脚配置
fm.register(1, fm.fpioa.UART1_TX)
fm.register(0, fm.fpioa.UART1_RX)
mic.init(i2s_d0=44, i2s_d1=46, i2s_d2=45, i2s_d3=47, i2s_ws=43, i2s_sclk=11, sk9822_dat=39, sk9822_clk=40)
fm.register(board_info.BOOT_KEY, fm.fpioa.GPIOHS0, force=True)

uart1 = UART(UART.UART1, 115200)
lcd.init()
ts.init()
lcd.clear()
sensor.reset(dual_buff=True)
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_windowing((224, 224))
sensor.skip_frames(time=2000)

boot_key = GPIO(GPIO.GPIOHS0, GPIO.IN, GPIO.PULL_UP)
display_img = image.Image()

class MicDirectionProcessor:
    def __init__(self, kalman_q=0.01, kalman_r=0.1, lb_level=5, use_kalman=True):
        self.kalman_prev_cov = 0.1
        self.kalman_state = 0
        self.kalman_Q = kalman_q
        self.kalman_R = kalman_r
        self.use_kalman = use_kalman
        self.lp_buffer = [0] * lb_level
        self.lp_index = 0
        self.lp_level = lb_level
        self.last_angle = 0

    def kalman_filter(self, value):
        cov = self.kalman_prev_cov + self.kalman_Q
        gain = cov / (cov + self.kalman_R)
        output = self.kalman_state + gain * (value - self.kalman_state)
        self.kalman_state = output
        self.kalman_prev_cov = (1 - gain) * cov
        return output

    def low_pass_filter(self, value):
        self.lp_buffer[self.lp_index] = value
        self.lp_index += 1
        if self.lp_index == self.lp_level:
            avg = sum(self.lp_buffer) / self.lp_level
            self.lp_index = 0
            return avg
        return None

    def process_direction(self, imga, levels):
        if imga is None:
            return None, None
        angle_x = sum(levels[i] * math.sin(i * math.pi / 6) for i in range(len(levels)))
        angle_y = sum(levels[i] * math.cos(i * math.pi / 6) for i in range(len(levels)))
        if angle_x == 0 and angle_y == 0:
            return None, None
        angle = math.degrees(math.atan2(angle_x, angle_y))
        if -30 <= angle <= 30:
            filtered = self.low_pass_filter(angle)
            if filtered is not None:
                filtered = max(min(filtered, 30), -30)
                if self.use_kalman:
                    filtered = self.kalman_filter(filtered)
                self.last_angle = filtered
                distance = 275 / math.cos(-filtered * math.pi / 180)
                return round(filtered, 2), round(distance, 2)
        return None, None

def boot_key_irq(key):
    global last_press_time, system_state
    current_time = time.ticks_ms()
    if current_time - last_press_time > 200:
        if key.value() == 0:
            system_state['locating'] = not system_state['locating']
            system_state['laser_on'] = False
            send_laser_control(False)
        last_press_time = current_time

def handle_touch_event(x, y):
    global system_state
    if y < 60:
        if x < 80:
            system_state['locating'] = not system_state['locating']
        elif x < 160:
            system_state['tracking'] = not system_state['tracking']
        elif x < 240:
            system_state['laser_on'] = not system_state['laser_on']
            send_laser_control(system_state['laser_on'])
        else:
            reset_system()

def reset_system():
    global system_state
    system_state['locating'] = False
    system_state['tracking'] = False
    system_state['laser_on'] = False
    system_state['distance'] = 0.0
    system_state['angle'] = 0.0
    send_laser_control(False)

def send_uart_data(distance, angle, laser_on=False):
    try:
        data = {'distance': round(distance, 2), 'angle': round(angle, 2), 'laser': laser_on, 'timestamp': time.ticks_ms()}
        uart1.write((json.dumps(data) + '\n').encode())
    except:
        pass

def send_laser_control(laser_on):
    try:
        cmd = {'cmd': 'laser', 'state': laser_on, 'timestamp': time.ticks_ms()}
        uart1.write((json.dumps(cmd) + '\n').encode())
    except:
        pass

def draw_interface():
    global system_state, display_img, flag
    display_img.clear()
    display_img.draw_string(10, 10, "Sound Source Localization&Tracking", color=(255, 255, 255), scale=1)
    button_y = 40
    button_width = 70
    button_height = 30
    color = (0, 255, 0) if system_state['locating'] else (255, 0, 0)
    display_img.draw_rectangle(10, button_y, button_width, button_height, color=color, fill=True)
    display_img.draw_string(15, button_y + 10, "Locate", color=(255, 255, 255), scale=1)
    color = (0, 255, 0) if system_state['tracking'] else (255, 0, 0)
    display_img.draw_rectangle(90, button_y, button_width, button_height, color=color, fill=True)
    display_img.draw_string(95, button_y + 10, "Track", color=(255, 255, 255), scale=1)
    color = (0, 255, 0) if system_state['laser_on'] or system_state['tracking'] else (255, 0, 0)
    display_img.draw_rectangle(170, button_y, button_width, button_height, color=color, fill=True)
    display_img.draw_string(175, button_y + 10, "Laser", color=(255, 255, 255), scale=1)
    display_img.draw_rectangle(250, button_y, 60, button_height, color=(0, 0, 255), fill=True)
    display_img.draw_string(255, button_y + 10, "Reset", color=(255, 255, 255), scale=1)
    result_y = 80
    display_img.draw_string(10, result_y, "Distance: " + str(round(system_state['distance'], 2)) + " cm", color=(255, 255, 255), scale=1)
    display_img.draw_string(10, result_y + 20, "Angle: " + str(round(system_state['angle'], 1)) + " deg", color=(255, 255, 255), scale=1)
    center_x, center_y = 160, 150
    if flag > 19: flag = 0
    radius = 50 + 10 * int(flag / 5)
    for r in range(10 + 10 * int(flag / 5), radius, 10):
        display_img.draw_circle(center_x, center_y, r, color=(128, 128, 128))
    flag = flag + 2 if system_state['locating'] else 0
    if system_state['distance'] > 0:
        angle_rad = math.radians(system_state['angle'])
        target_x = center_x + int(system_state['distance'] * math.cos(angle_rad) * 0.5)
        target_y = center_y + int(system_state['distance'] * math.sin(angle_rad) * 0.5)
        display_img.draw_circle(target_x, target_y, 3, color=(255, 0, 0), fill=True)
    display_img.draw_circle(center_x, center_y, 2, color=(0, 255, 0), fill=True)
    lcd.display(display_img)

def main_loop():
    global system_state, last_location_time, touch_config
    while True:
        current_time = time.ticks_ms()
        try:
            status, x, y = ts.read()
            if status != touch_config['status_last']:
                touch_config['status_last'] = status
                if status == ts.STATUS_PRESS:
                    handle_touch_event(x, y)
            touch_config['x_last'] = x
            touch_config['y_last'] = y
        except:
            pass
        draw_interface()
        if system_state['locating'] or system_state['tracking']:
            if current_time - last_location_time > localization_params['update_interval'] * 1000:
                imga = mic.get_map()
                if imga:
                    levels = mic.get_dir(imga)
                    angle, distance = processor.process_direction(imga, levels)
                    if distance is not None and angle is not None:
                        system_state['distance'] = distance
                        system_state['angle'] = angle
                        send_uart_data(distance, angle, system_state['laser_on'])
                        if system_state['tracking']:
                            system_state['laser_on'] = True
                            send_laser_control(True)
                last_location_time = current_time
        if uart1.any():
            try:
                received = uart1.read()
                if received:
                    print("收到: " + received.decode())
            except:
                pass
        time.sleep(0.05)

boot_key.irq(boot_key_irq, GPIO.IRQ_BOTH, GPIO.WAKEUP_NOT_SUPPORT, 7)
processor = MicDirectionProcessor(kalman_q=0.01, kalman_r=0.1, lb_level=5, use_kalman=True)

if __name__ == "__main__":
    try:
        main_loop()
        mic.deinit()
    except Exception as e:
        print("程序错误: " + str(e))