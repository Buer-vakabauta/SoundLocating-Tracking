from board import board_info
from fpioa_manager import fm
from maix import GPIO, I2S
from maix import mic_array as mic
import time, image, lcd, gc, math
from machine import UART
import touchscreen as ts

system_state = {
    'locating': False,
    'tracking': False,
    'laser_on': False,
    'distance': 0.0,
    'angle': 0.0,
    'target_x': 0.0,
    'target_y': 0.0,
    'display': False
}

touch_config = {
    'status_last': ts.STATUS_IDLE,
    'x_last': 0,
    'y_last': 0
}

flag = 0
last_press_time = 0

# 硬件初始化
mic.init(i2s_d0=44, i2s_d1=46, i2s_d2=45, i2s_d3=47, i2s_ws=43, i2s_sclk=11, sk9822_dat=39, sk9822_clk=40)
fm.register(1, fm.fpioa.UART1_TX)
fm.register(0, fm.fpioa.UART1_RX)
fm.register(board_info.BOOT_KEY, fm.fpioa.GPIOHS0, force=True)
uart1 = UART(UART.UART1, 115200)
lcd.init()
ts.init()
lcd.clear()
boot_key = GPIO(GPIO.GPIOHS0, GPIO.IN, GPIO.PULL_UP)
display_img = image.Image()

class MicDirectionProcessor:
    def __init__(self, lb_level=3):
        self.lp_buffer = [0] * lb_level
        self.lp_index = 0
        self.lp_level = lb_level
        self.last_angle = 0

    def low_pass_filter(self, value):
        self.lp_buffer[self.lp_index] = value
        if self.lp_index == self.lp_level - 1:
            avg = sum(self.lp_buffer) / self.lp_level
            self.lp_index = 0
            return avg
        else:
            self.lp_index += 1
            return None

    def process_direction(self, imga, levels):
        if imga is None or levels is None or len(levels) == 0:
            return None, None
        angle_x = sum(levels[i] * math.sin(i * math.pi / 6) for i in range(len(levels)))
        angle_y = sum(levels[i] * math.cos(i * math.pi / 6) for i in range(len(levels)))
        if angle_x == 0 and angle_y == 0:
            return None, None
        angle = math.degrees(math.atan2(angle_x, angle_y))
        if -60 <= angle <= 60:
            angle = self.last_angle * 0.1 + angle * 0.9
            filtered = self.low_pass_filter(angle)
            if filtered is not None:
                filtered = max(min(filtered, 90), -90)
                self.last_angle = filtered
                distance = 275 / math.cos(filtered * math.pi / 180)
                return round(filtered, 2), round(distance, 2)
        return None, None

def boot_key_irq(key):
    global last_press_time, system_state
    current_time = time.ticks_ms()
    if current_time - last_press_time > 200:
        if key.value() == 0:
            system_state['display'] = not system_state['display']
        last_press_time = current_time

def handle_touch_event(x, y):
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
    system_state['locating'] = False
    system_state['tracking'] = False
    system_state['laser_on'] = False
    system_state['distance'] = 0.0
    system_state['angle'] = 0.0
    send_laser_control(False)

def send_uart_data(distance, angle, laser_on=False):
    if uart1:
        laser = 1 if laser_on else 0
        json_str = '('+str(angle)+','+str(laser)+')' + '\n'
        uart1.write(json_str.encode())

def send_laser_control(state):
    send_uart_data(0, -180, state)

def draw_interface():
    global system_state, display_img, flag
    display_img.clear()
    display_img.draw_string(10, 10, "Sound Source Localization&Tracking", color=(255, 255, 255), scale=1)
    button_y = 40
    color = (0, 255, 0) if system_state['locating'] else (255, 0, 0)
    display_img.draw_rectangle(10, button_y, 70, 30, color=color, fill=True)
    display_img.draw_string(15, button_y + 10, "Locate", color=(255, 255, 255), scale=1)
    color = (0, 255, 0) if system_state['tracking'] else (255, 0, 0)
    display_img.draw_rectangle(90, button_y, 70, 30, color=color, fill=True)
    display_img.draw_string(95, button_y + 10, "Track", color=(255, 255, 255), scale=1)
    color = (0, 255, 0) if system_state['laser_on'] or system_state['tracking'] else (255, 0, 0)
    display_img.draw_rectangle(170, button_y, 70, 30, color=color, fill=True)
    display_img.draw_string(175, button_y + 10, "Laser", color=(255, 255, 255), scale=1)
    display_img.draw_rectangle(250, button_y, 60, 30, color=(0, 0, 255), fill=True)
    display_img.draw_string(255, button_y + 10, "Reset", color=(255, 255, 255), scale=1)

    result_y = 80
    distance_text = "Distance: " + str(round(system_state['distance'], 2)) + " cm"
    angle_text = "Angle: " + str(round(system_state['angle'], 1)) + " deg"
    display_img.draw_string(10, result_y, distance_text, color=(255, 255, 255), scale=1)
    display_img.draw_string(10, result_y + 20, angle_text, color=(255, 255, 255), scale=1)
    center_x, center_y = 160, 150
    if flag > 19:
        flag = 0
    radius = 50 + 10 * int(flag / 5)
    for r in range(10 + 10 * int(flag / 5), radius, 10):
        display_img.draw_circle(center_x, center_y, r, color=(128, 128, 128))
    if system_state['locating']:
        flag += 2
    else:
        flag = 0
    if system_state['distance'] > 0:
        angle_rad = math.radians(system_state['angle'])
        target_y = center_y - int(system_state['distance'] * math.cos(angle_rad) * 0.2)
        target_x = center_x + int(system_state['distance'] * math.sin(angle_rad) * 0.2)
        display_img.draw_circle(target_x, target_y, 6, color=(255, 0, 0), fill=True)
    display_img.draw_circle(center_x, center_y, 2, color=(0, 255, 0), fill=True)
    display_img = display_img.rotation_corr(z_rotation=180)
    lcd.display(display_img)

def main_loop():
    processor = MicDirectionProcessor(lb_level=5)
    while True:
        current_time = time.ticks_ms()
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

        if system_state['display']:
            imga = mic.get_map()
            b = mic.get_dir(imga)
            mic.set_led(b, (0, 0, 255))
            lcd.display(imga.resize(160, 160).to_rainbow(1))
            continue

        draw_interface()
        if system_state['locating'] or system_state['tracking']:
            imga = mic.get_map()
            if imga:
                levels = mic.get_dir(imga)
                angle, distance = processor.process_direction(imga, levels)
                if angle is not None and distance is not None:
                    system_state['angle'] = angle
                    system_state['distance'] = distance
                    if system_state['tracking']:
                        system_state['laser_on'] = True
                        send_uart_data(distance, angle, system_state['laser_on'])

# 设置中断
boot_key.irq(boot_key_irq, GPIO.IRQ_BOTH, GPIO.WAKEUP_NOT_SUPPORT, 7)

# 启动主循环
main_loop()
