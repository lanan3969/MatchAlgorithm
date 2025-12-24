"""态势感知模块 - 计算八个方向的威胁度"""
import math
import logging
from typing import Dict, Tuple, List
from models import Target, GameData, Position
from direction_mapper import calculate_direction_angle, angle_to_motor_id

logger = logging.getLogger(__name__)

# 方向角度范围（每个方向覆盖22.5度）
DIRECTION_RANGES = {
    0: (348.75, 11.25),    # 正北 (0° ±11.25°)
    1: (11.25, 33.75),     # 北偏东 (22.5° ±11.25°)
    2: (33.75, 56.25),     # 东北 (45° ±11.25°)
    3: (56.25, 78.75),     # 东偏北 (67.5° ±11.25°)
    4: (78.75, 101.25),    # 正东 (90° ±11.25°)
    5: (101.25, 123.75),   # 东偏南 (112.5° ±11.25°)
    6: (123.75, 146.25),   # 东南 (135° ±11.25°)
    7: (146.25, 168.75),   # 南偏东 (157.5° ±11.25°)
    8: (168.75, 191.25),   # 正南 (180° ±11.25°)
    9: (191.25, 213.75),   # 南偏西 (202.5° ±11.25°)
    10: (213.75, 236.25),  # 西南 (225° ±11.25°)
    11: (236.25, 258.75),  # 西偏南 (247.5° ±11.25°)
    12: (258.75, 281.25),  # 正西 (270° ±11.25°)
    13: (281.25, 303.75),  # 西偏北 (292.5° ±11.25°)
    14: (303.75, 326.25),  # 西北 (315° ±11.25°)
    15: (326.25, 348.75)   # 北偏西 (337.5° ±11.25°)
}

# 类型威胁因子
TYPE_THREAT_FACTOR = {
    "Tank": 2.0,
    "tank": 2.0,
    "Soldier": 1.0,
    "soldier": 1.0
}

# 最大速度（用于归一化速度因子，单位：米/秒）
MAX_VELOCITY = 20.0


def normalize_angle(angle: float) -> float:
    """
    将角度归一化到0-360度范围
    
    Args:
        angle: 角度（度）
    
    Returns:
        归一化后的角度（0-360度）
    """
    while angle < 0:
        angle += 360
    while angle >= 360:
        angle -= 360
    return angle


def is_angle_in_range(angle: float, range_start: float, range_end: float) -> bool:
    """
    判断角度是否在指定范围内（考虑跨越0度的情况）
    
    Args:
        angle: 要判断的角度（0-360度）
        range_start: 范围起始角度
        range_end: 范围结束角度
    
    Returns:
        是否在范围内
    """
    angle = normalize_angle(angle)
    range_start = normalize_angle(range_start)
    range_end = normalize_angle(range_end)
    
    if range_start <= range_end:
        # 正常情况，不跨越0度
        return range_start <= angle < range_end
    else:
        # 跨越0度的情况（如337.5-22.5）
        return angle >= range_start or angle < range_end


def calculate_target_threat_score(
    target: Target,
    player_pos: Position,
    direction_angle: float
) -> float:
    """
    计算单个目标对特定方向的威胁度
    
    Args:
        target: 目标对象
        player_pos: 玩家位置
        direction_angle: 目标方向的角度（0-360度）
    
    Returns:
        威胁度分数
    """
    # 1. 距离因子：距离越近威胁越大
    distance_factor = 1.0 / (target.distance + 1)
    
    # 2. 角度因子：计算目标相对于该方向的角度偏移
    target_angle = calculate_direction_angle(player_pos, target.position)
    angle_offset = abs(target_angle - direction_angle)
    # 考虑最短角度差（可能跨越0度）
    if angle_offset > 180:
        angle_offset = 360 - angle_offset
    angle_factor = 1.0 / (angle_offset + 1)
    
    # 3. 类型因子
    type_factor = TYPE_THREAT_FACTOR.get(target.type, 1.0)
    
    # 4. 速度因子：速度越快威胁越大（如果有速度信息）
    velocity_factor = 1.0
    if target.velocity is not None and target.velocity > 0:
        # 归一化速度（0-1范围）
        normalized_velocity = min(target.velocity / MAX_VELOCITY, 1.0)
        velocity_factor = 0.5 + 0.5 * normalized_velocity  # 范围：0.5-1.0
    
    # 5. 移动方向因子：如果敌人朝向玩家移动，威胁度更高
    movement_factor = 1.0
    if target.direction is not None and target.velocity is not None and target.velocity > 0:
        # 计算敌人移动方向与指向玩家方向的夹角
        enemy_to_player_angle = target_angle
        enemy_movement_angle = normalize_angle(target.direction)
        
        # 计算角度差
        angle_diff = abs(enemy_movement_angle - enemy_to_player_angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        # 如果敌人朝向玩家移动（角度差小于90度），威胁度增加
        if angle_diff < 90:
            # 角度差越小，威胁度越高
            movement_factor = 1.0 + 0.5 * (1.0 - angle_diff / 90.0)  # 范围：1.0-1.5
        else:
            # 敌人远离玩家，威胁度降低
            movement_factor = 0.8
    
    # 综合威胁度
    threat_score = distance_factor * angle_factor * type_factor * velocity_factor * movement_factor
    
    logger.debug(
        f"Target {target.id} ({target.type}) threat to direction {direction_angle:.1f}°: "
        f"distance={target.distance:.2f}, angle_offset={angle_offset:.1f}°, "
        f"velocity={target.velocity or 'N/A'}, movement_factor={movement_factor:.2f}, "
        f"threat_score={threat_score:.4f}"
    )
    
    return threat_score


def calculate_direction_threat_score(
    game_data: GameData,
    direction_id: int
) -> float:
    """
    计算特定方向的综合威胁度
    
    Args:
        game_data: 游戏数据对象
        direction_id: 方向ID（0-15）
    
    Returns:
        该方向的综合威胁度分数
    """
    if direction_id < 0 or direction_id > 15:
        logger.warning(f"Invalid direction_id: {direction_id}")
        return 0.0
    
    # 获取该方向的角度范围
    range_start, range_end = DIRECTION_RANGES[direction_id]
    direction_center_angle = direction_id * 22.5  # 方向中心角度
    
    total_threat = 0.0
    target_count = 0
    
    # 遍历所有目标，累加该方向范围内的威胁度
    for target in game_data.targets:
        # 计算目标相对于玩家的方向角度
        target_angle = calculate_direction_angle(game_data.playerPosition, target.position)
        
        # 判断目标是否在该方向范围内
        if is_angle_in_range(target_angle, range_start, range_end):
            target_count += 1
            threat_score = calculate_target_threat_score(
                target,
                game_data.playerPosition,
                direction_center_angle
            )
            total_threat += threat_score
    
    # 数量因子：同一方向的敌人越多，威胁度越高（但不是线性增长）
    count_factor = 1.0 + 0.2 * min(target_count, 5)  # 最多5个敌人时达到2.0倍
    
    final_threat = total_threat * count_factor
    
    logger.debug(
        f"Direction {direction_id} ({direction_center_angle:.1f}°): "
        f"target_count={target_count}, total_threat={total_threat:.4f}, "
        f"count_factor={count_factor:.2f}, final_threat={final_threat:.4f}"
    )
    
    return final_threat


def calculate_all_directions_threat(
    game_data: GameData
) -> Dict[int, float]:
    """
    计算所有16个方向的威胁度
    
    Args:
        game_data: 游戏数据对象
    
    Returns:
        字典，键为方向ID（0-15），值为威胁度分数
    """
    direction_threats = {}
    
    for direction_id in range(16):
        threat_score = calculate_direction_threat_score(game_data, direction_id)
        direction_threats[direction_id] = threat_score
    
    return direction_threats


def normalize_threat_to_intensity(
    threat_scores: Dict[int, float],
    min_intensity: int = 80,
    max_intensity: int = 255,
    threshold: float = 0.01
) -> Dict[int, int]:
    """
    将威胁度分数归一化并映射到震动强度（0-255）
    
    Args:
        threat_scores: 各方向的威胁度分数字典
        min_intensity: 最小可感知震动强度，默认80（低于此值几乎感觉不到）
        max_intensity: 最大震动强度，默认255
        threshold: 威胁度阈值，低于此值不震动
    
    Returns:
        字典，键为方向ID（0-15），值为震动强度（0或min_intensity-max_intensity）
    
    说明：
        - 威胁度 < threshold：不震动（intensity = 0）
        - 威胁度 >= threshold：映射到 [min_intensity, max_intensity] 范围
        - 这样确保所有有效震动都能被用户感知到
    """
    if not threat_scores:
        return {i: 0 for i in range(16)}
    
    # 找到最大威胁度（用于归一化）
    max_threat = max(threat_scores.values()) if threat_scores.values() else 0.0
    
    if max_threat <= 0:
        return {i: 0 for i in range(16)}
    
    # 归一化并映射到震动强度
    intensities = {}
    for direction_id in range(16):
        threat = threat_scores.get(direction_id, 0.0)
        
        if threat < threshold:
            # 威胁度太低，不震动
            intensities[direction_id] = 0
        else:
            # 归一化到0-1范围，然后映射到min_intensity-max_intensity
            # 确保所有有效震动都在可感知范围内
            normalized = threat / max_threat
            intensity = int(min_intensity + normalized * (max_intensity - min_intensity))
            intensities[direction_id] = intensity
    
    logger.info("=" * 60)
    logger.info("🎯 Situation Awareness - Direction Threat Analysis")
    logger.info("=" * 60)
    
    direction_names = [
        "正北", "北偏东", "东北", "东偏北",
        "正东", "东偏南", "东南", "南偏东",
        "正南", "南偏西", "西南", "西偏南",
        "正西", "西偏北", "西北", "北偏西"
    ]
    
    for direction_id in range(16):
        threat = threat_scores.get(direction_id, 0.0)
        intensity = intensities.get(direction_id, 0)
        direction_name = direction_names[direction_id]
        logger.info(
            f"  Direction {direction_id} ({direction_name}): "
            f"Threat={threat:.4f}, Intensity={intensity}"
        )
    logger.info("=" * 60)
    
    return intensities

