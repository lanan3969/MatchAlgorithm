"""主程序入口"""
import logging
import signal
import sys
from threat_analyzer import find_most_threatening_target
from serial_handler import SerialHandler
from udp_server import UDPServer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# 全局变量，用于优雅退出
running = True
vibrator_id = 0  # 固定使用振动器编号0


def signal_handler(sig, frame):
    """处理中断信号（Ctrl+C）"""
    global running
    logger.info("Received interrupt signal, shutting down...")
    running = False


def calculate_vibration_intensity(threat_score: float, max_threat_score: float) -> int:
    """
    根据威胁度计算震动强度
    
    Args:
        threat_score: 当前目标的威胁度
        max_threat_score: 最大可能的威胁度（用于归一化）
    
    Returns:
        震动强度：255（高威胁）或200（低威胁）
    """
    if max_threat_score == 0:
        return 200
    
    # 归一化威胁度（0-1）
    normalized_threat = threat_score / max_threat_score
    
    # 如果威胁度超过阈值，使用高强度，否则使用低强度
    # 阈值设为0.5（可根据实际需求调整）
    if normalized_threat > 0.5:
        return 255
    else:
        return 200


def main():
    """主函数"""
    global running
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 初始化UDP服务器
    udp_server = UDPServer(host="0.0.0.0", port=5005)
    if not udp_server.start():
        logger.error("Failed to start UDP server, exiting...")
        sys.exit(1)
    
    # 初始化串口处理器
    serial_handler = SerialHandler(port="COM7", baudrate=9600)
    if not serial_handler.connect():
        logger.error("Failed to connect to serial port, exiting...")
        udp_server.stop()
        sys.exit(1)
    
    logger.info("System initialized successfully. Waiting for data...")
    
    try:
        while running:
            # 接收UDP数据
            game_data = udp_server.receive_data()
            
            if game_data is None:
                # 超时或接收失败，继续循环
                continue
            
            # 打印接收到的数据详情
            logger.info("=" * 60)
            logger.info(f"Processing received data - Round: {game_data.round}")
            logger.info(f"Player Position: X={game_data.playerPosition.x:.2f}, Y={game_data.playerPosition.y:.2f}, Z={game_data.playerPosition.z:.2f}")
            logger.info(f"Total targets: {len(game_data.targets)}")
            for i, target in enumerate(game_data.targets, 1):
                logger.info(f"  Target {i}: ID={target.id}, Type={target.type}, Distance={target.distance:.2f}, Angle={target.angle:.2f}°, Position=({target.position.x:.2f}, {target.position.y:.2f}, {target.position.z:.2f})")
            logger.info("=" * 60)
            
            # 如果没有目标，跳过
            if not game_data.targets:
                logger.warning("No targets in received data, skipping...")
                continue
            
            # 找出最有威胁的目标
            most_threatening = find_most_threatening_target(game_data)
            
            if most_threatening is None:
                logger.warning("Could not determine most threatening target")
                continue
            
            # 计算威胁度分数（用于决定震动强度）
            from threat_analyzer import calculate_threat_score
            threat_score = calculate_threat_score(
                most_threatening, 
                game_data.playerPosition
            )
            
            # 估算最大威胁度（用于归一化）
            # Tank在正前方距离1时的威胁度作为参考
            max_threat_score = (1.0 / (1 + 1)) * (1.0 / (0 + 1)) * 2.0  # = 1.0
            
            # 计算震动强度
            intensity = calculate_vibration_intensity(threat_score, max_threat_score)
            
            # 发送震动信号
            success = serial_handler.send_vibration(vibrator_id, intensity)
            
            if not success:
                logger.error("Failed to send vibration signal")
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
    finally:
        # 清理资源
        logger.info("Cleaning up resources...")
        serial_handler.disconnect()
        udp_server.stop()
        logger.info("System shutdown complete")


if __name__ == "__main__":
    main()

