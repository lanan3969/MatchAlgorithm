"""方向计算和马达映射模块"""
import math
import logging
from models import Position

logger = logging.getLogger(__name__)

# 马达方向描述（从玩家视角，16个方向）
MOTOR_DIRECTIONS = {
    0: "正北 (0°)",
    1: "北偏东 (22.5°)",
    2: "东北 (45°)",
    3: "东偏北 (67.5°)",
    4: "正东 (90°)",
    5: "东偏南 (112.5°)",
    6: "东南 (135°)",
    7: "南偏东 (157.5°)",
    8: "正南 (180°)",
    9: "南偏西 (202.5°)",
    10: "西南 (225°)",
    11: "西偏南 (247.5°)",
    12: "正西 (270°)",
    13: "西偏北 (292.5°)",
    14: "西北 (315°)",
    15: "北偏西 (337.5°)"
}


def calculate_direction_angle(player_pos: Position, target_pos: Position) -> float:
    """
    计算目标相对于玩家的水平方向角度
    
    坐标系：
    - X轴正方向：右
    - Y轴正方向：上
    - Z轴正方向：前
    
    Args:
        player_pos: 玩家位置
        target_pos: 目标位置
    
    Returns:
        角度（0-360度），0度为正前方（Z+），顺时针递增
    """
    # 计算从玩家到目标的向量（忽略Y轴，只考虑水平面）
    dx = target_pos.x - player_pos.x  # 右方向分量
    dz = target_pos.z - player_pos.z  # 前方向分量
    
    # 使用atan2计算角度（返回弧度，范围-π到π）
    # atan2(x, z): x为右（X轴），z为前（Z轴）
    # 结果：0度为正前方，顺时针为正
    angle_rad = math.atan2(dx, dz)
    
    # 转换为度数
    angle_deg = math.degrees(angle_rad)
    
    # 转换为0-360度范围
    if angle_deg < 0:
        angle_deg += 360
    
    logger.debug(f"Direction calculation: dx={dx:.2f}, dz={dz:.2f}, angle={angle_deg:.2f}°")
    
    return angle_deg


def angle_to_motor_id(angle: float) -> int:
    """
    将角度映射到马达编号（0-15）
    
    马达布局（俯视图，顺时针，16个方向）：
    - 0号：0° ±11.25°（正北）
    - 1号：22.5° ±11.25°（北偏东）
    - 2号：45° ±11.25°（东北）
    - 3号：67.5° ±11.25°（东偏北）
    - 4号：90° ±11.25°（正东）
    - 5号：112.5° ±11.25°（东偏南）
    - 6号：135° ±11.25°（东南）
    - 7号：157.5° ±11.25°（南偏东）
    - 8号：180° ±11.25°（正南）
    - 9号：202.5° ±11.25°（南偏西）
    - 10号：225° ±11.25°（西南）
    - 11号：247.5° ±11.25°（西偏南）
    - 12号：270° ±11.25°（正西）
    - 13号：292.5° ±11.25°（西偏北）
    - 14号：315° ±11.25°（西北）
    - 15号：337.5° ±11.25°（北偏西）
    
    Args:
        angle: 角度（0-360度）
    
    Returns:
        马达编号（0-15）
    """
    # 归一化角度到 0-360
    angle = angle % 360
    # 每个马达覆盖 22.5 度
    # 使用 int((angle + 11.25) / 22.5) 来实现四舍五入效果
    motor_id = int((angle + 11.25) / 22.5) % 16
    
    logger.debug(f"Angle {angle:.2f}° mapped to motor {motor_id}")
    
    return motor_id


def get_motor_direction_description(motor_id: int) -> str:
    """
    获取马达方向的文字描述
    
    Args:
        motor_id: 马达编号（0-15）
    
    Returns:
        方向描述字符串
    """
    return MOTOR_DIRECTIONS.get(motor_id, f"未知方向 (马达{motor_id})")


def calculate_motor_for_target(player_pos: Position, target_pos: Position) -> tuple:
    """
    计算目标对应的马达编号和详细信息
    
    Args:
        player_pos: 玩家位置
        target_pos: 目标位置
    
    Returns:
        元组 (motor_id, angle, direction_description)
    """
    angle = calculate_direction_angle(player_pos, target_pos)
    motor_id = angle_to_motor_id(angle)
    direction_desc = get_motor_direction_description(motor_id)
    
    logger.info(
        f"Target direction analysis: angle={angle:.2f}°, "
        f"motor_id={motor_id}, direction={direction_desc}"
    )
    
    return motor_id, angle, direction_desc




