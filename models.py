"""数据模型定义模块"""
from dataclasses import dataclass
from typing import List


@dataclass
class Position:
    """位置坐标"""
    x: float
    y: float
    z: float


@dataclass
class Target:
    """敌人目标信息"""
    id: int
    angle: float
    distance: float
    type: str  # "Tank" or "Soldier"
    position: Position
    speed: float = 0.0          # 移动速度 (m/s)
    direction: float = 0.0      # 移动方向 (0-360度)
    velocity: Position = None   # 速度矢量（可选）


@dataclass
class GameData:
    """游戏数据"""
    round: int
    playerPosition: Position
    targets: List[Target]

    @classmethod
    def from_dict(cls, data: dict) -> 'GameData':
        """从字典创建GameData对象"""
        player_pos = Position(**data['playerPosition'])
        targets = []
        for target_data in data['targets']:
            target_pos = Position(**target_data['position'])
            
            # 解析速度矢量（如果存在）
            velocity = None
            if 'velocity' in target_data and target_data['velocity']:
                velocity = Position(**target_data['velocity'])
            
            target = Target(
                id=target_data['id'],
                angle=target_data['angle'],
                distance=target_data['distance'],
                type=target_data['type'],
                position=target_pos,
                speed=target_data.get('speed', 0.0),       # 向后兼容
                direction=target_data.get('direction', 0.0),  # 向后兼容
                velocity=velocity
            )
            targets.append(target)
        
        return cls(
            round=data['round'],
            playerPosition=player_pos,
            targets=targets
        )

