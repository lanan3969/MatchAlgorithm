"""
IFS威胁评估系统测试脚本

包含单元测试和集成测试，验证系统的正确性和性能
"""

import sys
import os
import time
import json
import numpy as np

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ifs_core import IFS, IFSConverter, IFSOperations
from threat_indicators import ThreatIndicators
from threat_evaluator import IFSThreatEvaluator
from terrain_analyzer import TerrainAnalyzer
from visualizer import ThreatVisualizer


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_results = []
    
    def assert_equal(self, actual, expected, test_name: str):
        """断言相等"""
        if actual == expected:
            self.passed += 1
            print(f"  ✓ {test_name}")
            return True
        else:
            self.failed += 1
            print(f"  ✗ {test_name}: Expected {expected}, got {actual}")
            return False
    
    def assert_true(self, condition, test_name: str):
        """断言为真"""
        if condition:
            self.passed += 1
            print(f"  ✓ {test_name}")
            return True
        else:
            self.failed += 1
            print(f"  ✗ {test_name}: Condition is False")
            return False
    
    def assert_range(self, value, min_val, max_val, test_name: str):
        """断言在范围内"""
        if min_val <= value <= max_val:
            self.passed += 1
            print(f"  ✓ {test_name}")
            return True
        else:
            self.failed += 1
            print(f"  ✗ {test_name}: {value} not in range [{min_val}, {max_val}]")
            return False
    
    def print_summary(self):
        """打印测试总结"""
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        print(f"总测试数: {total}")
        print(f"通过: {self.passed} ({success_rate:.1f}%)")
        print(f"失败: {self.failed}")
        print("=" * 80)


def test_ifs_core():
    """测试IFS核心库"""
    print("\n" + "=" * 80)
    print("【模块1】测试 IFS 核心库")
    print("=" * 80)
    
    runner = TestRunner()
    
    # 测试1：IFS基本创建
    print("\n测试1.1：IFS基本创建和约束")
    ifs1 = IFS(0.7, 0.2)
    runner.assert_range(ifs1.mu, 0, 1, "隶属度在[0,1]范围内")
    runner.assert_range(ifs1.nu, 0, 1, "非隶属度在[0,1]范围内")
    runner.assert_range(ifs1.pi, 0, 1, "犹豫度在[0,1]范围内")
    runner.assert_true(abs((ifs1.mu + ifs1.nu + ifs1.pi) - 1.0) < 0.001, 
                      "μ + ν + π = 1")
    
    # 测试2：得分函数
    print("\n测试1.2：得分函数和精确函数")
    score = ifs1.score()
    runner.assert_range(score, -1, 1, "得分函数在[-1,1]范围内")
    accuracy = ifs1.accuracy()
    runner.assert_range(accuracy, 0, 1, "精确函数在[0,1]范围内")
    
    # 测试3：数据转换
    print("\n测试1.3：数据类型转换")
    converter = IFSConverter()
    
    # 实数转换
    ifs_real = converter.from_real_number(30, ideal=0, tolerance=15, min_val=0, max_val=50)
    runner.assert_true(isinstance(ifs_real, IFS), "实数转IFS成功")
    
    # 语言术语转换
    ifs_high = converter.from_linguistic_term('高')
    ifs_low = converter.from_linguistic_term('低')
    runner.assert_true(ifs_high.score() > ifs_low.score(), "高威胁 > 低威胁")
    
    # 测试4：IFS运算
    print("\n测试1.4：IFS运算")
    ops = IFSOperations()
    
    # 比较
    comparison = ops.compare(ifs_high, ifs_low)
    runner.assert_equal(comparison, 1, "高威胁IFS > 低威胁IFS")
    
    # 加权平均
    ifs_list = [IFS(0.8, 0.1), IFS(0.6, 0.3), IFS(0.4, 0.5)]
    weights = [0.5, 0.3, 0.2]
    ifs_avg = ops.weighted_average(ifs_list, weights)
    runner.assert_true(isinstance(ifs_avg, IFS), "加权平均计算成功")
    
    runner.print_summary()
    return runner


def test_threat_indicators():
    """测试威胁指标"""
    print("\n" + "=" * 80)
    print("【模块2】测试威胁指标量化")
    print("=" * 80)
    
    runner = TestRunner()
    indicators = ThreatIndicators()
    
    # 测试1：距离指标
    print("\n测试2.1：距离指标")
    dist_result_near = indicators.evaluate_distance(5)  # 近距离
    dist_result_far = indicators.evaluate_distance(40)  # 远距离
    runner.assert_true(dist_result_near['threat_score'] > dist_result_far['threat_score'],
                      "近距离威胁 > 远距离威胁")
    runner.assert_equal(dist_result_near['zone'], 'critical', "5米为极高威胁区域")
    
    # 测试2：速度指标
    print("\n测试2.2：速度指标")
    speed_high = indicators.evaluate_speed(8, 'soldier')
    speed_low = indicators.evaluate_speed(1, 'soldier')
    runner.assert_true(speed_high['threat_score'] > speed_low['threat_score'],
                      "高速威胁 > 低速威胁")
    
    # 测试3：攻击角度
    print("\n测试2.3：攻击角度")
    angle_front = indicators.evaluate_attack_angle(
        enemy_direction=180,  # 朝向玩家
        enemy_pos=(20, 0),
        player_pos=(0, 0)
    )
    angle_back = indicators.evaluate_attack_angle(
        enemy_direction=0,  # 背向玩家
        enemy_pos=(20, 0),
        player_pos=(0, 0)
    )
    runner.assert_true(angle_front['threat_score'] > angle_back['threat_score'],
                      "正面接近威胁 > 背向撤退威胁")
    
    # 测试4：目标类型
    print("\n测试2.4：目标类型")
    type_ifv = indicators.evaluate_target_type('ifv')
    type_soldier = indicators.evaluate_target_type('soldier')
    runner.assert_true(type_ifv['threat_score'] >= type_soldier['threat_score'],
                      "IFV威胁 >= 士兵威胁")
    
    # 测试5：通视条件
    print("\n测试2.5：通视条件")
    vis_clear = indicators.evaluate_visibility(is_blocked=False, visibility_ratio=1.0)
    vis_blocked = indicators.evaluate_visibility(is_blocked=True, visibility_ratio=0.2)
    runner.assert_true(vis_clear['threat_score'] > vis_blocked['threat_score'],
                      "无遮挡威胁 > 有遮挡威胁")
    
    # 测试6：作战环境
    print("\n测试2.6：作战环境")
    env_open = indicators.evaluate_environment(0.1, 0.1)
    env_complex = indicators.evaluate_environment(0.8, 0.7)
    runner.assert_true(env_open['threat_score'] > env_complex['threat_score'],
                      "开阔环境威胁 > 复杂环境威胁")
    
    runner.print_summary()
    return runner


def test_threat_evaluator():
    """测试综合威胁评估器"""
    print("\n" + "=" * 80)
    print("【模块3】测试综合威胁评估器")
    print("=" * 80)
    
    runner = TestRunner()
    evaluator = IFSThreatEvaluator()
    
    # 创建测试敌人
    enemies = [
        {
            'id': 1,
            'type': 'ifv',
            'x': 15.0,
            'z': 10.0,
            'speed': 12.0,
            'direction': 200  # 朝向玩家
        },
        {
            'id': 2,
            'type': 'soldier',
            'x': 40.0,
            'z': 30.0,
            'speed': 2.0,
            'direction': 90  # 侧向
        },
        {
            'id': 3,
            'type': 'soldier',
            'x': 8.0,
            'z': 5.0,
            'speed': 7.0,
            'direction': 180  # 接近
        }
    ]
    
    # 测试1：单目标评估
    print("\n测试3.1：单目标评估")
    result = evaluator.evaluate_single_target(enemies[0])
    runner.assert_true('comprehensive_threat_score' in result, "包含综合威胁得分")
    runner.assert_true('threat_level' in result, "包含威胁等级")
    runner.assert_true('indicator_details' in result, "包含指标详情")
    runner.assert_range(result['comprehensive_threat_score'], -1, 1, "综合得分在[-1,1]范围内")
    runner.assert_true(result['evaluation_time'] > 0, "评估耗时已记录")
    
    # 测试2：多目标排序
    print("\n测试3.2：多目标威胁排序")
    ranked = evaluator.rank_targets(enemies)
    runner.assert_equal(len(ranked), len(enemies), "排序结果数量正确")
    runner.assert_true(ranked[0]['rank'] == 1, "第一名rank=1")
    
    # 验证排序正确性
    scores = [r['comprehensive_threat_score'] for r in ranked]
    is_sorted = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
    runner.assert_true(is_sorted, "威胁度按降序排列")
    
    # 测试3：找出最高威胁
    print("\n测试3.3：快速识别最高威胁")
    most_threatening = evaluator.find_most_threatening(enemies)
    runner.assert_true(most_threatening is not None, "找到最高威胁目标")
    runner.assert_true(most_threatening['enemy_id'] == ranked[0]['enemy_id'],
                      "最高威胁与排序第一名一致")
    
    # 测试4：目标对比
    print("\n测试3.4：目标对比")
    comparison = evaluator.compare_targets(enemies[0], enemies[1])
    runner.assert_true('more_threatening' in comparison, "包含对比结果")
    runner.assert_true('score_difference' in comparison, "包含得分差异")
    
    # 测试5：统计信息
    print("\n测试3.5：威胁统计")
    stats = evaluator.get_threat_statistics(ranked)
    runner.assert_equal(stats['total_enemies'], len(enemies), "总敌人数正确")
    runner.assert_true('threat_level_distribution' in stats, "包含威胁等级分布")
    runner.assert_true('score_statistics' in stats, "包含得分统计")
    
    runner.print_summary()
    return runner


def test_terrain_analyzer():
    """测试地形分析器"""
    print("\n" + "=" * 80)
    print("【模块4】测试地形分析器")
    print("=" * 80)
    
    runner = TestRunner()
    analyzer = TerrainAnalyzer()
    
    # 设置测试地形
    analyzer.buildings = [
        {'id': 1, 'x': 10, 'z': 10, 'width': 8, 'depth': 8, 'height': 10}
    ]
    analyzer.obstacles = [
        {'id': 1, 'type': 'Cover', 'x': 20, 'z': 20, 'width': 2, 'depth': 2}
    ]
    
    # 测试1：通视检测
    print("\n测试4.1：通视条件检测")
    vis_blocked = analyzer.check_line_of_sight((0, 0), (10, 10))  # 穿过建筑
    vis_clear = analyzer.check_line_of_sight((0, 0), (50, 50))   # 开阔区域
    
    runner.assert_true(vis_blocked['is_blocked'], "检测到建筑遮挡")
    runner.assert_true(not vis_clear['is_blocked'], "开阔区域无遮挡")
    
    # 测试2：环境复杂度
    print("\n测试4.2：环境复杂度计算")
    env_near_building = analyzer.calculate_environment_complexity((10, 10), radius=5)
    env_open_area = analyzer.calculate_environment_complexity((50, 50), radius=10)
    
    runner.assert_true(env_near_building['nearby_buildings'] > 0, "建筑附近检测到建筑物")
    runner.assert_equal(env_open_area['nearby_buildings'], 0, "开阔区域无建筑物")
    runner.assert_true(env_near_building['complexity_level'] in ['open', 'moderate', 'complex'],
                      "复杂度等级有效")
    
    # 测试3：战术位置分析
    print("\n测试4.3：战术位置综合分析")
    tactical = analyzer.analyze_tactical_position((15, 15), player_pos=(0, 0))
    runner.assert_true('visibility' in tactical, "包含通视信息")
    runner.assert_true('environment' in tactical, "包含环境信息")
    runner.assert_true('tactical_advantage' in tactical, "包含战术优势评估")
    
    runner.print_summary()
    return runner


def test_performance():
    """性能测试"""
    print("\n" + "=" * 80)
    print("【模块5】性能基准测试")
    print("=" * 80)
    
    evaluator = IFSThreatEvaluator()
    
    # 生成测试数据
    num_enemies = 30
    enemies = []
    for i in range(num_enemies):
        angle = np.random.uniform(0, 2*np.pi)
        distance = np.random.uniform(10, 40)
        enemies.append({
            'id': i+1,
            'type': np.random.choice(['soldier', 'ifv']),
            'x': distance * np.cos(angle),
            'z': distance * np.sin(angle),
            'speed': np.random.uniform(1, 15),
            'direction': np.random.uniform(0, 360)
        })
    
    # 测试1：单目标评估性能
    print(f"\n测试5.1：单目标评估性能（{num_enemies}次）")
    times = []
    for enemy in enemies:
        start = time.time()
        evaluator.evaluate_single_target(enemy)
        times.append((time.time() - start) * 1000)  # 转换为毫秒
    
    avg_time = np.mean(times)
    max_time = np.max(times)
    print(f"  平均耗时: {avg_time:.2f}ms")
    print(f"  最大耗时: {max_time:.2f}ms")
    print(f"  ✓ 目标: < 5ms, 实际: {avg_time:.2f}ms {'[通过]' if avg_time < 5 else '[超时]'}")
    
    # 测试2：多目标排序性能
    print(f"\n测试5.2：多目标排序性能（{num_enemies}个目标）")
    start = time.time()
    ranked = evaluator.rank_targets(enemies)
    elapsed = (time.time() - start) * 1000
    
    print(f"  排序耗时: {elapsed:.2f}ms")
    print(f"  ✓ 目标: < 50ms, 实际: {elapsed:.2f}ms {'[通过]' if elapsed < 50 else '[超时]'}")
    
    # 测试3：找最高威胁性能
    print(f"\n测试5.3：找最高威胁性能（{num_enemies}个目标）")
    start = time.time()
    most_threatening = evaluator.find_most_threatening(enemies)
    elapsed = (time.time() - start) * 1000
    
    print(f"  查找耗时: {elapsed:.2f}ms")
    print(f"  ✓ 目标: < 50ms, 实际: {elapsed:.2f}ms {'[通过]' if elapsed < 50 else '[超时]'}")


def test_integration():
    """集成测试：完整流程"""
    print("\n" + "=" * 80)
    print("【模块6】集成测试 - 完整评估流程")
    print("=" * 80)
    
    # 创建所有组件
    evaluator = IFSThreatEvaluator()
    visualizer = ThreatVisualizer(output_dir="examples")
    
    # 模拟战场场景
    print("\n场景：城市巷战，玩家被3个敌人包围")
    enemies = [
        {
            'id': 1,
            'type': 'ifv',
            'x': 12.0,
            'z': 8.0,
            'speed': 10.0,
            'direction': 225  # 西南方向，接近玩家
        },
        {
            'id': 2,
            'type': 'soldier',
            'x': -15.0,
            'z': 10.0,
            'speed': 5.0,
            'direction': 45   # 东北方向，接近玩家
        },
        {
            'id': 3,
            'type': 'soldier',
            'x': 5.0,
            'z': -20.0,
            'speed': 2.0,
            'direction': 90   # 东，侧向移动
        }
    ]
    
    # 执行威胁评估
    print("\n执行威胁评估...")
    ranked_results = evaluator.rank_targets(enemies)
    
    # 显示结果
    print("\n威胁评估结果：")
    for result in ranked_results:
        print(f"\n  [{result['rank']}] 敌人#{result['enemy_id']} "
              f"({result['indicator_details']['type']['type_name']})")
        print(f"      综合威胁得分: {result['comprehensive_threat_score']:.3f}")
        print(f"      威胁等级: {result['threat_level']}")
        print(f"      距离: {result['distance']:.1f}m")
        print(f"      关键指标:")
        for ind_name, ind_data in result['indicator_details'].items():
            if 'threat_score' in ind_data:
                print(f"        - {ind_name}: {ind_data['threat_score']:.3f}")
    
    # 生成可视化
    print("\n生成可视化图表...")
    try:
        # 威胁排名
        ranking_file = visualizer.plot_threat_ranking(ranked_results, "integration_ranking.png")
        print(f"  ✓ 威胁排名: {ranking_file}")
        
        # 雷达图（最高威胁）
        radar_file = visualizer.plot_radar_chart(ranked_results[0], "integration_radar.png")
        print(f"  ✓ 威胁雷达图: {radar_file}")
        
        # 贡献度分析
        contrib_file = visualizer.plot_indicator_contributions(
            ranked_results[0], "integration_contributions.png"
        )
        print(f"  ✓ 指标贡献度: {contrib_file}")
        
        # 对比分析
        compare_file = visualizer.plot_comparison(ranked_results, "integration_comparison.png")
        print(f"  ✓ 目标对比: {compare_file}")
        
    except Exception as e:
        print(f"  ⚠ 可视化生成警告: {e}")
    
    # 获取统计信息
    stats = evaluator.get_threat_statistics(ranked_results)
    
    print("\n\n战场态势统计：")
    print(f"  总敌人数: {stats['total_enemies']}")
    print(f"  威胁等级分布: {stats['threat_level_distribution']}")
    print(f"  平均威胁得分: {stats['score_statistics']['mean']:.3f}")
    print(f"  得分范围: [{stats['score_statistics']['min']:.3f}, "
          f"{stats['score_statistics']['max']:.3f}]")
    
    print("\n✓ 集成测试完成")


def main():
    """主测试函数"""
    print("=" * 80)
    print("IFS威胁评估系统 - 完整测试套件")
    print("=" * 80)
    print("基于论文：《地面作战目标威胁评估多属性指标处理方法》")
    print("=" * 80)
    
    all_runners = []
    
    # 运行所有测试
    try:
        all_runners.append(test_ifs_core())
        all_runners.append(test_threat_indicators())
        all_runners.append(test_threat_evaluator())
        all_runners.append(test_terrain_analyzer())
        test_performance()
        test_integration()
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 总体测试报告
    print("\n" + "=" * 80)
    print("总体测试报告")
    print("=" * 80)
    
    total_passed = sum(r.passed for r in all_runners)
    total_failed = sum(r.failed for r in all_runners)
    total_tests = total_passed + total_failed
    
    if total_tests > 0:
        success_rate = total_passed / total_tests * 100
        print(f"总测试数: {total_tests}")
        print(f"通过: {total_passed} ({success_rate:.1f}%)")
        print(f"失败: {total_failed}")
        
        if total_failed == 0:
            print("\n🎉 所有测试通过！系统运行正常。")
        else:
            print(f"\n⚠️  有 {total_failed} 个测试失败，需要检查。")
    
    print("=" * 80)


if __name__ == "__main__":
    main()

