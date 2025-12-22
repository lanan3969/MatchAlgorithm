"""
威胁指标量化处理模块

基于论文《地面作战目标威胁评估多属性指标处理方法》
实现6个核心威胁指标的IFS量化方法：
1. 目标距离 (Distance)
2. 目标速度 (Velocity)
3. 攻击角度 (Attack Angle)
4. 目标类型 (Target Type)
5. 通视条件 (Visibility)
6. 作战环境 (Environment)
"""

import numpy as np
import math
from typing import Dict, Tuple
from ifs_core import IFS, IFSConverter


class ThreatIndicators:
    """威胁指标评估类"""
    
    def __init__(self):
        """初始化指标参数"""
        self.converter = IFSConverter()
        
        # 距离分段阈值（米）
        self.distance_thresholds = {
            'critical': 10,    # 极高威胁区域
            'high': 20,        # 高威胁区域
            'medium': 35,      # 中威胁区域
            'low': 50          # 低威胁区域
        }
        
        # 速度阈值（m/s）
        self.speed_thresholds = {
            'soldier': {
                'high': 5.0,    # 士兵高速阈值
                'medium': 2.0   # 士兵中速阈值
            },
            'ifv': {
                'high': 10.0,   # IFV高速阈值
                'medium': 5.0   # IFV中速阈值
            }
        }
        
        # 角度阈值（度）
        self.angle_thresholds = {
            'direct': 30,      # 直接朝向
            'oblique': 90,     # 斜向
            'lateral': 150     # 侧向
        }
    
    def evaluate_distance(self, distance: float) -> Dict:
        """
        指标1：目标距离评估
        
        论文方法：使用分段函数和高斯隶属度
        - 距离越近，威胁越高
        - 考虑不同距离段的威胁特性
        
        Args:
            distance: 目标距离（米）
        
        Returns:
            {
                'ifs': IFS对象,
                'threat_score': float,
                'threat_level': str,
                'distance': float,
                'zone': str  # 'critical', 'high', 'medium', 'low'
            }
        """
        # 确定距离区域
        if distance <= self.distance_thresholds['critical']:
            zone = 'critical'
            # 极近距离：极高威胁
            ifs = self.converter.from_real_number(
                value=distance,
                ideal=0,
                tolerance=5,
                min_val=0,
                max_val=self.distance_thresholds['critical']
            )
            # 增强威胁度
            ifs = IFS(mu=min(0.95, ifs.mu + 0.15), nu=max(0.02, ifs.nu - 0.1))
            
        elif distance <= self.distance_thresholds['high']:
            zone = 'high'
            # 近距离：高威胁
            ifs = self.converter.from_real_number(
                value=distance,
                ideal=self.distance_thresholds['critical'],
                tolerance=5,
                min_val=self.distance_thresholds['critical'],
                max_val=self.distance_thresholds['high']
            )
            ifs = IFS(mu=min(0.85, ifs.mu + 0.1), nu=max(0.05, ifs.nu - 0.05))
            
        elif distance <= self.distance_thresholds['medium']:
            zone = 'medium'
            # 中距离：中威胁
            ifs = self.converter.from_real_number(
                value=distance,
                ideal=self.distance_thresholds['high'],
                tolerance=7,
                min_val=self.distance_thresholds['high'],
                max_val=self.distance_thresholds['medium']
            )
            
        else:
            zone = 'low'
            # 远距离：低威胁
            # 威胁度随距离增加而递减
            decay_factor = math.exp(-(distance - self.distance_thresholds['medium']) / 15)
            mu = max(0.1, 0.4 * decay_factor)
            nu = min(0.8, 0.5 + (1 - decay_factor) * 0.3)
            ifs = IFS(mu=mu, nu=nu)
        
        threat_score = ifs.score()
        
        # 确定威胁等级
        if threat_score >= 0.7:
            threat_level = 'critical'
        elif threat_score >= 0.4:
            threat_level = 'high'
        elif threat_score >= 0.0:
            threat_level = 'medium'
        else:
            threat_level = 'low'
        
        return {
            'ifs': ifs,
            'threat_score': threat_score,
            'threat_level': threat_level,
            'distance': distance,
            'zone': zone,
            'description': f"{zone}区域，距离{distance:.1f}米"
        }
    
    def evaluate_speed(self, speed: float, enemy_type: str) -> Dict:
        """
        指标2：目标速度评估
        
        论文方法：考虑目标类型和移动速度
        - 高速运动 → 可能是攻击意图 → 高威胁
        - 低速/静止 → 可能是巡逻/防守 → 低威胁
        
        Args:
            speed: 移动速度（m/s）
            enemy_type: 敌人类型 ('soldier' 或 'ifv')
        
        Returns:
            {
                'ifs': IFS对象,
                'threat_score': float,
                'threat_level': str,
                'speed': float,
                'speed_category': str
            }
        """
        # 获取对应类型的速度阈值
        thresholds = self.speed_thresholds.get(enemy_type, self.speed_thresholds['soldier'])
        
        # 分类速度等级
        if speed >= thresholds['high']:
            speed_category = 'high_speed'
            # 高速运动：高威胁（可能是冲锋/攻击）
            # 超出阈值越多，威胁越大
            excess_ratio = min(2.0, speed / thresholds['high'])
            mu = min(0.9, 0.65 + 0.25 * (excess_ratio - 1))
            nu = max(0.05, 0.25 - 0.2 * (excess_ratio - 1))
            ifs = IFS(mu=mu, nu=nu)
            
        elif speed >= thresholds['medium']:
            speed_category = 'medium_speed'
            # 中速运动：中等威胁（可能是机动）
            ifs = self.converter.from_real_number(
                value=speed,
                ideal=thresholds['high'],
                tolerance=thresholds['medium'],
                min_val=0,
                max_val=thresholds['high'] * 1.5
            )
            
        elif speed >= 0.5:
            speed_category = 'low_speed'
            # 低速运动：低威胁（可能是巡逻）
            mu = 0.3 + 0.2 * (speed / thresholds['medium'])
            nu = 0.6 - 0.3 * (speed / thresholds['medium'])
            ifs = IFS(mu=mu, nu=nu)
            
        else:
            speed_category = 'static'
            # 静止/极慢：低威胁但有不确定性（可能是埋伏）
            ifs = IFS(mu=0.25, nu=0.50)  # 保留较高的犹豫度
        
        threat_score = ifs.score()
        
        # 确定威胁等级
        if threat_score >= 0.5:
            threat_level = 'high'
        elif threat_score >= 0.1:
            threat_level = 'medium'
        else:
            threat_level = 'low'
        
        return {
            'ifs': ifs,
            'threat_score': threat_score,
            'threat_level': threat_level,
            'speed': speed,
            'speed_category': speed_category,
            'enemy_type': enemy_type,
            'description': f"{speed_category}，{speed:.1f}m/s"
        }
    
    def evaluate_attack_angle(self, enemy_direction: float, 
                             enemy_pos: Tuple[float, float],
                             player_pos: Tuple[float, float] = (0, 0)) -> Dict:
        """
        指标3：攻击角度评估
        
        论文方法：分析敌人移动方向与玩家位置的关系
        - 敌人朝向玩家 → 高威胁（可能是进攻）
        - 敌人背向玩家 → 低威胁（可能是撤退）
        
        Args:
            enemy_direction: 敌人移动方向（度，0-360）
            enemy_pos: 敌人位置 (x, z)
            player_pos: 玩家位置 (x, z)，默认(0, 0)
        
        Returns:
            {
                'ifs': IFS对象,
                'threat_score': float,
                'threat_level': str,
                'angle_to_player': float,
                'angle_diff': float,
                'direction_category': str
            }
        """
        # 计算从敌人到玩家的方位角
        dx = player_pos[0] - enemy_pos[0]
        dz = player_pos[1] - enemy_pos[1]
        angle_to_player = math.degrees(math.atan2(dz, dx))
        
        # 标准化到[0, 360)
        if angle_to_player < 0:
            angle_to_player += 360
        
        # 计算角度差（敌人移动方向与朝向玩家方向的夹角）
        angle_diff = abs((enemy_direction - angle_to_player + 180) % 360 - 180)
        
        # 根据角度差评估威胁
        if angle_diff <= self.angle_thresholds['direct']:
            direction_category = 'approaching'  # 正面接近
            # 直接朝向玩家：极高威胁
            # 角度差越小，威胁越大
            mu = 0.95 - 0.15 * (angle_diff / self.angle_thresholds['direct'])
            nu = 0.02 + 0.08 * (angle_diff / self.angle_thresholds['direct'])
            ifs = IFS(mu=mu, nu=nu)
            
        elif angle_diff <= self.angle_thresholds['oblique']:
            direction_category = 'flanking'  # 侧向包抄
            # 斜向接近：高威胁
            relative_angle = (angle_diff - self.angle_thresholds['direct']) / \
                           (self.angle_thresholds['oblique'] - self.angle_thresholds['direct'])
            mu = 0.8 - 0.3 * relative_angle
            nu = 0.1 + 0.3 * relative_angle
            ifs = IFS(mu=mu, nu=nu)
            
        elif angle_diff <= self.angle_thresholds['lateral']:
            direction_category = 'lateral'  # 侧向移动
            # 侧向：中等威胁（可能是机动）
            relative_angle = (angle_diff - self.angle_thresholds['oblique']) / \
                           (self.angle_thresholds['lateral'] - self.angle_thresholds['oblique'])
            mu = 0.5 - 0.2 * relative_angle
            nu = 0.4 + 0.2 * relative_angle
            ifs = IFS(mu=mu, nu=nu)
            
        else:
            direction_category = 'retreating'  # 撤退
            # 背向玩家：低威胁
            retreat_factor = (angle_diff - self.angle_thresholds['lateral']) / \
                           (180 - self.angle_thresholds['lateral'])
            mu = 0.3 - 0.2 * retreat_factor
            nu = 0.6 + 0.2 * retreat_factor
            ifs = IFS(mu=mu, nu=nu)
        
        threat_score = ifs.score()
        
        # 确定威胁等级
        if threat_score >= 0.6:
            threat_level = 'high'
        elif threat_score >= 0.2:
            threat_level = 'medium'
        else:
            threat_level = 'low'
        
        return {
            'ifs': ifs,
            'threat_score': threat_score,
            'threat_level': threat_level,
            'angle_to_player': angle_to_player,
            'angle_diff': angle_diff,
            'direction_category': direction_category,
            'description': f"{direction_category}，角度差{angle_diff:.1f}°"
        }
    
    def evaluate_target_type(self, enemy_type: str) -> Dict:
        """
        指标4：目标类型评估
        
        论文方法：使用模糊评价语言转IFS
        - IFV（步兵战车）：装甲厚、火力强 → 高威胁
        - Soldier（士兵）：单兵作战 → 中等威胁
        
        Args:
            enemy_type: 敌人类型 ('soldier', 'ifv', 'tank')
        
        Returns:
            {
                'ifs': IFS对象,
                'threat_score': float,
                'threat_level': str,
                'type': str,
                'type_name': str
            }
        """
        enemy_type_lower = enemy_type.lower().strip()
        
        # 根据类型分配IFS值（基于战斗力和生存能力）
        type_mapping = {
            'ifv': {
                'ifs': IFS(0.90, 0.05),  # 步兵战车：高威胁
                'name': '步兵战车',
                'level': 'high'
            },
            'tank': {
                'ifs': IFS(0.90, 0.05),  # 坦克：高威胁
                'name': '坦克',
                'level': 'high'
            },
            'soldier': {
                'ifs': IFS(0.60, 0.30),  # 士兵：中等威胁
                'name': '士兵',
                'level': 'medium'
            },
            'armed_personnel': {
                'ifs': IFS(0.50, 0.40),  # 武装人员：中低威胁
                'name': '武装人员',
                'level': 'medium'
            }
        }
        
        # 获取类型信息
        type_info = type_mapping.get(enemy_type_lower, {
            'ifs': IFS(0.55, 0.35),  # 默认：中等威胁
            'name': '未知类型',
            'level': 'medium'
        })
        
        ifs = type_info['ifs']
        threat_score = ifs.score()
        
        return {
            'ifs': ifs,
            'threat_score': threat_score,
            'threat_level': type_info['level'],
            'type': enemy_type,
            'type_name': type_info['name'],
            'description': f"{type_info['name']}({type_info['level']}威胁)"
        }
    
    def evaluate_visibility(self, is_blocked: bool, 
                           blocking_count: int = 0,
                           visibility_ratio: float = None) -> Dict:
        """
        指标5：通视条件评估
        
        论文方法：考虑射线遮挡情况
        - 无遮挡：清晰可见 → 高威胁（易被发现和打击）
        - 有遮挡：视线受阻 → 低威胁但不确定性高
        
        Args:
            is_blocked: 是否被遮挡
            blocking_count: 遮挡物数量
            visibility_ratio: 可见度比例 [0, 1]，None表示完全可见或完全遮挡
        
        Returns:
            {
                'ifs': IFS对象,
                'threat_score': float,
                'threat_level': str,
                'is_blocked': bool,
                'visibility_ratio': float
            }
        """
        if visibility_ratio is not None:
            # 使用精确的可见度比例
            vis = visibility_ratio
        else:
            # 根据遮挡状态估算
            vis = 0.0 if is_blocked else 1.0
        
        if not is_blocked or vis > 0.7:
            # 无遮挡或轻微遮挡：高威胁
            mu = 0.85 - 0.1 * (1 - vis)
            nu = 0.10 + 0.1 * (1 - vis)
            ifs = IFS(mu=mu, nu=nu)
            threat_level = 'high'
            
        elif vis > 0.3:
            # 部分遮挡：中等威胁，不确定性增加
            mu = 0.45 + 0.25 * vis
            nu = 0.35 - 0.15 * vis
            ifs = IFS(mu=mu, nu=nu)  # 犹豫度会相对较高
            threat_level = 'medium'
            
        else:
            # 严重遮挡或完全遮挡：低威胁，高不确定性
            # 考虑遮挡物数量的影响
            uncertainty_factor = min(0.3, 0.1 + blocking_count * 0.05)
            mu = 0.30 - uncertainty_factor
            nu = 0.50
            ifs = IFS(mu=mu, nu=nu)  # 保持较高犹豫度
            threat_level = 'low'
        
        threat_score = ifs.score()
        
        return {
            'ifs': ifs,
            'threat_score': threat_score,
            'threat_level': threat_level,
            'is_blocked': is_blocked,
            'visibility_ratio': vis,
            'blocking_count': blocking_count,
            'description': f"{'遮挡' if is_blocked else '无遮挡'}，可见度{vis*100:.0f}%"
        }
    
    def evaluate_environment(self, obstacle_density: float,
                            building_density: float = 0.0,
                            complexity_level: str = None) -> Dict:
        """
        指标6：作战环境评估
        
        论文方法：分析目标周围的环境复杂度
        - 开阔地带：敌人易暴露 → 高威胁（对我方有利）
        - 复杂地形：掩体多，难预测 → 中低威胁但不确定性高
        
        Args:
            obstacle_density: 障碍物密度 [0, 1]
            building_density: 建筑物密度 [0, 1]
            complexity_level: 复杂度等级 ('open', 'moderate', 'complex')
        
        Returns:
            {
                'ifs': IFS对象,
                'threat_score': float,
                'threat_level': str,
                'obstacle_density': float,
                'complexity_level': str
            }
        """
        # 计算综合环境复杂度
        total_density = (obstacle_density + building_density) / 2.0
        
        # 自动判断复杂度等级
        if complexity_level is None:
            if total_density < 0.3:
                complexity_level = 'open'
            elif total_density < 0.6:
                complexity_level = 'moderate'
            else:
                complexity_level = 'complex'
        
        if complexity_level == 'open':
            # 开阔地带：敌人暴露，高威胁（便于观察和打击）
            mu = 0.70 - 0.2 * total_density
            nu = 0.20 + 0.1 * total_density
            ifs = IFS(mu=mu, nu=nu)
            threat_level = 'high'
            
        elif complexity_level == 'moderate':
            # 适度复杂：中等威胁
            mu = 0.50 - 0.1 * (total_density - 0.3)
            nu = 0.35 + 0.1 * (total_density - 0.3)
            ifs = IFS(mu=mu, nu=nu)
            threat_level = 'medium'
            
        else:  # complex
            # 复杂地形：低威胁，高不确定性（难以预测）
            mu = 0.40 - 0.15 * total_density
            nu = 0.30 + 0.1 * total_density
            ifs = IFS(mu=mu, nu=nu)  # 犹豫度较高
            threat_level = 'low'
        
        threat_score = ifs.score()
        
        return {
            'ifs': ifs,
            'threat_score': threat_score,
            'threat_level': threat_level,
            'obstacle_density': obstacle_density,
            'building_density': building_density,
            'total_density': total_density,
            'complexity_level': complexity_level,
            'description': f"{complexity_level}环境，密度{total_density*100:.0f}%"
        }


if __name__ == "__main__":
    # 测试代码
    print("=" * 70)
    print("威胁指标量化处理测试")
    print("=" * 70)
    
    indicators = ThreatIndicators()
    
    # 测试1：距离指标
    print("\n【测试1】距离指标评估：")
    for dist in [5, 15, 25, 40]:
        result = indicators.evaluate_distance(dist)
        print(f"距离{dist}m: {result['ifs']} - {result['threat_level']} - {result['zone']}")
    
    # 测试2：速度指标
    print("\n【测试2】速度指标评估：")
    for speed, etype in [(8, 'soldier'), (15, 'ifv'), (2, 'soldier')]:
        result = indicators.evaluate_speed(speed, etype)
        print(f"{etype} {speed}m/s: {result['ifs']} - {result['speed_category']}")
    
    # 测试3：攻击角度
    print("\n【测试3】攻击角度评估：")
    for direction in [0, 90, 180, 270]:
        result = indicators.evaluate_attack_angle(
            enemy_direction=direction,
            enemy_pos=(20, 10),
            player_pos=(0, 0)
        )
        print(f"方向{direction}°: {result['ifs']} - {result['direction_category']}")
    
    # 测试4：目标类型
    print("\n【测试4】目标类型评估：")
    for etype in ['soldier', 'ifv']:
        result = indicators.evaluate_target_type(etype)
        print(f"{etype}: {result['ifs']} - {result['type_name']}")
    
    # 测试5：通视条件
    print("\n【测试5】通视条件评估：")
    for blocked, vis_ratio in [(False, 1.0), (True, 0.5), (True, 0.1)]:
        result = indicators.evaluate_visibility(blocked, visibility_ratio=vis_ratio)
        print(f"遮挡={blocked}, 可见度={vis_ratio}: {result['ifs']}")
    
    # 测试6：作战环境
    print("\n【测试6】作战环境评估：")
    for density in [0.2, 0.5, 0.8]:
        result = indicators.evaluate_environment(density, density)
        print(f"密度={density}: {result['ifs']} - {result['complexity_level']}")
    
    print("\n" + "=" * 70)
    print("测试完成！")

