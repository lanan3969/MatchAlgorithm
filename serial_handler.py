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
    
    def send_vibration(self, vibrator_id: int, intensity: int, duration: float = 0.5, mode: int = 0) -> bool:
        """
        发送震动信号并控制震动时长
        
        Args:
            vibrator_id: 振动器编号（0-7）
            intensity: 震动强度（200或255）
            duration: 震动持续时间（秒），默认0.5秒
            mode: 震动模式（0-3），默认0
                  0=持续震动
                  1=超快脉冲 (密集蜂鸣)
                  2=三连击 (敲门效果)
                  3=波浪式 (渐强渐弱)
        
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
        
        # 验证模式值
        if mode not in [0, 1, 2, 3]:
            logger.warning(f"Invalid mode {mode}, using 0")
            mode = 0
        
        # 模式描述
        mode_descriptions = {
            0: "持续震动",
            1: "超快脉冲",
            2: "三连击",
            3: "波浪式"
        }
        
        try:
            # 第一步：发送震动信号（格式：motorID,intensity,mode）
            start_message = f"{vibrator_id},{intensity},{mode}\n"
            bytes_written = self.serial_connection.write(start_message.encode('utf-8'))
            logger.info("─" * 60)
            logger.info(f"✓ Vibration START signal sent to serial port {self.port}")
            logger.info(f"  Vibrator ID: {vibrator_id}")
            logger.info(f"  Intensity: {intensity} {'(HIGH THREAT)' if intensity == 255 else '(LOW THREAT)'}")
            logger.info(f"  Mode: {mode} ({mode_descriptions[mode]})")
            logger.info(f"  Message: {start_message.strip()}")
            logger.info(f"  Bytes written: {bytes_written}")
            logger.info(f"  Duration: {duration} seconds")
            
            # 第二步：等待指定时长
            time.sleep(duration)
            
            # 第三步：发送停止信号
            stop_message = f"{vibrator_id},0,0\n"
            bytes_written_stop = self.serial_connection.write(stop_message.encode('utf-8'))
            logger.info(f"✓ Vibration STOP signal sent")
            logger.info(f"  Message: {stop_message.strip()}")
            logger.info(f"  Bytes written: {bytes_written_stop}")
            logger.info("─" * 60)
            return True
        except Exception as e:
            logger.error(f"Failed to send vibration signal: {e}")
            return False
    
    def send_multi_vibration(self, intensities: list, duration: float = 3.0, mode: int = 0) -> bool:
        """
        同时发送多个马达的震动信号（用于态势感知模式）
        
        Args:
            intensities: 16个马达的震动强度列表（0-255）
            duration: 震动持续时间（秒），默认3.0秒
            mode: 震动模式（0-3），默认0
        
        Returns:
            发送是否成功
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            logger.error("Serial port is not connected")
            return False
        
        if len(intensities) != 16:
            logger.error(f"Invalid intensities length: {len(intensities)}, expected 16")
            return False
        
        try:
            logger.info("=" * 60)
            logger.info("🌐 态势感知模式 - 16方向多马达同时震动")
            logger.info(f"  震动模式: {mode}")
            logger.info(f"  持续时间: {duration}s")
            logger.info("  各方向震动强度:")
            
            # 方向描述（16个）
            directions = [
                "正北(0)", "北偏东(1)", "东北(2)", "东偏北(3)",
                "正东(4)", "东偏南(5)", "东南(6)", "南偏东(7)",
                "正南(8)", "南偏西(9)", "西南(10)", "西偏南(11)",
                "正西(12)", "西偏北(13)", "西北(14)", "北偏西(15)"
            ]
            
            # 发送所有16个马达的启动信号
            for motor_id in range(16):
                intensity = int(intensities[motor_id])
                if intensity > 0:
                    start_message = f"{motor_id},{intensity},{mode}\n"
                    self.serial_connection.write(start_message.encode('utf-8'))
                    logger.info(f"    {directions[motor_id]}: 强度 {intensity}")
            
            logger.info("─" * 60)
            
            # 等待指定时长
            time.sleep(duration)
            
            # 发送所有16个马达的停止信号
            for motor_id in range(16):
                stop_message = f"{motor_id},0,0\n"
                self.serial_connection.write(stop_message.encode('utf-8'))
            
            logger.info("✓ 态势感知震动完成")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send multi-motor vibration signals: {e}")
            return False
    
    def is_connected(self) -> bool:
        """检查串口是否已连接"""
        return self.serial_connection is not None and self.serial_connection.is_open

    def hardware_test(self, num_vibrators: int = 16, test_duration: float = 1.0, pause_duration: float = 1.0) -> bool:
        """
        硬件测试：依次测试所有振动器的所有模式
        
        Args:
            num_vibrators: 振动器数量，默认16个（编号0-15）
            test_duration: 每种模式的测试时长（秒），默认1秒
            pause_duration: 每次测试之间的间隔时长（秒），默认1秒
        
        Returns:
            测试是否成功完成
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            logger.error("Serial port is not connected, cannot perform hardware test")
            return False
        
        # 模式描述
        mode_descriptions = {
            0: "持续震动",
            1: "超快脉冲 (密集蜂鸣)",
            2: "三连击 (敲门效果)",
            3: "波浪式 (渐强渐弱)"
        }
        
        logger.info("=" * 60)
        logger.info("🔧 Starting comprehensive hardware test...")
        logger.info(f"  Total vibrators: {num_vibrators} (ID: 0-{num_vibrators-1})")
        logger.info(f"  Modes per vibrator: 4 (Mode 0-3)")
        logger.info(f"  Test duration per mode: {test_duration} seconds")
        logger.info(f"  Pause between tests: {pause_duration} seconds")
        logger.info(f"  Intensity: 255 (HIGH)")
        logger.info("=" * 60)
        
        try:
            for vibrator_id in range(num_vibrators):
                logger.info(f"\n{'─' * 60}")
                logger.info(f"📍 Testing Vibrator #{vibrator_id}")
                logger.info(f"{'─' * 60}")
                
                for mode in range(4):  # 测试4种模式：0, 1, 2, 3
                    # 启动震动（发送格式：motorID,intensity,mode）
                    start_message = f"{vibrator_id},{255},{mode}\n"
                    self.serial_connection.write(start_message.encode('utf-8'))
                    logger.info(f"✓ Vibrator {vibrator_id} Mode {mode} ({mode_descriptions[mode]}): START - {start_message.strip()}")
                    
                    # 等待指定时长
                    time.sleep(test_duration)
                    
                    # 停止震动
                    stop_message = f"{vibrator_id},0,0\n"
                    self.serial_connection.write(stop_message.encode('utf-8'))
                    logger.info(f"✓ Vibrator {vibrator_id} Mode {mode}: STOP - {stop_message.strip()}")
                    
                    # 间隔时长（除非是最后一个测试）
                    if not (vibrator_id == num_vibrators - 1 and mode == 3):
                        logger.info(f"⏸  Pausing {pause_duration}s...")
                        time.sleep(pause_duration)
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ Hardware test completed successfully!")
            logger.info(f"   Total tests: {num_vibrators * 4} ({num_vibrators} vibrators × 4 modes)")
            logger.info("=" * 60)
            return True
            
        except Exception as e:
            logger.error(f"❌ Hardware test failed: {e}")
            return False

