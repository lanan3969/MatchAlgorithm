"""串口通信模块"""
import logging
import serial
import time
from typing import Optional

logger = logging.getLogger(__name__)


class SerialHandler:
    """串口通信处理器"""
    
    def __init__(self, port: str = "COM7", baudrate: int = 9600):
        """
        初始化串口连接
        
        Args:
            port: 串口名称，默认COM7
            baudrate: 波特率，默认9600
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
    
    def connect(self) -> bool:
        """
        连接串口
        
        Returns:
            连接是否成功
        """
        logger.info(f"Attempting to connect to serial port {self.port} with baudrate {self.baudrate}...")
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            logger.info("=" * 60)
            logger.info(f"✓ Serial port connection successful!")
            logger.info(f"  Port: {self.port}")
            logger.info(f"  Baudrate: {self.baudrate}")
            logger.info(f"  Timeout: 1 second")
            logger.info("=" * 60)
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to serial port {self.port}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to serial port: {e}")
            return False
    
    def disconnect(self):
        """断开串口连接"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            logger.info(f"Disconnected from serial port {self.port}")
    
    def send_vibration(self, vibrator_id: int, intensity: int, duration: float = 0.5) -> bool:
        """
        发送震动信号并控制震动时长
        
        Args:
            vibrator_id: 振动器编号
            intensity: 震动强度（200或255）
            duration: 震动持续时间（秒），默认0.5秒
        
        Returns:
            发送是否成功
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            logger.error("Serial port is not connected")
            return False
        
        # 验证强度值
        if intensity not in [200, 255]:
            logger.warning(f"Invalid intensity {intensity}, using 200")
            intensity = 200
        
        try:
            # 第一步：发送震动信号
            start_message = f"{vibrator_id} {intensity}\n"
            bytes_written = self.serial_connection.write(start_message.encode('utf-8'))
            logger.info("─" * 60)
            logger.info(f"✓ Vibration START signal sent to serial port {self.port}")
            logger.info(f"  Vibrator ID: {vibrator_id}")
            logger.info(f"  Intensity: {intensity} {'(HIGH THREAT)' if intensity == 255 else '(LOW THREAT)'}")
            logger.info(f"  Message: {start_message.strip()}")
            logger.info(f"  Bytes written: {bytes_written}")
            logger.info(f"  Duration: {duration} seconds")
            
            # 第二步：等待指定时长
            time.sleep(duration)
            
            # 第三步：发送停止信号
            stop_message = f"{vibrator_id} 0\n"
            bytes_written_stop = self.serial_connection.write(stop_message.encode('utf-8'))
            logger.info(f"✓ Vibration STOP signal sent")
            logger.info(f"  Message: {stop_message.strip()}")
            logger.info(f"  Bytes written: {bytes_written_stop}")
            logger.info("─" * 60)
            return True
        except Exception as e:
            logger.error(f"Failed to send vibration signal: {e}")
            return False
    
    def is_connected(self) -> bool:
        """检查串口是否已连接"""
        return self.serial_connection is not None and self.serial_connection.is_open

    def hardware_test(self, num_vibrators: int = 8, test_duration: float = 1.0) -> bool:
        """
        硬件测试：依次测试所有振动器
        
        Args:
            num_vibrators: 振动器数量，默认8个（编号0-7）
            test_duration: 每个振动器的测试时长（秒），默认1秒
        
        Returns:
            测试是否成功完成
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            logger.error("Serial port is not connected, cannot perform hardware test")
            return False
        
        logger.info("=" * 60)
        logger.info("🔧 Starting hardware test for all vibrators...")
        logger.info(f"  Total vibrators: {num_vibrators} (ID: 0-{num_vibrators-1})")
        logger.info(f"  Test duration per vibrator: {test_duration} seconds")
        logger.info(f"  Intensity: 255 (HIGH)")
        logger.info("=" * 60)
        
        try:
            for vibrator_id in range(num_vibrators):
                # 启动震动
                start_message = f"{vibrator_id} 255\n"
                self.serial_connection.write(start_message.encode('utf-8'))
                logger.info(f"✓ Vibrator {vibrator_id}: START (255) - {start_message.strip()}")
                
                # 等待指定时长
                time.sleep(test_duration)
                
                # 停止震动
                stop_message = f"{vibrator_id} 0\n"
                self.serial_connection.write(stop_message.encode('utf-8'))
                logger.info(f"✓ Vibrator {vibrator_id}: STOP (0) - {stop_message.strip()}")
                
                # 短暂间隔，避免震动器切换过快
                time.sleep(0.2)
            
            logger.info("=" * 60)
            logger.info("✅ Hardware test completed successfully!")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"❌ Hardware test failed: {e}")
            return False

