"""检查可用的串口"""
import serial.tools.list_ports

print("\n" + "=" * 60)
print("可用串口列表")
print("=" * 60)

ports = serial.tools.list_ports.comports()

if not ports:
    print("❌ 未找到任何串口设备")
else:
    for port in ports:
        print(f"\n串口: {port.device}")
        print(f"  描述: {port.description}")
        print(f"  硬件ID: {port.hwid}")
        
        # 尝试打开端口检查是否可用
        try:
            s = serial.Serial(port.device, timeout=0.1)
            s.close()
            print(f"  状态: ✓ 可用")
        except serial.SerialException as e:
            print(f"  状态: ✗ 被占用或无权限")
            print(f"  错误: {e}")

print("\n" + "=" * 60)





