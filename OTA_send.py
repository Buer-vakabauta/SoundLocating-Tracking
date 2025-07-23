import serial
import time
import argparse
import os
import sys

START_BYTE = 0xA5
ACK_BYTE = 0x5A
PACKET_SIZE = 98
RETRY_LIMIT = 3
ACK_TIMEOUT = 5  # seconds
MAGIC_TRIGGER = bytes([0x55, 0xAA, 0xDE, 0xAD, 0xBE, 0xEF])
END_MESSAGE=bytes([0XA5,0XFF])
flag=0
def wait_for_bootloader_message(ser, timeout=5):
    """等待并解析bootloader的启动消息"""
    global flag
    print("🔍 等待bootloader启动消息...")
    start_time = time.time()
    buffer = b''
    
    while time.time() - start_time < timeout:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            buffer += data
            
            # 将接收到的数据转换为字符串进行解析
            try:
                message = buffer.decode('utf-8', errors='ignore')
                print(f"📥 收到: {message.strip()}")
                
                # 检查是否收到等待OTA触发的消息
                if "Waiting for OTA trigger" in message and flag==0:
                    print("✅ 检测到bootloader等待OTA触发")
                    flag=1
                    return "waiting_trigger"
                
                # 检查是否已经进入OTA模式
                if "OTA update mode" in message:
                    print("✅ bootloader已进入OTA更新模式")
                    return "ota_mode"
                
                # 检查是否跳转到应用程序
                if "Jumping to App" in message:
                    print("ℹ️ bootloader跳转到应用程序")
                    return "app_mode"
                
                # 如果消息太长，保留最后部分避免内存溢出
                if len(buffer) > 1000:
                    buffer = buffer[-500:]
                    
            except UnicodeDecodeError:
                # 如果解码失败，继续等待更多数据
                pass
    
    print("⏰ 等待bootloader消息超时")
    return "timeout"

def send_magic_trigger(ser):
    """发送魔术值触发OTA模式"""
    print("🔮 发送OTA触发魔术值...")
    ser.write(MAGIC_TRIGGER)
    ser.flush()
    
    # 等待重启后的消息
    time.sleep(1)  # 给设备重启时间
    
    result = wait_for_bootloader_message(ser, timeout=5)
    if result == "ota_mode":
        print("✅ 成功触发OTA模式")
        return True
    else:
        print("❌ 未能进入OTA模式")
        return False

def send_packet(ser, packet, index, total_packets):
    """发送单个数据包"""
    for attempt in range(RETRY_LIMIT):
        # 清空接收缓冲区
        # 发送数据包
        ser.write(bytes(packet))
        ser.flush()
        progress = (index / total_packets) * 100
        print(f"[包 {index}/{total_packets}] ({progress:.1f}%) 发送 {len(packet)} 字节, 等待ACK...")
        start_time = time.time()
        while time.time() - start_time < ACK_TIMEOUT:
            ack = ser.read(1)
            #print("------",ack)
            if ack:    
                ser.flushInput()
                if ack and ack[0] == ACK_BYTE:
                    print(f"[包 {index}] ✅ 收到ACK")
                    return True
                else:
                    print(f"[包 {index}] ❌ 无效ACK: {ack.hex() if ack else 'None'}")
        
        print(f"[包 {index}] ⏰ 等待ACK超时. 重试 {attempt+1}/{RETRY_LIMIT}")
        time.sleep(0.1)  # 短暂延迟后重试
    
    return False

def verify_bin_file(bin_path):
    """验证bin文件"""
    if not os.path.exists(bin_path):
        print(f"❌ 错误: 文件 {bin_path} 不存在")
        return None
    
    file_size = os.path.getsize(bin_path)
    if file_size == 0:
        print(f"❌ 错误: 文件 {bin_path} 为空")
        return None
    
    if file_size > (64 - 16) * 1024:  # 假设64KB Flash，预留16KB给bootloader
        print(f"❌ 错误: 文件太大 ({file_size} bytes), 超过可用Flash空间")
        return None
    
    print(f"📄 文件验证通过: {bin_path} ({file_size} bytes)")
    return file_size

def send_bin_file(serial_port, baud_rate, bin_path, force_trigger=False):
    """发送bin文件进行OTA升级"""
    
    # 验证文件
    file_size = verify_bin_file(bin_path)
    if file_size is None:
        return False
    
    try:
        # 打开串口
        print(f"🔌 连接串口: {serial_port} @ {baud_rate}")
        ser = serial.Serial(serial_port, baud_rate, timeout=0.1)
        time.sleep(0.5)  # 等待串口稳定
        # 清空缓冲区
        ser.flushInput()
        ser.flushOutput()
        ser.write("cmd:restart\n".encode())#发送重启命令
        ser.write("cmd:restart\n".encode())#发送重启命令
        if force_trigger:
            # 强制发送魔术值
            if not send_magic_trigger(ser):
                print("❌ 无法触发OTA模式")
                return False
        else:
            # 等待bootloader消息并判断状态
            result = wait_for_bootloader_message(ser)
            
            if result == "waiting_trigger":
                # bootloader等待触发，发送魔术值
                if not send_magic_trigger(ser):
                    print("❌ 无法触发OTA模式")
                    return False
            elif result == "ota_mode":
                # 已经在OTA模式，直接开始传输
                print("✅ bootloader已在OTA模式")
            elif result == "app_mode":
                print("ℹ️ 设备运行在应用模式，需要重启到bootloader")
                print("💡 请重启设备或使用 --force 参数")
                return False
            else:
                print("❌ 无法确定bootloader状态")
                if input("是否强制发送魔术值? (y/N): ").lower() == 'y':
                    if not send_magic_trigger(ser):
                        print("❌ 无法触发OTA模式")
                        return False
                else:
                    return False
        
        # 读取文件数据
        with open(bin_path, 'rb') as f:
            data = f.read()
        total_packets = (len(data) + PACKET_SIZE - 1) // PACKET_SIZE
        print(f"\n📦 开始传输: {total_packets} 个数据包 ({len(data)} bytes)")
        print("=" * 50)
        print("连接中")
        time.sleep(3)
        start_time = time.time()
        success_count = 0
        
        # 发送数据包
        for i in range(total_packets):
            chunk = data[i * PACKET_SIZE:(i + 1) * PACKET_SIZE]
            length=len(chunk)
            packet = bytes([START_BYTE, length]) + chunk
            success = send_packet(ser, packet, i + 1, total_packets)
            if not success:
                print(f"❌ 发送包 {i + 1} 失败，传输中止")
                return False
            success_count += 1
            time.sleep(0.02)  # 短暂延迟，避免过快发送
        ser.write(END_MESSAGE)
        ser.flush()
        elapsed_time = time.time() - start_time
        speed = len(data) / elapsed_time if elapsed_time > 0 else 0
        
        print("=" * 50)
        print(f"✅ 传输完成!")
        print(f"📊 统计信息:")
        print(f"   - 总包数: {total_packets}")
        print(f"   - 成功包数: {success_count}")
        print(f"   - 传输时间: {elapsed_time:.2f}s")
        print(f"   - 传输速度: {speed:.0f} bytes/s")
        print("设备已自动进入APP")
        
        return True
        
    except serial.SerialException as e:
        print(f"❌ 串口错误: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n⏹️ 用户中断传输")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("🔌 串口已关闭")

def main():
    parser = argparse.ArgumentParser(
        description="STM32 OTA升级工具 - 通过ESP8266桥接",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python ota_tool.py --port COM5 --bin firmware.bin
  python ota_tool.py --port /dev/ttyUSB0 --baud 9600 --bin app.bin --force
        """
    )
    
    parser.add_argument("--port", 
                       help="串口端口, 例如: COM5 或 /dev/ttyUSB0", 
                       default="COM12",
                       type=str)
    parser.add_argument("--baud", 
                       help="波特率 (默认: 9600)", 
                       default=115200, 
                       type=int)
    parser.add_argument("--bin", 
                       help="固件.bin文件路径",
                       default=".\\stm32_servo_control\\bin_file\\projet.bin", 
                       type=str)
    parser.add_argument("--force", 
                       help="强制发送魔术值触发OTA", 
                       action="store_true")
    
    args = parser.parse_args()
    
    print("🚀 STM32 OTA升级工具")
    print("=" * 50)
    
    success = send_bin_file(args.port, args.baud, args.bin, args.force)
    
    if success:
        print("\n🎉 OTA升级完成!")
        sys.exit(0)
    else:
        print("\n💥 OTA升级失败!")
        sys.exit(1)

if __name__ == '__main__':
    main()