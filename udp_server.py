"""UDP服务器模块"""
import socket
import json
import logging
from typing import Optional
from models import GameData

logger = logging.getLogger(__name__)


class UDPServer:
    """UDP服务器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5005):
        """
        初始化UDP服务器
        
        Args:
            host: 监听地址，默认0.0.0.0（所有网络接口）
            port: 监听端口，默认5005
        """
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
    
    def start(self) -> bool:
        """
        启动UDP服务器
        
        Returns:
            启动是否成功
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            self.socket.settimeout(1.0)  # 设置超时以便能够响应中断
            logger.info(f"UDP server started on {self.host}:{self.port}")
            return True
        except OSError as e:
            logger.error(f"Failed to start UDP server: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error starting UDP server: {e}")
            return False
    
    def receive_data(self) -> Optional[GameData]:
        """
        接收UDP数据并解析为GameData对象
        
        Returns:
            GameData对象，如果接收失败或解析失败则返回None
        """
        if not self.socket:
            logger.error("UDP server is not started")
            return None
        
        try:
            # 接收数据（最大65507字节，UDP最大数据包大小）
            data, addr = self.socket.recvfrom(65507)
            logger.info(f"Received UDP data from {addr}, size: {len(data)} bytes")
            
            # 解析JSON
            try:
                json_str = data.decode('utf-8')
                logger.info(f"Received JSON data: {json_str}")
                json_data = json.loads(json_str)
                game_data = GameData.from_dict(json_data)
                logger.info(f"Successfully parsed game data - Round: {game_data.round}, Player Position: ({game_data.playerPosition.x}, {game_data.playerPosition.y}, {game_data.playerPosition.z}), Targets count: {len(game_data.targets)}")
                return game_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON data: {e}")
                return None
            except KeyError as e:
                logger.error(f"Missing required field in JSON data: {e}")
                return None
            except Exception as e:
                logger.error(f"Failed to create GameData object: {e}")
                return None
                
        except socket.timeout:
            # 超时是正常的，用于检查是否需要退出
            return None
        except Exception as e:
            logger.error(f"Error receiving UDP data: {e}")
            return None
    
    def stop(self):
        """停止UDP服务器"""
        if self.socket:
            self.socket.close()
            logger.info("UDP server stopped")
            self.socket = None
    
    def is_running(self) -> bool:
        """检查服务器是否正在运行"""
        return self.socket is not None

