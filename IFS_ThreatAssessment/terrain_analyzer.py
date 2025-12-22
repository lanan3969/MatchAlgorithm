"""
地形通视条件分析模块

实现功能：
1. 加载地形数据（建筑物、障碍物、巷道）
2. 射线追踪检测通视条件
3. 计算环境复杂度
4. 评估目标周围的战术环境
"""

import json
import numpy as np
import math
from typing import Dict, List, Tuple, Optional


class TerrainAnalyzer:
    """地形分析器"""
    
    def __init__(self, terrain_data_path: str = None):
        """
        初始化地形分析器
        
        Args:
            terrain_data_path: 地形数据JSON文件路径
        """
        self.buildings = []
        self.obstacles = []
        self.alleys = []
        self.terrain_bounds = None
        
        if terrain_data_path:
            self.load_terrain_data(terrain_data_path)
    
    def load_terrain_data(self, file_path: str):
        """
        加载地形数据
        
        Args:
            file_path: JSON文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
            
            # 提取地形数据
            if 'terrain' in data:
                terrain = data['terrain']
                self.buildings = terrain.get('buildings', [])
                self.obstacles = terrain.get('obstacles', [])
                self.alleys = terrain.get('alleys', [])
                
                # 设置地形边界
                if 'terrain_info' in terrain:
                    info = terrain['terrain_info']
                    self.terrain_bounds = {
                        'min_x': info.get('min_x', -50),
                        'max_x': info.get('max_x', 50),
                        'min_z': info.get('min_z', -50),
                        'max_z': info.get('max_z', 50)
                    }
            
            print(f"✓ 地形数据加载成功: {len(self.buildings)}栋建筑, "
                  f"{len(self.obstacles)}个障碍物, {len(self.alleys)}条巷道")
                  
        except FileNotFoundError:
            print(f"⚠ 警告: 找不到地形文件 {file_path}，使用空地形")
        except json.JSONDecodeError as e:
            print(f"⚠ 警告: 地形文件格式错误 {e}，使用空地形")
        except Exception as e:
            print(f"⚠ 警告: 加载地形数据失败 {e}，使用空地形")
    
    def check_line_of_sight(self, 
                           pos1: Tuple[float, float], 
                           pos2: Tuple[float, float]) -> Dict:
        """
        射线追踪检测通视条件
        
        使用Liang-Barsky线段裁剪算法检测射线与建筑物/障碍物的相交
        
        Args:
            pos1: 起点位置 (x, z)
            pos2: 终点位置 (x, z)
        
        Returns:
            {
                'is_blocked': bool,  # 是否被遮挡
                'blocking_buildings': List[int],  # 遮挡的建筑物ID列表
                'blocking_obstacles': List[int],  # 遮挡的障碍物ID列表
                'visibility_ratio': float,  # 可见度比例 [0, 1]
                'blocked_segments': int  # 被遮挡的线段数
            }
        """
        x1, z1 = pos1
        x2, z2 = pos2
        
        blocking_buildings = []
        blocking_obstacles = []
        blocked_segments = 0
        
        # 检查与建筑物的相交
        for building in self.buildings:
            if self._line_intersects_building(x1, z1, x2, z2, building):
                blocking_buildings.append(building.get('id', -1))
                blocked_segments += 1
        
        # 检查与障碍物的相交
        for obstacle in self.obstacles:
            if self._line_intersects_obstacle(x1, z1, x2, z2, obstacle):
                blocking_obstacles.append(obstacle.get('id', -1))
                blocked_segments += 1
        
        # 计算可见度比例（简化模型）
        total_blockers = len(blocking_buildings) + len(blocking_obstacles)
        if total_blockers == 0:
            visibility_ratio = 1.0
        else:
            # 每个遮挡物降低可见度
            visibility_ratio = max(0.0, 1.0 - total_blockers * 0.3)
        
        is_blocked = total_blockers > 0
        
        return {
            'is_blocked': is_blocked,
            'blocking_buildings': blocking_buildings,
            'blocking_obstacles': blocking_obstacles,
            'visibility_ratio': visibility_ratio,
            'blocked_segments': blocked_segments
        }
    
    def _line_intersects_building(self, x1: float, z1: float, 
                                 x2: float, z2: float, 
                                 building: Dict) -> bool:
        """
        检测线段是否与建筑物相交
        
        使用AABB（轴对齐包围盒）相交测试
        """
        bx = building['x']
        bz = building['z']
        bw = building['width']
        bd = building['depth']
        
        # 建筑物边界
        b_left = bx - bw / 2
        b_right = bx + bw / 2
        b_bottom = bz - bd / 2
        b_top = bz + bd / 2
        
        # Liang-Barsky线段裁剪算法
        return self._line_rect_intersection(x1, z1, x2, z2, 
                                           b_left, b_bottom, b_right, b_top)
    
    def _line_intersects_obstacle(self, x1: float, z1: float, 
                                  x2: float, z2: float, 
                                  obstacle: Dict) -> bool:
        """检测线段是否与障碍物相交"""
        ox = obstacle['x']
        oz = obstacle['z']
        ow = obstacle['width']
        od = obstacle['depth']
        
        # 障碍物边界
        o_left = ox - ow / 2
        o_right = ox + ow / 2
        o_bottom = oz - od / 2
        o_top = oz + od / 2
        
        return self._line_rect_intersection(x1, z1, x2, z2, 
                                           o_left, o_bottom, o_right, o_top)
    
    def _line_rect_intersection(self, x1: float, y1: float, 
                               x2: float, y2: float,
                               rect_left: float, rect_bottom: float,
                               rect_right: float, rect_top: float) -> bool:
        """
        Liang-Barsky线段-矩形相交算法
        
        Returns:
            True if线段与矩形相交, False otherwise
        """
        dx = x2 - x1
        dy = y2 - y1
        
        # 参数化线段: P(t) = (x1, y1) + t*(dx, dy), t ∈ [0, 1]
        t_min = 0.0
        t_max = 1.0
        
        # 检查四条边界
        # p = [-dx, dx, -dy, dy]
        # q = [x1 - rect_left, rect_right - x1, y1 - rect_bottom, rect_top - y1]
        
        p = [-dx, dx, -dy, dy]
        q = [x1 - rect_left, rect_right - x1, y1 - rect_bottom, rect_top - y1]
        
        for i in range(4):
            if p[i] == 0:
                # 线段平行于边界
                if q[i] < 0:
                    return False  # 线段在矩形外
            else:
                t = q[i] / p[i]
                if p[i] < 0:
                    # 线段从外进入
                    t_min = max(t_min, t)
                else:
                    # 线段从内退出
                    t_max = min(t_max, t)
                
                if t_min > t_max:
                    return False  # 没有相交
        
        return True  # 有相交
    
    def calculate_environment_complexity(self, 
                                        position: Tuple[float, float], 
                                        radius: float = 10.0) -> Dict:
        """
        计算位置周围的环境复杂度
        
        Args:
            position: 目标位置 (x, z)
            radius: 搜索半径（米）
        
        Returns:
            {
                'obstacle_density': float,  # 障碍物密度 [0, 1]
                'building_density': float,  # 建筑物密度 [0, 1]
                'alley_coverage': float,    # 巷道覆盖率 [0, 1]
                'complexity_level': str,    # 'open', 'moderate', 'complex'
                'nearby_buildings': int,    # 附近建筑物数量
                'nearby_obstacles': int     # 附近障碍物数量
            }
        """
        px, pz = position
        
        # 搜索区域面积
        search_area = math.pi * radius ** 2
        
        # 统计附近的建筑物
        nearby_buildings = []
        building_area = 0.0
        
        for building in self.buildings:
            bx, bz = building['x'], building['z']
            distance = math.sqrt((px - bx)**2 + (pz - bz)**2)
            
            if distance < radius:
                nearby_buildings.append(building)
                # 累计建筑物占地面积
                building_area += building['width'] * building['depth']
        
        # 统计附近的障碍物
        nearby_obstacles = []
        obstacle_area = 0.0
        
        for obstacle in self.obstacles:
            ox, oz = obstacle['x'], obstacle['z']
            distance = math.sqrt((px - ox)**2 + (pz - oz)**2)
            
            if distance < radius:
                nearby_obstacles.append(obstacle)
                # 累计障碍物占地面积
                obstacle_area += obstacle['width'] * obstacle['depth']
        
        # 计算密度
        building_density = min(1.0, building_area / search_area)
        obstacle_density = min(1.0, obstacle_area / search_area)
        
        # 检查是否在巷道内
        in_alley = False
        alley_coverage = 0.0
        for alley in self.alleys:
            if self._point_in_alley(px, pz, alley):
                in_alley = True
                alley_coverage = 0.5  # 简化：在巷道内算50%覆盖
                break
        
        # 综合复杂度
        total_density = (building_density + obstacle_density) / 2.0
        
        # 确定复杂度等级
        if total_density < 0.2 and len(nearby_buildings) == 0:
            complexity_level = 'open'  # 开阔地带
        elif total_density < 0.5:
            complexity_level = 'moderate'  # 适度复杂
        else:
            complexity_level = 'complex'  # 复杂地形
        
        return {
            'obstacle_density': obstacle_density,
            'building_density': building_density,
            'alley_coverage': alley_coverage,
            'complexity_level': complexity_level,
            'nearby_buildings': len(nearby_buildings),
            'nearby_obstacles': len(nearby_obstacles),
            'total_density': total_density,
            'in_alley': in_alley
        }
    
    def _point_in_alley(self, x: float, z: float, alley: Dict) -> bool:
        """检查点是否在巷道内（简化检测）"""
        # 巷道作为矩形区域
        ax1, az1 = alley['start_x'], alley['start_z']
        ax2, az2 = alley['end_x'], alley['end_z']
        width = alley['width']
        
        # 计算点到线段的距离
        distance = self._point_to_segment_distance(x, z, ax1, az1, ax2, az2)
        
        return distance < width / 2
    
    def _point_to_segment_distance(self, px: float, pz: float,
                                   x1: float, z1: float,
                                   x2: float, z2: float) -> float:
        """计算点到线段的距离"""
        dx = x2 - x1
        dz = z2 - z1
        
        if dx == 0 and dz == 0:
            # 线段退化为点
            return math.sqrt((px - x1)**2 + (pz - z1)**2)
        
        # 参数化线段
        t = ((px - x1) * dx + (pz - z1) * dz) / (dx**2 + dz**2)
        t = max(0, min(1, t))  # 限制在[0,1]
        
        # 最近点
        closest_x = x1 + t * dx
        closest_z = z1 + t * dz
        
        return math.sqrt((px - closest_x)**2 + (pz - closest_z)**2)
    
    def analyze_tactical_position(self, 
                                  position: Tuple[float, float],
                                  player_pos: Tuple[float, float] = (0, 0)) -> Dict:
        """
        综合分析战术位置
        
        Args:
            position: 目标位置
            player_pos: 玩家位置
        
        Returns:
            完整的地形战术分析
        """
        # 通视条件
        visibility = self.check_line_of_sight(player_pos, position)
        
        # 环境复杂度
        environment = self.calculate_environment_complexity(position, radius=10.0)
        
        # 距离分析
        distance = math.sqrt((position[0] - player_pos[0])**2 + 
                           (position[1] - player_pos[1])**2)
        
        # 战术评估
        tactical_advantage = 'neutral'
        
        if visibility['is_blocked'] and environment['complexity_level'] == 'complex':
            tactical_advantage = 'high'  # 有掩护，复杂地形，敌人优势大
        elif not visibility['is_blocked'] and environment['complexity_level'] == 'open':
            tactical_advantage = 'low'  # 无掩护，开阔地带，我方优势大
        
        return {
            'position': position,
            'distance_to_player': distance,
            'visibility': visibility,
            'environment': environment,
            'tactical_advantage': tactical_advantage,
            'description': self._generate_tactical_description(
                visibility, environment, tactical_advantage
            )
        }
    
    def _generate_tactical_description(self, visibility: Dict, 
                                      environment: Dict,
                                      tactical_advantage: str) -> str:
        """生成战术描述文本"""
        desc_parts = []
        
        # 通视条件
        if visibility['is_blocked']:
            desc_parts.append(f"视线受阻({len(visibility['blocking_buildings'])}栋建筑)")
        else:
            desc_parts.append("视线清晰")
        
        # 环境复杂度
        desc_parts.append(f"{environment['complexity_level']}地形")
        
        # 建筑物和障碍物
        if environment['nearby_buildings'] > 0:
            desc_parts.append(f"{environment['nearby_buildings']}栋建筑附近")
        
        if environment['nearby_obstacles'] > 0:
            desc_parts.append(f"{environment['nearby_obstacles']}个障碍物")
        
        # 巷道
        if environment['in_alley']:
            desc_parts.append("在巷道内")
        
        return ", ".join(desc_parts)
    
    def batch_analyze_enemies(self, 
                             enemies: List[Dict],
                             player_pos: Tuple[float, float] = (0, 0)) -> Dict:
        """
        批量分析多个敌人的地形情况
        
        Args:
            enemies: 敌人列表
            player_pos: 玩家位置
        
        Returns:
            {
                'enemies': {
                    enemy_id: {
                        'visibility': Dict,
                        'environment': Dict
                    }
                },
                'overall_statistics': Dict
            }
        """
        results = {}
        
        for enemy in enemies:
            enemy_id = enemy['id']
            enemy_pos = (enemy['x'], enemy['z'])
            
            # 分析该敌人的地形情况
            analysis = self.analyze_tactical_position(enemy_pos, player_pos)
            
            results[enemy_id] = {
                'visibility': analysis['visibility'],
                'environment': analysis['environment'],
                'tactical_advantage': analysis['tactical_advantage'],
                'description': analysis['description']
            }
        
        # 统计信息
        blocked_count = sum(1 for r in results.values() if r['visibility']['is_blocked'])
        complex_count = sum(1 for r in results.values() 
                          if r['environment']['complexity_level'] == 'complex')
        
        return {
            'enemies': results,
            'overall_statistics': {
                'total_enemies': len(enemies),
                'blocked_enemies': blocked_count,
                'visible_enemies': len(enemies) - blocked_count,
                'in_complex_terrain': complex_count,
                'average_visibility': np.mean([r['visibility']['visibility_ratio'] 
                                             for r in results.values()])
            }
        }


if __name__ == "__main__":
    # 测试代码
    print("=" * 80)
    print("地形分析器测试")
    print("=" * 80)
    
    # 创建分析器（不加载实际文件，使用测试数据）
    analyzer = TerrainAnalyzer()
    
    # 手动设置测试地形
    analyzer.buildings = [
        {'id': 1, 'x': 10, 'z': 15, 'width': 8, 'depth': 12, 'height': 10},
        {'id': 2, 'x': -15, 'z': 20, 'width': 10, 'depth': 10, 'height': 8},
        {'id': 3, 'x': 25, 'z': -10, 'width': 6, 'depth': 8, 'height': 6}
    ]
    
    analyzer.obstacles = [
        {'id': 1, 'type': 'Cover', 'x': 5, 'z': 5, 'width': 2, 'depth': 2},
        {'id': 2, 'type': 'Barrier', 'x': 20, 'z': 10, 'width': 3, 'depth': 1},
    ]
    
    analyzer.alleys = [
        {'id': 1, 'start_x': 0, 'start_z': 0, 'end_x': 30, 'end_z': 0, 'width': 5}
    ]
    
    print(f"✓ 测试地形: {len(analyzer.buildings)}栋建筑, "
          f"{len(analyzer.obstacles)}个障碍物, {len(analyzer.alleys)}条巷道")
    
    # 测试1：通视检测
    print("\n【测试1】通视条件检测：")
    test_cases = [
        ((0, 0), (10, 15), "玩家→建筑1中心"),
        ((0, 0), (30, 30), "玩家→远处开阔区"),
        ((0, 0), (5, 5), "玩家→障碍物1")
    ]
    
    for pos1, pos2, desc in test_cases:
        result = analyzer.check_line_of_sight(pos1, pos2)
        print(f"\n{desc}:")
        print(f"  遮挡: {result['is_blocked']}")
        print(f"  可见度: {result['visibility_ratio']:.2f}")
        print(f"  遮挡建筑: {result['blocking_buildings']}")
        print(f"  遮挡障碍物: {result['blocking_obstacles']}")
    
    # 测试2：环境复杂度
    print("\n" + "=" * 80)
    print("【测试2】环境复杂度分析：")
    test_positions = [
        (10, 15, "建筑1中心"),
        (40, 40, "远离建筑的开阔区"),
        (15, 10, "建筑1附近")
    ]
    
    for x, z, desc in test_positions:
        result = analyzer.calculate_environment_complexity((x, z), radius=10)
        print(f"\n位置({x}, {z}) - {desc}:")
        print(f"  复杂度等级: {result['complexity_level']}")
        print(f"  建筑物密度: {result['building_density']:.2f}")
        print(f"  障碍物密度: {result['obstacle_density']:.2f}")
        print(f"  附近建筑: {result['nearby_buildings']}栋")
        print(f"  附近障碍物: {result['nearby_obstacles']}个")
    
    # 测试3：战术位置分析
    print("\n" + "=" * 80)
    print("【测试3】战术位置综合分析：")
    
    enemy_pos = (15, 20)
    player_pos = (0, 0)
    
    result = analyzer.analyze_tactical_position(enemy_pos, player_pos)
    print(f"\n敌人位置: {enemy_pos}")
    print(f"玩家位置: {player_pos}")
    print(f"距离: {result['distance_to_player']:.1f}m")
    print(f"战术优势: {result['tactical_advantage']}")
    print(f"描述: {result['description']}")
    
    # 测试4：批量分析
    print("\n" + "=" * 80)
    print("【测试4】批量敌人地形分析：")
    
    enemies = [
        {'id': 1, 'x': 10, 'z': 15},
        {'id': 2, 'x': 30, 'z': 30},
        {'id': 3, 'x': -10, 'z': -10}
    ]
    
    batch_result = analyzer.batch_analyze_enemies(enemies, player_pos)
    
    print(f"\n总体统计:")
    stats = batch_result['overall_statistics']
    print(f"  总敌人数: {stats['total_enemies']}")
    print(f"  被遮挡: {stats['blocked_enemies']}")
    print(f"  可见: {stats['visible_enemies']}")
    print(f"  复杂地形中: {stats['in_complex_terrain']}")
    print(f"  平均可见度: {stats['average_visibility']:.2f}")
    
    print("\n各敌人详情:")
    for enemy_id, data in batch_result['enemies'].items():
        print(f"\n  敌人#{enemy_id}:")
        print(f"    {data['description']}")
        print(f"    战术优势: {data['tactical_advantage']}")
    
    print("\n" + "=" * 80)
    print("测试完成！")

