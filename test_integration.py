"""IFS威胁评估系统集成测试"""
import unittest
import sys
import os
from unittest.mock import Mock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Target, Position, GameData
from threat_analyzer_ifs import IFSThreatAnalyzerAdapter, log_ifs_details


class TestTargetConversion(unittest.TestCase):
    """测试Target对象转换"""
    
    def setUp(self):
        """测试前准备"""
        self.adapter = IFSThreatAnalyzerAdapter()
    
    def test_convert_soldier_target(self):
        """测试转换Soldier类型目标"""
        target = Target(
            id=1,
            angle=45.0,
            distance=15.5,
            type="Soldier",
            position=Position(10.0, 0.0, -10.0),
            speed=5.0,
            direction=90.0
        )
        
        enemy = self.adapter.convert_target_to_enemy(target)
        
        self.assertEqual(enemy['id'], 1)
        self.assertEqual(enemy['type'], 'soldier')
        self.assertEqual(enemy['x'], 10.0)
        self.assertEqual(enemy['z'], -10.0)
        self.assertEqual(enemy['speed'], 5.0)
        self.assertEqual(enemy['direction'], 90.0)
    
    def test_convert_tank_target(self):
        """测试转换Tank类型目标"""
        target = Target(
            id=2,
            angle=-30.0,
            distance=25.0,
            type="Tank",
            position=Position(-15.0, 0.0, 20.0),
            speed=8.0,
            direction=180.0
        )
        
        enemy = self.adapter.convert_target_to_enemy(target)
        
        self.assertEqual(enemy['id'], 2)
        self.assertEqual(enemy['type'], 'ifv')  # Tank映射为ifv
        self.assertEqual(enemy['x'], -15.0)
        self.assertEqual(enemy['z'], 20.0)
        self.assertEqual(enemy['speed'], 8.0)
        self.assertEqual(enemy['direction'], 180.0)
    
    def test_convert_with_default_values(self):
        """测试转换带默认值的目标"""
        target = Target(
            id=3,
            angle=0.0,
            distance=10.0,
            type="Soldier",
            position=Position(0.0, 0.0, 10.0)
            # speed和direction使用默认值0.0
        )
        
        enemy = self.adapter.convert_target_to_enemy(target)
        
        self.assertEqual(enemy['speed'], 0.0)
        self.assertEqual(enemy['direction'], 0.0)


class TestIFSEvaluation(unittest.TestCase):
    """测试IFS评估功能"""
    
    def setUp(self):
        """测试前准备"""
        # 不加载地形数据的简单版本
        self.adapter = IFSThreatAnalyzerAdapter()
    
    def create_game_data(self, targets_data):
        """创建测试用的GameData对象"""
        targets = []
        for data in targets_data:
            target = Target(
                id=data['id'],
                angle=data['angle'],
                distance=data['distance'],
                type=data['type'],
                position=Position(data['x'], 0.0, data['z']),
                speed=data.get('speed', 0.0),
                direction=data.get('direction', 0.0)
            )
            targets.append(target)
        
        return GameData(
            round=1,
            playerPosition=Position(0.0, 0.0, 0.0),
            targets=targets
        )
    
    def test_find_most_threatening_single_target(self):
        """测试单个目标评估"""
        game_data = self.create_game_data([
            {
                'id': 1,
                'type': 'Soldier',
                'x': 10.0,
                'z': 0.0,
                'distance': 10.0,
                'angle': 0.0,
                'speed': 3.0,
                'direction': 180.0
            }
        ])
        
        target, details = self.adapter.find_most_threatening(game_data)
        
        self.assertIsNotNone(target)
        self.assertEqual(target.id, 1)
        self.assertIsNotNone(details)
        self.assertIn('comprehensive_threat_score', details)
        self.assertIn('threat_level', details)
    
    def test_find_most_threatening_multiple_targets(self):
        """测试多目标评估"""
        game_data = self.create_game_data([
            {
                'id': 1,
                'type': 'Soldier',
                'x': 20.0,
                'z': 0.0,
                'distance': 20.0,
                'angle': 0.0,
                'speed': 3.0,
                'direction': 180.0
            },
            {
                'id': 2,
                'type': 'Tank',
                'x': 5.0,
                'z': 0.0,
                'distance': 5.0,
                'angle': 0.0,
                'speed': 8.0,
                'direction': 180.0
            },
            {
                'id': 3,
                'type': 'Soldier',
                'x': 15.0,
                'z': 15.0,
                'distance': 21.2,
                'angle': 45.0,
                'speed': 4.0,
                'direction': 225.0
            }
        ])
        
        target, details = self.adapter.find_most_threatening(game_data)
        
        self.assertIsNotNone(target)
        # 应该选择最近的Tank（ID=2）
        self.assertEqual(target.id, 2)
        self.assertGreater(details['comprehensive_threat_score'], 0.5)
    
    def test_empty_targets(self):
        """测试空目标列表"""
        game_data = GameData(
            round=1,
            playerPosition=Position(0.0, 0.0, 0.0),
            targets=[]
        )
        
        target, details = self.adapter.find_most_threatening(game_data)
        
        self.assertIsNone(target)
        self.assertIsNone(details)
    
    def test_evaluate_all_targets(self):
        """测试评估所有目标并排序"""
        game_data = self.create_game_data([
            {
                'id': 1,
                'type': 'Soldier',
                'x': 30.0,
                'z': 0.0,
                'distance': 30.0,
                'angle': 0.0,
                'speed': 2.0,
                'direction': 180.0
            },
            {
                'id': 2,
                'type': 'Tank',
                'x': 10.0,
                'z': 0.0,
                'distance': 10.0,
                'angle': 0.0,
                'speed': 7.0,
                'direction': 180.0
            },
            {
                'id': 3,
                'type': 'Soldier',
                'x': 15.0,
                'z': 0.0,
                'distance': 15.0,
                'angle': 0.0,
                'speed': 5.0,
                'direction': 180.0
            }
        ])
        
        results = self.adapter.evaluate_all_targets(game_data)
        
        self.assertEqual(len(results), 3)
        # 验证结果按威胁度降序排列
        scores = [details['comprehensive_threat_score'] for _, details in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
        
        # 第一个应该是威胁最大的（ID=2或ID=3都合理，取决于IFS权重）
        most_threatening, most_details = results[0]
        self.assertIn(most_threatening.id, [2, 3])  # Tank或中距Soldier
        self.assertGreater(most_details['comprehensive_threat_score'], 0.3)  # 合理的威胁分数


class TestIFSDetailsLogging(unittest.TestCase):
    """测试IFS详细日志输出"""
    
    def test_log_ifs_details(self):
        """测试日志输出功能"""
        target = Target(
            id=1,
            angle=30.0,
            distance=12.5,
            type="Tank",
            position=Position(10.0, 0.0, 6.0),
            speed=8.0,
            direction=180.0
        )
        
        # 模拟IFS评估详情
        ifs_details = {
            'enemy_id': 1,
            'distance': 12.5,
            'comprehensive_threat_score': 0.752,
            'threat_level': 'high',
            'ifs_values': {
                'membership': 0.75,
                'non_membership': 0.18,
                'hesitancy': 0.07
            },
            'indicator_details': {
                'distance': {
                    'threat_score': 0.85,
                    'threat_level': 'very_high'
                },
                'type': {
                    'threat_score': 0.90,
                    'threat_level': 'very_high'
                },
                'speed': {
                    'threat_score': 0.70,
                    'threat_level': 'high'
                },
                'angle': {
                    'threat_score': 0.65,
                    'threat_level': 'medium'
                }
            },
            'weighted_aggregation': {
                'contributions': {
                    'distance': {
                        'weight': 0.30,
                        'contribution': 0.255,
                        'percentage': 33.9
                    },
                    'type': {
                        'weight': 0.25,
                        'contribution': 0.225,
                        'percentage': 29.9
                    },
                    'speed': {
                        'weight': 0.20,
                        'contribution': 0.140,
                        'percentage': 18.6
                    },
                    'angle': {
                        'weight': 0.15,
                        'contribution': 0.097,
                        'percentage': 12.9
                    }
                }
            }
        }
        
        # 测试日志函数不抛出异常
        try:
            log_ifs_details(target, ifs_details)
            test_passed = True
        except Exception:
            test_passed = False
        
        self.assertTrue(test_passed)


class TestDataModelBackwardCompatibility(unittest.TestCase):
    """测试数据模型向后兼容性"""
    
    def test_from_dict_with_new_fields(self):
        """测试解析包含新字段的数据"""
        data = {
            'round': 1,
            'playerPosition': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'targets': [
                {
                    'id': 1,
                    'angle': 30.0,
                    'distance': 15.0,
                    'type': 'Soldier',
                    'position': {'x': 10.0, 'y': 0.0, 'z': 8.0},
                    'speed': 5.0,
                    'direction': 180.0
                }
            ]
        }
        
        game_data = GameData.from_dict(data)
        
        self.assertEqual(len(game_data.targets), 1)
        target = game_data.targets[0]
        self.assertEqual(target.speed, 5.0)
        self.assertEqual(target.direction, 180.0)
    
    def test_from_dict_without_new_fields(self):
        """测试解析不包含新字段的旧数据"""
        data = {
            'round': 1,
            'playerPosition': {'x': 0.0, 'y': 0.0, 'z': 0.0},
            'targets': [
                {
                    'id': 1,
                    'angle': 30.0,
                    'distance': 15.0,
                    'type': 'Soldier',
                    'position': {'x': 10.0, 'y': 0.0, 'z': 8.0}
                    # 没有speed和direction字段
                }
            ]
        }
        
        game_data = GameData.from_dict(data)
        
        self.assertEqual(len(game_data.targets), 1)
        target = game_data.targets[0]
        # 应该使用默认值
        self.assertEqual(target.speed, 0.0)
        self.assertEqual(target.direction, 0.0)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTests(loader.loadTestsFromTestCase(TestTargetConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestIFSEvaluation))
    suite.addTests(loader.loadTestsFromTestCase(TestIFSDetailsLogging))
    suite.addTests(loader.loadTestsFromTestCase(TestDataModelBackwardCompatibility))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回结果
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 70)
    print("IFS威胁评估系统 - 集成测试")
    print("=" * 70)
    print()
    
    success = run_tests()
    
    print()
    print("=" * 70)
    if success:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败，请检查错误信息")
    print("=" * 70)
    
    sys.exit(0 if success else 1)

