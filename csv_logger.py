"""CSV日志记录模块"""
import csv
import logging
import os
from datetime import datetime
from typing import Optional, List
from models import Target

logger = logging.getLogger(__name__)


class CSVLogger:
    """CSV日志记录器，用于记录实验数据"""
    
    def __init__(self, base_dir: str = "logs"):
        """
        初始化CSV日志记录器
        
        Args:
            base_dir: 日志文件存储目录，默认为 "logs"
        """
        self.base_dir = base_dir
        self.csv_file = None
        self.csv_writer = None
        self.file_path = None
        
        # 创建日志目录
        self._create_log_directory()
        
        # 创建CSV文件
        self._create_csv_file()
    
    def _create_log_directory(self):
        """创建日志目录（如果不存在）"""
        try:
            if not os.path.exists(self.base_dir):
                os.makedirs(self.base_dir)
                logger.info(f"Created log directory: {self.base_dir}")
        except Exception as e:
            logger.error(f"Failed to create log directory: {e}")
            raise
    
    def _create_csv_file(self):
        """创建带时间戳的CSV文件并写入列头"""
        try:
            # 生成文件名（使用时间戳）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.file_path = os.path.join(self.base_dir, f"experiment_{timestamp}.csv")
            
            # 打开文件
            self.csv_file = open(self.file_path, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.csv_file)
            
            # 写入列头
            headers = [
                'timestamp',
                'round',
                'threat_enemy_id',
                'threat_enemy_type',
                'threat_enemy_distance',
                'threat_enemy_angle',
                'threat_enemy_x',
                'threat_enemy_y',
                'threat_enemy_z',
                'north_threat',              # 0
                'north_northeast_threat',    # 1
                'northeast_threat',          # 2
                'east_northeast_threat',     # 3
                'east_threat',               # 4
                'east_southeast_threat',     # 5
                'southeast_threat',          # 6
                'south_southeast_threat',    # 7
                'south_threat',              # 8
                'south_southwest_threat',    # 9
                'southwest_threat',          # 10
                'west_southwest_threat',     # 11
                'west_threat',               # 12
                'west_northwest_threat',     # 13
                'northwest_threat',          # 14
                'north_northwest_threat'     # 15
            ]
            self.csv_writer.writerow(headers)
            self.csv_file.flush()
            
            logger.info("=" * 60)
            logger.info("📊 CSV Logger initialized")
            logger.info(f"  File path: {self.file_path}")
            logger.info(f"  Columns: {len(headers)}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Failed to create CSV file: {e}")
            raise
    
    def log_round_data(
        self,
        round_number: str,
        most_threatening_target: Optional[Target],
        direction_threats  # 可以是字典或列表
    ):
        """
        记录每轮的数据到CSV
        
        Args:
            round_number: 轮次编号（如 "1-1"）
            most_threatening_target: 最具威胁的目标对象，如果没有则为None
            direction_threats: 16个方向的威胁值（字典{0-15: float}或列表）
        """
        if not self.csv_writer or not self.csv_file:
            logger.error("CSV logger is not initialized")
            return
        
        try:
            # 生成时间戳（精确到毫秒）
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # 提取威胁目标信息
            if most_threatening_target:
                threat_id = most_threatening_target.id
                threat_type = most_threatening_target.type
                threat_distance = round(most_threatening_target.distance, 2)
                threat_angle = round(most_threatening_target.angle, 2)
                threat_x = round(most_threatening_target.position.x, 2)
                threat_y = round(most_threatening_target.position.y, 2)
                threat_z = round(most_threatening_target.position.z, 2)
            else:
                threat_id = "N/A"
                threat_type = "N/A"
                threat_distance = "N/A"
                threat_angle = "N/A"
                threat_x = "N/A"
                threat_y = "N/A"
                threat_z = "N/A"
            
            # 处理direction_threats（可以是字典或列表）
            if isinstance(direction_threats, dict):
                # 如果是字典，按方向ID（0-15）排序提取值
                direction_threats_list = [direction_threats.get(i, 0.0) for i in range(16)]
            else:
                # 如果是列表，直接使用
                direction_threats_list = list(direction_threats)
            
            # 确保有16个方向的威胁值
            if len(direction_threats_list) < 16:
                logger.warning(f"Expected 16 direction threats, got {len(direction_threats_list)}")
                direction_threats_list = direction_threats_list + [0.0] * (16 - len(direction_threats_list))
            
            # 四舍五入威胁值到3位小数
            direction_threats_rounded = [round(t, 3) for t in direction_threats_list[:16]]
            
            # 写入数据行
            row = [
                timestamp,
                round_number,
                threat_id,
                threat_type,
                threat_distance,
                threat_angle,
                threat_x,
                threat_y,
                threat_z,
            ] + direction_threats_rounded
            
            self.csv_writer.writerow(row)
            self.csv_file.flush()  # 立即写入磁盘
            
            logger.debug(f"CSV: Logged data for round {round_number}")
            
        except Exception as e:
            logger.error(f"Failed to write to CSV file: {e}")
            # 不抛出异常，避免中断主程序
    
    def check_round_exists(self, round_number: str) -> bool:
        """
        检查CSV文件中是否已存在该round的记录
        
        Args:
            round_number: 轮次编号（如 "1-1"）
        
        Returns:
            如果round已存在返回True，否则返回False
        """
        if not self.file_path or not os.path.exists(self.file_path):
            return False
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('round') == round_number:
                        return True
            return False
        except Exception as e:
            logger.error(f"Error checking round existence: {e}")
            return False
    
    def read_round_data(self, round_number: str) -> Optional[dict]:
        """
        从CSV读取指定round的数据
        
        Args:
            round_number: 轮次编号（如 "1-1"）
        
        Returns:
            包含该round数据的字典，如果round不存在则返回None
            字典包含：threat_enemy_id, threat_enemy_type, threat_enemy_distance,
                    threat_enemy_angle, threat_enemy_x, threat_enemy_y, threat_enemy_z,
                    direction_threats (list of 16 floats)
        """
        if not self.file_path or not os.path.exists(self.file_path):
            logger.warning(f"CSV file does not exist: {self.file_path}")
            return None
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('round') == round_number:
                        # 提取16个方向的威胁值
                        direction_threats = [
                            float(row.get('north_threat', 0.0)),              # 0
                            float(row.get('north_northeast_threat', 0.0)),    # 1
                            float(row.get('northeast_threat', 0.0)),          # 2
                            float(row.get('east_northeast_threat', 0.0)),     # 3
                            float(row.get('east_threat', 0.0)),               # 4
                            float(row.get('east_southeast_threat', 0.0)),     # 5
                            float(row.get('southeast_threat', 0.0)),          # 6
                            float(row.get('south_southeast_threat', 0.0)),    # 7
                            float(row.get('south_threat', 0.0)),              # 8
                            float(row.get('south_southwest_threat', 0.0)),    # 9
                            float(row.get('southwest_threat', 0.0)),          # 10
                            float(row.get('west_southwest_threat', 0.0)),     # 11
                            float(row.get('west_threat', 0.0)),               # 12
                            float(row.get('west_northwest_threat', 0.0)),     # 13
                            float(row.get('northwest_threat', 0.0)),          # 14
                            float(row.get('north_northwest_threat', 0.0))     # 15
                        ]
                        
                        # 构建返回数据
                        data = {
                            'round': round_number,
                            'threat_enemy_id': row.get('threat_enemy_id'),
                            'threat_enemy_type': row.get('threat_enemy_type'),
                            'threat_enemy_distance': row.get('threat_enemy_distance'),
                            'threat_enemy_angle': row.get('threat_enemy_angle'),
                            'threat_enemy_x': row.get('threat_enemy_x'),
                            'threat_enemy_y': row.get('threat_enemy_y'),
                            'threat_enemy_z': row.get('threat_enemy_z'),
                            'direction_threats': direction_threats
                        }
                        
                        logger.debug(f"CSV: Read data for round {round_number}")
                        return data
            
            logger.warning(f"Round {round_number} not found in CSV")
            return None
            
        except Exception as e:
            logger.error(f"Error reading round data: {e}")
            return None
    
    def close(self):
        """关闭CSV文件"""
        if self.csv_file:
            try:
                self.csv_file.close()
                logger.info(f"CSV log file closed: {self.file_path}")
            except Exception as e:
                logger.error(f"Error closing CSV file: {e}")
    
    def __enter__(self):
        """支持with语句"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持with语句"""
        self.close()
        return False

