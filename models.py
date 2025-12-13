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
            target = Target(
                id=target_data['id'],
                angle=target_data['angle'],
                distance=target_data['distance'],
                type=target_data['type'],
                position=target_pos
            )
            targets.append(target)
        
        return cls(
            round=data['round'],
            playerPosition=player_pos,
            targets=targets
        )

