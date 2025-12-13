"""威胁评估算法模块"""
import logging
from typing import Optional
from models import Target, GameData

logger = logging.getLogger(__name__)


def calculate_threat_score(target: Target, player_pos) -> float:
    """
    计算单个目标的威胁度
    
    Args:
        target: 目标对象
        player_pos: 玩家位置（当前未使用，但保留接口）
    
    Returns:
        威胁度分数，分数越高威胁越大
    """
    # 距离因子（距离越近威胁越大）
    # 使用反比例关系，避免除零错误
    distance_factor = 1.0 / (target.distance + 1)
    
    # 角度因子（角度越小威胁越大，0度正前方）
    # 将角度转换为绝对值，正前方（0度）威胁最大
    angle_factor = 1.0 / (abs(target.angle) + 1)
    
    # 类型因子（Tank=2.0, Soldier=1.0）
    type_factor = 2.0 if target.type == "Tank" else 1.0
    
    # 综合威胁度
    threat_score = distance_factor * angle_factor * type_factor
    
    logger.debug(
        f"Target {target.id} ({target.type}): "
        f"distance={target.distance:.2f}, angle={target.angle:.2f}, "
        f"threat_score={threat_score:.4f}"
    )
    
    return threat_score


def find_most_threatening_target(game_data: GameData) -> Optional[Target]:
    """
    找出最有威胁的目标
    
    Args:
        game_data: 游戏数据对象
    
    Returns:
        最有威胁的目标对象，如果没有目标则返回None
    """
    if not game_data.targets:
        logger.warning("No targets found in game data")
        return None
    
    max_threat_score = -1
    most_threatening = None
    
    for target in game_data.targets:
        threat_score = calculate_threat_score(target, game_data.playerPosition)
        if threat_score > max_threat_score:
            max_threat_score = threat_score
            most_threatening = target
    
    if most_threatening:
        logger.info(
            f"Most threatening target: ID={most_threatening.id}, "
            f"Type={most_threatening.type}, "
            f"Distance={most_threatening.distance:.2f}, "
            f"Angle={most_threatening.angle:.2f}, "
            f"ThreatScore={max_threat_score:.4f}"
        )
    
    return most_threatening

