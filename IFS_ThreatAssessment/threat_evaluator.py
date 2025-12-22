"""
综合威胁评估器（主接口）

基于论文《地面作战目标威胁评估多属性指标处理方法》
实现多属性指标的加权聚合和威胁排序功能
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import time
from ifs_core import IFS, IFSOperations
from threat_indicators import ThreatIndicators


class IFSThreatEvaluator:
    """
    IFS威胁评估器主类
    
    功能：
    1. 评估单个目标的综合威胁度
    2. 对多个目标进行威胁排序
    3. 找出最具威胁的目标
    """
    
    def __init__(self, custom_weights: Dict[str, float] = None):
        """
        初始化威胁评估器
        
        Args:
            custom_weights: 自定义指标权重字典
                默认权重参考论文案例：
                {
                    'distance': 0.30,  # 距离最重要
                    'type': 0.25,      # 目标类型
                    'speed': 0.20,     # 速度
                    'angle': 0.15,     # 攻击角度
                    'visibility': 0.06,  # 通视条件
                    'environment': 0.04  # 作战环境
                }
        """
        self.indicators = ThreatIndicators()
        self.operations = IFSOperations()
        
        # 设置指标权重
        self.default_weights = {
            'distance': 0.30,
            'type': 0.25,
            'speed': 0.20,
            'angle': 0.15,
            'visibility': 0.06,
            'environment': 0.04
        }
        
        if custom_weights:
            self.weights = custom_weights
            # 归一化权重
            total = sum(self.weights.values())
            if total > 0:
                self.weights = {k: v/total for k, v in self.weights.items()}
        else:
            self.weights = self.default_weights
    
    def evaluate_single_target(self, 
                              enemy: Dict, 
                              player_pos: Tuple[float, float] = (0, 0),
                              terrain_data: Dict = None) -> Dict:
        """
        评估单个敌人的威胁度
        
        Args:
            enemy: 敌人数据字典
                必需字段: {
                    'id': int,
                    'type': str,  # 'soldier' 或 'ifv'
                    'x': float,
                    'z': float,
                    'speed': float,
                    'direction': float  # 0-360度
                }
            player_pos: 玩家位置 (x, z)
            terrain_data: 地形数据（可选），包含通视和环境信息
        
        Returns:
            {
                'enemy_id': int,
                'comprehensive_threat_score': float,  # -1 到 1
                'threat_level': str,  # 'low', 'medium', 'high', 'critical'
                'ifs_values': {
                    'membership': float,
                    'non_membership': float,
                    'hesitancy': float
                },
                'indicator_details': Dict,  # 各指标的详细评估结果
                'weighted_aggregation': Dict,  # 加权聚合信息
                'evaluation_time': float  # 评估耗时（秒）
            }
        """
        start_time = time.time()
        
        # 1. 计算距离
        dx = enemy['x'] - player_pos[0]
        dz = enemy['z'] - player_pos[1]
        distance = np.sqrt(dx**2 + dz**2)
        
        # 2. 评估各个威胁指标
        indicator_results = {}
        
        # 指标1：距离
        indicator_results['distance'] = self.indicators.evaluate_distance(distance)
        
        # 指标2：速度
        indicator_results['speed'] = self.indicators.evaluate_speed(
            enemy['speed'], 
            enemy['type']
        )
        
        # 指标3：攻击角度
        indicator_results['angle'] = self.indicators.evaluate_attack_angle(
            enemy['direction'],
            (enemy['x'], enemy['z']),
            player_pos
        )
        
        # 指标4：目标类型
        indicator_results['type'] = self.indicators.evaluate_target_type(
            enemy['type']
        )
        
        # 指标5：通视条件（如果有地形数据）
        if terrain_data and 'visibility' in terrain_data:
            vis_data = terrain_data['visibility']
            indicator_results['visibility'] = self.indicators.evaluate_visibility(
                vis_data.get('is_blocked', False),
                vis_data.get('blocking_count', 0),
                vis_data.get('visibility_ratio', None)
            )
        else:
            # 默认：假设无遮挡
            indicator_results['visibility'] = self.indicators.evaluate_visibility(
                is_blocked=False,
                visibility_ratio=1.0
            )
        
        # 指标6：作战环境（如果有地形数据）
        if terrain_data and 'environment' in terrain_data:
            env_data = terrain_data['environment']
            indicator_results['environment'] = self.indicators.evaluate_environment(
                env_data.get('obstacle_density', 0.0),
                env_data.get('building_density', 0.0),
                env_data.get('complexity_level', None)
            )
        else:
            # 默认：开阔环境
            indicator_results['environment'] = self.indicators.evaluate_environment(
                obstacle_density=0.2,
                building_density=0.1
            )
        
        # 3. 提取各指标的IFS值
        ifs_list = []
        weight_list = []
        indicator_names = []
        
        for indicator_name in ['distance', 'type', 'speed', 'angle', 'visibility', 'environment']:
            if indicator_name in indicator_results and indicator_name in self.weights:
                ifs_list.append(indicator_results[indicator_name]['ifs'])
                weight_list.append(self.weights[indicator_name])
                indicator_names.append(indicator_name)
        
        # 4. 使用IFS加权算术平均算子（IFWA）聚合
        comprehensive_ifs = self.operations.weighted_average(ifs_list, weight_list)
        
        # 5. 计算综合威胁得分
        comprehensive_score = comprehensive_ifs.score()
        
        # 6. 确定威胁等级
        if comprehensive_score >= 0.6:
            threat_level = 'critical'
        elif comprehensive_score >= 0.3:
            threat_level = 'high'
        elif comprehensive_score >= 0.0:
            threat_level = 'medium'
        else:
            threat_level = 'low'
        
        # 7. 计算各指标对综合得分的贡献
        contributions = {}
        for i, name in enumerate(indicator_names):
            indicator_score = ifs_list[i].score()
            contribution = weight_list[i] * indicator_score
            contributions[name] = {
                'weight': weight_list[i],
                'indicator_score': indicator_score,
                'contribution': contribution,
                'percentage': (contribution / comprehensive_score * 100) if comprehensive_score != 0 else 0
            }
        
        evaluation_time = time.time() - start_time
        
        return {
            'enemy_id': enemy['id'],
            'comprehensive_threat_score': comprehensive_score,
            'threat_level': threat_level,
            'ifs_values': {
                'membership': comprehensive_ifs.mu,
                'non_membership': comprehensive_ifs.nu,
                'hesitancy': comprehensive_ifs.pi
            },
            'indicator_details': indicator_results,
            'weighted_aggregation': {
                'weights': dict(zip(indicator_names, weight_list)),
                'contributions': contributions,
                'aggregation_method': 'IFWA'  # IFS加权算术平均
            },
            'distance': distance,
            'evaluation_time': evaluation_time
        }
    
    def rank_targets(self, 
                    enemies: List[Dict], 
                    player_pos: Tuple[float, float] = (0, 0),
                    terrain_data: Dict = None) -> List[Dict]:
        """
        对所有敌人进行威胁排序
        
        Args:
            enemies: 敌人列表
            player_pos: 玩家位置
            terrain_data: 地形数据（可选）
        
        Returns:
            按威胁度降序排列的评估结果列表
        """
        results = []
        
        for enemy in enemies:
            # 获取该敌人的地形数据（如果存在）
            enemy_terrain_data = None
            if terrain_data and 'enemies' in terrain_data:
                enemy_terrain_data = terrain_data['enemies'].get(enemy['id'], None)
            
            result = self.evaluate_single_target(enemy, player_pos, enemy_terrain_data)
            results.append(result)
        
        # 按综合威胁得分降序排序
        results.sort(key=lambda x: x['comprehensive_threat_score'], reverse=True)
        
        # 添加排名信息
        for rank, result in enumerate(results, 1):
            result['rank'] = rank
        
        return results
    
    def find_most_threatening(self, 
                             enemies: List[Dict], 
                             player_pos: Tuple[float, float] = (0, 0),
                             terrain_data: Dict = None) -> Optional[Dict]:
        """
        快速找出最高威胁目标（优化版）
        
        Args:
            enemies: 敌人列表
            player_pos: 玩家位置
            terrain_data: 地形数据（可选）
        
        Returns:
            最高威胁目标的评估结果，如果没有敌人则返回None
        """
        if not enemies:
            return None
        
        if len(enemies) == 1:
            return self.evaluate_single_target(enemies[0], player_pos, terrain_data)
        
        # 评估所有目标并找出最大威胁
        max_threat_score = -float('inf')
        most_threatening = None
        
        for enemy in enemies:
            enemy_terrain_data = None
            if terrain_data and 'enemies' in terrain_data:
                enemy_terrain_data = terrain_data['enemies'].get(enemy['id'], None)
            
            result = self.evaluate_single_target(enemy, player_pos, enemy_terrain_data)
            
            if result['comprehensive_threat_score'] > max_threat_score:
                max_threat_score = result['comprehensive_threat_score']
                most_threatening = result
        
        if most_threatening:
            most_threatening['rank'] = 1
        
        return most_threatening
    
    def compare_targets(self, enemy1: Dict, enemy2: Dict,
                       player_pos: Tuple[float, float] = (0, 0)) -> Dict:
        """
        比较两个目标的威胁度
        
        Args:
            enemy1: 第一个敌人
            enemy2: 第二个敌人
            player_pos: 玩家位置
        
        Returns:
            {
                'more_threatening': int,  # 1表示enemy1更危险，2表示enemy2更危险，0表示相同
                'score_difference': float,
                'enemy1_result': Dict,
                'enemy2_result': Dict
            }
        """
        result1 = self.evaluate_single_target(enemy1, player_pos)
        result2 = self.evaluate_single_target(enemy2, player_pos)
        
        score1 = result1['comprehensive_threat_score']
        score2 = result2['comprehensive_threat_score']
        score_diff = score1 - score2
        
        # 使用IFS比较法则
        ifs1 = IFS(
            result1['ifs_values']['membership'],
            result1['ifs_values']['non_membership']
        )
        ifs2 = IFS(
            result2['ifs_values']['membership'],
            result2['ifs_values']['non_membership']
        )
        
        comparison = self.operations.compare(ifs1, ifs2)
        
        return {
            'more_threatening': 1 if comparison > 0 else (2 if comparison < 0 else 0),
            'score_difference': score_diff,
            'enemy1_result': result1,
            'enemy2_result': result2,
            'comparison_method': 'IFS比较法则（得分函数+精确函数）'
        }
    
    def get_threat_statistics(self, evaluation_results: List[Dict]) -> Dict:
        """
        获取威胁评估统计信息
        
        Args:
            evaluation_results: 评估结果列表（来自rank_targets）
        
        Returns:
            统计信息字典
        """
        if not evaluation_results:
            return {}
        
        scores = [r['comprehensive_threat_score'] for r in evaluation_results]
        
        # 按威胁等级统计
        level_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for result in evaluation_results:
            level_counts[result['threat_level']] += 1
        
        # 指标重要性分析（基于平均贡献度）
        indicator_importance = {}
        for indicator_name in self.weights.keys():
            contributions = []
            for result in evaluation_results:
                if indicator_name in result['weighted_aggregation']['contributions']:
                    contrib = result['weighted_aggregation']['contributions'][indicator_name]
                    contributions.append(abs(contrib['contribution']))
            
            if contributions:
                indicator_importance[indicator_name] = {
                    'mean_contribution': np.mean(contributions),
                    'max_contribution': np.max(contributions),
                    'weight': self.weights[indicator_name]
                }
        
        return {
            'total_enemies': len(evaluation_results),
            'threat_level_distribution': level_counts,
            'score_statistics': {
                'mean': np.mean(scores),
                'median': np.median(scores),
                'std': np.std(scores),
                'min': np.min(scores),
                'max': np.max(scores)
            },
            'indicator_importance': indicator_importance,
            'most_threatening': evaluation_results[0] if evaluation_results else None,
            'least_threatening': evaluation_results[-1] if evaluation_results else None
        }


if __name__ == "__main__":
    # 测试代码
    print("=" * 80)
    print("IFS威胁评估器测试")
    print("=" * 80)
    
    # 创建评估器
    evaluator = IFSThreatEvaluator()
    
    # 测试数据：模拟战场上的3个敌人
    enemies = [
        {
            'id': 1,
            'type': 'soldier',
            'x': 15.0,
            'z': 10.0,
            'speed': 6.0,
            'direction': 200  # 大致朝向玩家
        },
        {
            'id': 2,
            'type': 'ifv',
            'x': 30.0,
            'z': -5.0,
            'speed': 12.0,
            'direction': 180  # 接近玩家
        },
        {
            'id': 3,
            'type': 'soldier',
            'x': -20.0,
            'z': 25.0,
            'speed': 1.5,
            'direction': 90  # 侧向移动
        }
    ]
    
    player_pos = (0, 0)
    
    # 测试1：评估单个目标
    print("\n【测试1】评估单个目标（敌人#1）：")
    result1 = evaluator.evaluate_single_target(enemies[0], player_pos)
    print(f"敌人ID: {result1['enemy_id']}")
    print(f"综合威胁得分: {result1['comprehensive_threat_score']:.3f}")
    print(f"威胁等级: {result1['threat_level']}")
    print(f"IFS值: μ={result1['ifs_values']['membership']:.3f}, "
          f"ν={result1['ifs_values']['non_membership']:.3f}, "
          f"π={result1['ifs_values']['hesitancy']:.3f}")
    print(f"评估耗时: {result1['evaluation_time']*1000:.2f}ms")
    
    print("\n各指标评估结果：")
    for indicator_name, indicator_data in result1['indicator_details'].items():
        print(f"  {indicator_name}: 得分={indicator_data['threat_score']:.3f}, "
              f"等级={indicator_data['threat_level']}")
    
    print("\n各指标贡献度：")
    for indicator_name, contrib_data in result1['weighted_aggregation']['contributions'].items():
        print(f"  {indicator_name}: 权重={contrib_data['weight']:.2f}, "
              f"贡献={contrib_data['contribution']:.3f} "
              f"({contrib_data['percentage']:.1f}%)")
    
    # 测试2：威胁排序
    print("\n" + "=" * 80)
    print("【测试2】多目标威胁排序：")
    ranked_results = evaluator.rank_targets(enemies, player_pos)
    
    print(f"\n威胁排名（共{len(ranked_results)}个目标）：")
    for result in ranked_results:
        distance = result['distance']
        print(f"\n排名#{result['rank']}: 敌人#{result['enemy_id']} "
              f"({result['indicator_details']['type']['type_name']})")
        print(f"  综合得分: {result['comprehensive_threat_score']:.3f}")
        print(f"  威胁等级: {result['threat_level']}")
        print(f"  距离: {distance:.1f}m")
        print(f"  速度: {result['indicator_details']['speed']['speed']:.1f}m/s")
        print(f"  方向: {result['indicator_details']['angle']['direction_category']}")
    
    # 测试3：找出最高威胁
    print("\n" + "=" * 80)
    print("【测试3】快速识别最高威胁：")
    most_threatening = evaluator.find_most_threatening(enemies, player_pos)
    
    print(f"\n⚠️ 最高威胁目标：敌人#{most_threatening['enemy_id']}")
    print(f"  类型: {most_threatening['indicator_details']['type']['type_name']}")
    print(f"  威胁得分: {most_threatening['comprehensive_threat_score']:.3f}")
    print(f"  威胁等级: {most_threatening['threat_level']}")
    print(f"  距离: {most_threatening['distance']:.1f}m")
    
    # 测试4：统计信息
    print("\n" + "=" * 80)
    print("【测试4】威胁评估统计：")
    stats = evaluator.get_threat_statistics(ranked_results)
    
    print(f"\n总敌人数: {stats['total_enemies']}")
    print(f"威胁等级分布: {stats['threat_level_distribution']}")
    print(f"\n得分统计:")
    print(f"  平均值: {stats['score_statistics']['mean']:.3f}")
    print(f"  中位数: {stats['score_statistics']['median']:.3f}")
    print(f"  标准差: {stats['score_statistics']['std']:.3f}")
    print(f"  范围: [{stats['score_statistics']['min']:.3f}, {stats['score_statistics']['max']:.3f}]")
    
    print(f"\n指标重要性分析:")
    for indicator, importance in sorted(stats['indicator_importance'].items(), 
                                       key=lambda x: x[1]['mean_contribution'], 
                                       reverse=True):
        print(f"  {indicator}: 平均贡献={importance['mean_contribution']:.3f}, "
              f"权重={importance['weight']:.2f}")
    
    print("\n" + "=" * 80)
    print("测试完成！")

