"""
测试Generate_Picture中的30个城市战场场景

使用IFS威胁评估系统分析urban_battlefield_data.json中的所有场景，
并生成详细的威胁评估报告和可视化结果。
"""

import json
import os
import sys
from typing import Dict, List
import numpy as np

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from threat_evaluator import IFSThreatEvaluator
from terrain_analyzer import TerrainAnalyzer
from visualizer import ThreatVisualizer


class UrbanBattlefieldTester:
    """城市战场威胁评估测试器"""
    
    def __init__(self, data_file: str, terrain_file: str = None):
        """
        初始化测试器
        
        Args:
            data_file: urban_battlefield_data.json文件路径
            terrain_file: TerrainData JSON文件路径（可选）
        """
        self.data_file = data_file
        self.evaluator = IFSThreatEvaluator()
        self.visualizer = ThreatVisualizer(output_dir="examples/urban_tests")
        
        # 加载地形分析器（如果提供了地形文件）
        self.terrain_analyzer = None
        if terrain_file and os.path.exists(terrain_file):
            self.terrain_analyzer = TerrainAnalyzer(terrain_file)
            print(f"✓ 地形分析器已加载: {terrain_file}")
        
        # 加载战场数据
        self.battlefield_data = self._load_data()
        print(f"✓ 战场数据已加载: {len(self.battlefield_data['images'])}个场景")
    
    def _load_data(self) -> Dict:
        """加载JSON数据"""
        with open(self.data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_single_scenario(self, image_data: Dict, 
                            use_terrain: bool = False) -> Dict:
        """
        测试单个战场场景
        
        Args:
            image_data: 图片数据（包含enemies列表）
            use_terrain: 是否使用地形分析
        
        Returns:
            评估结果字典
        """
        enemies = image_data['enemies']
        player_pos = (0, 0)  # 玩家在中心
        
        # 如果启用地形分析
        terrain_data = None
        if use_terrain and self.terrain_analyzer:
            terrain_data = self.terrain_analyzer.batch_analyze_enemies(
                enemies, player_pos
            )
        
        # 执行威胁评估
        ranked_results = self.evaluator.rank_targets(
            enemies, 
            player_pos, 
            terrain_data
        )
        
        # 获取统计信息
        stats = self.evaluator.get_threat_statistics(ranked_results)
        
        return {
            'image_id': image_data['imageId'],
            'filename': image_data['filename'],
            'tactic': image_data['tacticNameCN'],
            'tactic_type': image_data['tacticType'],
            'enemy_count': image_data['enemyCount'],
            'ranked_results': ranked_results,
            'statistics': stats,
            'terrain_data': terrain_data
        }
    
    def test_all_scenarios(self, use_terrain: bool = False,
                          generate_visualizations: bool = True) -> List[Dict]:
        """
        测试所有30个场景
        
        Args:
            use_terrain: 是否使用地形分析
            generate_visualizations: 是否生成可视化图表
        
        Returns:
            所有场景的评估结果列表
        """
        print("\n" + "=" * 80)
        print("开始测试30个城市战场场景")
        print("=" * 80)
        
        all_results = []
        images = self.battlefield_data['images']
        
        for idx, image_data in enumerate(images, 1):
            print(f"\n[{idx}/30] 测试场景: {image_data['filename']}")
            print(f"  战术: {image_data['tacticNameCN']} ({image_data['tacticType']})")
            print(f"  敌人数: {image_data['enemyCount']}")
            
            # 执行评估
            result = self.test_single_scenario(image_data, use_terrain)
            all_results.append(result)
            
            # 显示前3名威胁目标
            top3 = result['ranked_results'][:3]
            print(f"  Top 3威胁:")
            for r in top3:
                print(f"    #{r['rank']} 敌人#{r['enemy_id']}: "
                      f"得分={r['comprehensive_threat_score']:.3f}, "
                      f"等级={r['threat_level']}")
            
            # 生成可视化（可选）
            if generate_visualizations and idx <= 5:  # 只为前5个场景生成
                self._generate_visualization(result, idx)
        
        return all_results
    
    def _generate_visualization(self, result: Dict, scene_number: int):
        """为单个场景生成可视化"""
        try:
            # 威胁排名
            self.visualizer.plot_threat_ranking(
                result['ranked_results'],
                output_file=f"scene{scene_number:02d}_ranking.png",
                top_n=min(10, len(result['ranked_results']))
            )
            
            # 最高威胁的雷达图
            if result['ranked_results']:
                self.visualizer.plot_radar_chart(
                    result['ranked_results'][0],
                    output_file=f"scene{scene_number:02d}_radar.png"
                )
            
            print(f"  ✓ 可视化已生成")
        except Exception as e:
            print(f"  ⚠ 可视化生成失败: {e}")
    
    def generate_comprehensive_report(self, all_results: List[Dict]) -> Dict:
        """
        生成综合报告
        
        Args:
            all_results: 所有场景的评估结果
        
        Returns:
            综合统计报告
        """
        print("\n" + "=" * 80)
        print("生成综合分析报告")
        print("=" * 80)
        
        # 按场景类型统计
        type_stats = {
            'Type1_Sparse': [],
            'Type2_Dense': [],
            'Type3_Fast': []
        }
        
        # 按战术类型统计
        tactic_stats = {}
        
        for result in all_results:
            # 按图片类型分类
            img_type = result['filename'].split('_')[0]
            if img_type == 'type1':
                type_stats['Type1_Sparse'].append(result)
            elif img_type == 'type2':
                type_stats['Type2_Dense'].append(result)
            elif img_type == 'type3':
                type_stats['Type3_Fast'].append(result)
            
            # 按战术分类
            tactic = result['tactic']
            if tactic not in tactic_stats:
                tactic_stats[tactic] = []
            tactic_stats[tactic].append(result)
        
        # 生成统计信息
        report = {
            'total_scenarios': len(all_results),
            'type_statistics': {},
            'tactic_statistics': {},
            'overall_statistics': {}
        }
        
        # 类型统计
        print("\n【按场景类型统计】")
        for type_name, results in type_stats.items():
            if not results:
                continue
            
            avg_threat = np.mean([
                r['statistics']['score_statistics']['mean'] 
                for r in results
            ])
            
            threat_distribution = {
                'critical': 0, 'high': 0, 'medium': 0, 'low': 0
            }
            for r in results:
                for level, count in r['statistics']['threat_level_distribution'].items():
                    threat_distribution[level] += count
            
            report['type_statistics'][type_name] = {
                'scenario_count': len(results),
                'avg_threat_score': avg_threat,
                'threat_distribution': threat_distribution
            }
            
            print(f"\n{type_name} (共{len(results)}个场景):")
            print(f"  平均威胁得分: {avg_threat:.3f}")
            print(f"  威胁分布: {threat_distribution}")
        
        # 战术统计
        print("\n【按战术类型统计】")
        for tactic_name, results in tactic_stats.items():
            avg_threat = np.mean([
                r['statistics']['score_statistics']['mean'] 
                for r in results
            ])
            
            max_threat = max([
                r['statistics']['score_statistics']['max'] 
                for r in results
            ])
            
            report['tactic_statistics'][tactic_name] = {
                'scenario_count': len(results),
                'avg_threat_score': avg_threat,
                'max_threat_score': max_threat
            }
            
            print(f"\n{tactic_name}:")
            print(f"  场景数: {len(results)}")
            print(f"  平均威胁: {avg_threat:.3f}")
            print(f"  最高威胁: {max_threat:.3f}")
        
        # 总体统计
        print("\n【总体统计】")
        all_scores = []
        all_threat_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for result in all_results:
            all_scores.extend([
                r['comprehensive_threat_score'] 
                for r in result['ranked_results']
            ])
            for level, count in result['statistics']['threat_level_distribution'].items():
                all_threat_counts[level] += count
        
        report['overall_statistics'] = {
            'total_enemies': sum(all_threat_counts.values()),
            'avg_threat_score': np.mean(all_scores),
            'median_threat_score': np.median(all_scores),
            'std_threat_score': np.std(all_scores),
            'threat_distribution': all_threat_counts
        }
        
        print(f"\n总敌人数: {report['overall_statistics']['total_enemies']}")
        print(f"平均威胁得分: {report['overall_statistics']['avg_threat_score']:.3f}")
        print(f"中位数: {report['overall_statistics']['median_threat_score']:.3f}")
        print(f"标准差: {report['overall_statistics']['std_threat_score']:.3f}")
        print(f"威胁分布: {all_threat_counts}")
        
        # 找出最危险的场景
        most_dangerous = max(all_results, 
                            key=lambda x: x['statistics']['score_statistics']['max'])
        print(f"\n最危险场景: {most_dangerous['filename']}")
        print(f"  战术: {most_dangerous['tactic']}")
        print(f"  最高威胁得分: {most_dangerous['statistics']['score_statistics']['max']:.3f}")
        
        return report
    
    def save_report(self, all_results: List[Dict], report: Dict, 
                   output_file: str = "examples/urban_tests/evaluation_report.json"):
        """保存评估报告为JSON文件"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 准备可序列化的数据（过滤掉不可序列化的对象）
        serializable_results = []
        for result in all_results:
            # 提取统计信息（过滤IFS对象）
            stats = result['statistics']
            serializable_stats = {
                'total_enemies': stats['total_enemies'],
                'threat_level_distribution': stats['threat_level_distribution'],
                'score_statistics': {
                    'mean': float(stats['score_statistics']['mean']),
                    'median': float(stats['score_statistics']['median']),
                    'std': float(stats['score_statistics']['std']),
                    'min': float(stats['score_statistics']['min']),
                    'max': float(stats['score_statistics']['max'])
                }
            }
            
            serializable_results.append({
                'image_id': result['image_id'],
                'filename': result['filename'],
                'tactic': result['tactic'],
                'tactic_type': result['tactic_type'],
                'enemy_count': result['enemy_count'],
                'top_threats': [
                    {
                        'enemy_id': r['enemy_id'],
                        'rank': r['rank'],
                        'threat_score': float(r['comprehensive_threat_score']),
                        'threat_level': r['threat_level'],
                        'distance': float(r['distance'])
                    }
                    for r in result['ranked_results'][:5]  # 只保存前5名
                ],
                'statistics': serializable_stats
            })
        
        output_data = {
            'evaluation_summary': report,
            'scenario_results': serializable_results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 评估报告已保存: {output_file}")


def main():
    """主函数"""
    print("=" * 80)
    print("IFS威胁评估系统 - 城市战场30场景测试")
    print("=" * 80)
    
    # 文件路径
    data_file = "../Generate_Picture/urban_battlefield_data.json"
    terrain_file = "../Generate_Picture/TerrainData_20251219_191755.json"
    
    # 检查文件是否存在
    if not os.path.exists(data_file):
        print(f"❌ 错误: 找不到数据文件 {data_file}")
        return
    
    # 创建测试器
    tester = UrbanBattlefieldTester(data_file, terrain_file)
    
    # 询问是否使用地形分析
    print("\n选项:")
    print("  1. 基础评估（不含地形分析）")
    print("  2. 完整评估（含地形分析，较慢）")
    
    choice = input("\n请选择 (1/2, 默认1): ").strip() or "1"
    use_terrain = (choice == "2")
    
    # 询问是否生成可视化
    gen_viz = input("是否生成可视化图表（前5个场景）? (Y/N, 默认Y): ").strip().upper() != "N"
    
    # 执行测试
    print(f"\n{'='*80}")
    print(f"开始评估...")
    print(f"地形分析: {'启用' if use_terrain else '禁用'}")
    print(f"可视化: {'启用' if gen_viz else '禁用'}")
    print(f"{'='*80}")
    
    try:
        # 测试所有场景
        all_results = tester.test_all_scenarios(
            use_terrain=use_terrain,
            generate_visualizations=gen_viz
        )
        
        # 生成综合报告
        report = tester.generate_comprehensive_report(all_results)
        
        # 保存报告
        tester.save_report(all_results, report)
        
        print("\n" + "=" * 80)
        print("✅ 所有测试完成！")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

