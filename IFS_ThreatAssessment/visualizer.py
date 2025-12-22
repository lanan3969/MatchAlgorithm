"""
威胁度可视化工具

实现功能：
1. 威胁度热力图（基于战场地形）
2. 威胁指标雷达图
3. 目标对比分析图
4. 威胁排名柱状图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Circle, Rectangle, Wedge, FancyBboxPatch
import numpy as np
from typing import Dict, List, Tuple, Optional
import os


class ThreatVisualizer:
    """威胁可视化工具类"""
    
    def __init__(self, output_dir: str = "examples"):
        """
        初始化可视化工具
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置中文字体（尝试多个选项）
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 威胁等级颜色映射
        self.threat_colors = {
            'critical': '#FF0000',  # 红色
            'high': '#FF6600',      # 橙红色
            'medium': '#FFAA00',    # 橙黄色
            'low': '#00AA00'        # 绿色
        }
    
    def plot_threat_heatmap(self,
                           evaluation_results: List[Dict],
                           terrain_data: Dict = None,
                           player_pos: Tuple[float, float] = (0, 0),
                           output_file: str = "threat_heatmap.png",
                           show_details: bool = True) -> str:
        """
        绘制威胁度热力图
        
        Args:
            evaluation_results: 威胁评估结果列表
            terrain_data: 地形数据（建筑物、障碍物等）
            player_pos: 玩家位置
            output_file: 输出文件名
            show_details: 是否显示详细标注
        
        Returns:
            保存的文件路径
        """
        fig, ax = plt.subplots(figsize=(16, 16), dpi=100)
        
        # 设置坐标范围
        coord_range = 50
        ax.set_xlim(-coord_range, coord_range)
        ax.set_ylim(-coord_range, coord_range)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlabel('X (meters)', fontsize=12)
        ax.set_ylabel('Z (meters)', fontsize=12)
        ax.set_title('Threat Assessment Heatmap', fontsize=16, fontweight='bold')
        
        # 1. 绘制地形（如果有）
        if terrain_data:
            self._draw_terrain(ax, terrain_data)
        
        # 2. 绘制同心圆（10m, 20m）
        for radius in [10, 20]:
            circle = Circle(player_pos, radius, fill=False, 
                          edgecolor='blue', linestyle='--', linewidth=1.5, alpha=0.5)
            ax.add_patch(circle)
            ax.text(player_pos[0] + radius, player_pos[1], f'{radius}m', 
                   fontsize=9, color='blue', alpha=0.7)
        
        # 3. 绘制玩家位置
        ax.plot(player_pos[0], player_pos[1], '*', 
               color='blue', markersize=20, markeredgecolor='darkblue', markeredgewidth=2)
        ax.text(player_pos[0], player_pos[1] - 3, 'Player', 
               fontsize=11, ha='center', fontweight='bold', color='blue')
        
        # 4. 绘制敌人及威胁度
        for result in evaluation_results:
            enemy_id = result['enemy_id']
            distance = result['distance']
            threat_score = result['comprehensive_threat_score']
            threat_level = result['threat_level']
            
            # 从indicator_details获取位置和类型
            enemy_type = result['indicator_details']['type']['type']
            
            # 计算敌人位置（从距离和角度反推，或者从原始数据获取）
            # 这里简化处理：从evaluation_results中我们需要保存原始位置
            # 实际使用时，应该在evaluate时保存x, z坐标
            # 这里假设我们能从distance和其他信息推断位置
            # 为了演示，我们使用一个占位符方法
            
            # 获取颜色（基于威胁等级）
            color = self.threat_colors.get(threat_level, '#AAAAAA')
            
            # 威胁度映射到大小（6-30像素）
            marker_size = 10 + int(20 * (threat_score + 1) / 2)  # score范围[-1, 1]
            
            # 根据类型选择标记
            if enemy_type == 'ifv':
                marker = 's'  # 方形
                marker_size = marker_size * 1.5
            else:
                marker = 'o'  # 圆形
            
            # 由于我们没有直接的x, z坐标，这里用一个变通方法
            # 实际使用时，应该在调用时传入完整的敌人信息
            # 暂时用随机位置演示（仅用于结构展示）
            angle = np.random.uniform(0, 2*np.pi)
            ex = player_pos[0] + distance * np.cos(angle)
            ez = player_pos[1] + distance * np.sin(angle)
            
            # 绘制敌人
            ax.plot(ex, ez, marker, color=color, markersize=marker_size,
                   markeredgecolor='darkred' if threat_level in ['critical', 'high'] else 'black',
                   markeredgewidth=2, alpha=0.8)
            
            # 显示详细信息
            if show_details:
                # 敌人编号
                ax.text(ex, ez, str(enemy_id), fontsize=8, ha='center', va='center',
                       color='white', fontweight='bold')
                
                # 威胁得分标注
                score_text = f"{threat_score:.2f}"
                ax.text(ex, ez - 2, score_text, fontsize=7, ha='center',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.7, edgecolor='none'))
        
        # 5. 添加图例
        legend_elements = [
            plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='blue', 
                      markersize=15, label='Player'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.threat_colors['critical'],
                      markersize=10, label='Critical Threat'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.threat_colors['high'],
                      markersize=10, label='High Threat'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.threat_colors['medium'],
                      markersize=10, label='Medium Threat'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.threat_colors['low'],
                      markersize=10, label='Low Threat'),
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10, framealpha=0.9)
        
        # 保存图像
        output_path = os.path.join(self.output_dir, output_file)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def _draw_terrain(self, ax, terrain_data: Dict):
        """绘制地形元素（建筑物、障碍物等）"""
        # 绘制建筑物
        if 'buildings' in terrain_data:
            for building in terrain_data['buildings']:
                bx, bz = building['x'], building['z']
                bw, bd = building['width'], building['depth']
                
                rect = Rectangle((bx - bw/2, bz - bd/2), bw, bd,
                               facecolor='gray', edgecolor='darkgray',
                               alpha=0.3, linewidth=1.5)
                ax.add_patch(rect)
                
                # 建筑物标签
                ax.text(bx, bz, f"B{building.get('id', '?')}", 
                       fontsize=8, ha='center', va='center', color='gray', alpha=0.7)
        
        # 绘制障碍物
        if 'obstacles' in terrain_data:
            for obstacle in terrain_data['obstacles']:
                ox, oz = obstacle['x'], obstacle['z']
                ow, od = obstacle['width'], obstacle['depth']
                
                obstacle_type = obstacle.get('type', 'unknown')
                if obstacle_type == 'Cover':
                    color = 'brown'
                elif obstacle_type == 'Barrier':
                    color = 'black'
                else:
                    color = 'darkblue'
                
                rect = Rectangle((ox - ow/2, oz - od/2), ow, od,
                               facecolor=color, edgecolor=color,
                               alpha=0.4, linewidth=1)
                ax.add_patch(rect)
        
        # 绘制巷道
        if 'alleys' in terrain_data:
            for alley in terrain_data['alleys']:
                x1, z1 = alley['start_x'], alley['start_z']
                x2, z2 = alley['end_x'], alley['end_z']
                width = alley['width']
                
                ax.plot([x1, x2], [z1, z2], color='lightgray', 
                       linewidth=width*2, alpha=0.3, solid_capstyle='round')
    
    def plot_radar_chart(self,
                        evaluation_result: Dict,
                        output_file: str = "threat_radar.png") -> str:
        """
        绘制单个目标的威胁指标雷达图
        
        Args:
            evaluation_result: 单个目标的评估结果
            output_file: 输出文件名
        
        Returns:
            保存的文件路径
        """
        # 提取6个指标的威胁得分
        indicators = evaluation_result['indicator_details']
        
        categories = []
        scores = []
        
        indicator_order = ['distance', 'type', 'speed', 'angle', 'visibility', 'environment']
        indicator_labels = {
            'distance': 'Distance',
            'type': 'Type',
            'speed': 'Speed',
            'angle': 'Angle',
            'visibility': 'Visibility',
            'environment': 'Environment'
        }
        
        for ind_name in indicator_order:
            if ind_name in indicators:
                categories.append(indicator_labels[ind_name])
                # 将得分从[-1, 1]映射到[0, 1]
                score = (indicators[ind_name]['threat_score'] + 1) / 2
                scores.append(score)
        
        # 创建雷达图
        num_vars = len(categories)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        scores += scores[:1]  # 闭合图形
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        # 绘制数据
        ax.plot(angles, scores, 'o-', linewidth=2, color='red', label='Threat Score')
        ax.fill(angles, scores, alpha=0.25, color='red')
        
        # 设置标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=11)
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=9)
        ax.grid(True, alpha=0.3)
        
        # 标题
        enemy_id = evaluation_result['enemy_id']
        threat_level = evaluation_result['threat_level']
        threat_score = evaluation_result['comprehensive_threat_score']
        
        plt.title(f'Enemy #{enemy_id} Threat Indicators\n'
                 f'Level: {threat_level.upper()} (Score: {threat_score:.3f})',
                 fontsize=14, fontweight='bold', pad=20)
        
        # 保存
        output_path = os.path.join(self.output_dir, output_file)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def plot_threat_ranking(self,
                           evaluation_results: List[Dict],
                           output_file: str = "threat_ranking.png",
                           top_n: int = 10) -> str:
        """
        绘制威胁排名柱状图
        
        Args:
            evaluation_results: 评估结果列表（已排序）
            output_file: 输出文件名
            top_n: 显示前N个目标
        
        Returns:
            保存的文件路径
        """
        # 取前N个
        top_results = evaluation_results[:top_n]
        
        enemy_ids = [f"Enemy #{r['enemy_id']}" for r in top_results]
        threat_scores = [r['comprehensive_threat_score'] for r in top_results]
        threat_levels = [r['threat_level'] for r in top_results]
        
        # 获取颜色
        colors = [self.threat_colors.get(level, '#AAAAAA') for level in threat_levels]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 8))
        
        bars = ax.barh(enemy_ids, threat_scores, color=colors, edgecolor='black', linewidth=1.5)
        
        # 添加数值标签
        for i, (bar, score) in enumerate(zip(bars, threat_scores)):
            ax.text(score + 0.02, bar.get_y() + bar.get_height()/2, 
                   f'{score:.3f}', va='center', fontsize=10, fontweight='bold')
        
        # 设置坐标轴
        ax.set_xlabel('Threat Score', fontsize=12, fontweight='bold')
        ax.set_ylabel('Enemy', fontsize=12, fontweight='bold')
        ax.set_title(f'Top {len(top_results)} Threat Ranking', fontsize=14, fontweight='bold')
        ax.set_xlim(-1, 1)
        ax.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.grid(axis='x', alpha=0.3)
        
        # 添加威胁等级图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor=self.threat_colors['critical'], label='Critical'),
            Patch(facecolor=self.threat_colors['high'], label='High'),
            Patch(facecolor=self.threat_colors['medium'], label='Medium'),
            Patch(facecolor=self.threat_colors['low'], label='Low')
        ]
        ax.legend(handles=legend_elements, loc='lower right', fontsize=10)
        
        # 保存
        output_path = os.path.join(self.output_dir, output_file)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def plot_indicator_contributions(self,
                                    evaluation_result: Dict,
                                    output_file: str = "indicator_contributions.png") -> str:
        """
        绘制各指标对综合威胁度的贡献饼图
        
        Args:
            evaluation_result: 单个目标的评估结果
            output_file: 输出文件名
        
        Returns:
            保存的文件路径
        """
        contributions = evaluation_result['weighted_aggregation']['contributions']
        
        labels = []
        values = []
        colors_list = []
        
        color_palette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']
        
        for i, (indicator_name, contrib_data) in enumerate(contributions.items()):
            labels.append(f"{indicator_name.capitalize()}\n({contrib_data['weight']:.2f})")
            values.append(abs(contrib_data['contribution']))
            colors_list.append(color_palette[i % len(color_palette)])
        
        # 创建饼图
        fig, ax = plt.subplots(figsize=(10, 8))
        
        wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors_list,
                                          autopct='%1.1f%%', startangle=90,
                                          textprops={'fontsize': 10, 'fontweight': 'bold'})
        
        # 设置标题
        enemy_id = evaluation_result['enemy_id']
        threat_score = evaluation_result['comprehensive_threat_score']
        
        plt.title(f'Enemy #{enemy_id} - Indicator Contributions\n'
                 f'Comprehensive Threat Score: {threat_score:.3f}',
                 fontsize=14, fontweight='bold', pad=20)
        
        # 保存
        output_path = os.path.join(self.output_dir, output_file)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def plot_comparison(self,
                       evaluation_results: List[Dict],
                       output_file: str = "threat_comparison.png") -> str:
        """
        绘制多个目标的对比分析图
        
        Args:
            evaluation_results: 多个目标的评估结果列表
            output_file: 输出文件名
        
        Returns:
            保存的文件路径
        """
        if len(evaluation_results) > 5:
            evaluation_results = evaluation_results[:5]  # 最多对比5个
        
        num_enemies = len(evaluation_results)
        
        # 创建子图
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Multi-Target Threat Comparison', fontsize=16, fontweight='bold')
        
        indicators_order = ['distance', 'type', 'speed', 'angle', 'visibility', 'environment']
        indicator_labels = {
            'distance': 'Distance', 'type': 'Type', 'speed': 'Speed',
            'angle': 'Angle', 'visibility': 'Visibility', 'environment': 'Environment'
        }
        
        # 为每个指标绘制对比柱状图
        for idx, indicator_name in enumerate(indicators_order):
            row = idx // 3
            col = idx % 3
            ax = axes[row, col]
            
            enemy_labels = [f"E{r['enemy_id']}" for r in evaluation_results]
            scores = []
            colors = []
            
            for result in evaluation_results:
                if indicator_name in result['indicator_details']:
                    score = result['indicator_details'][indicator_name]['threat_score']
                    scores.append((score + 1) / 2)  # 映射到[0, 1]
                    colors.append(self.threat_colors.get(result['threat_level'], '#AAAAAA'))
                else:
                    scores.append(0)
                    colors.append('#CCCCCC')
            
            bars = ax.bar(enemy_labels, scores, color=colors, edgecolor='black', linewidth=1.5)
            
            ax.set_title(indicator_labels[indicator_name], fontsize=12, fontweight='bold')
            ax.set_ylabel('Normalized Score', fontsize=10)
            ax.set_ylim(0, 1)
            ax.grid(axis='y', alpha=0.3)
            
            # 添加数值标签
            for bar, score in zip(bars, scores):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height + 0.02,
                       f'{score:.2f}', ha='center', va='bottom', fontsize=9)
        
        # 保存
        output_path = os.path.join(self.output_dir, output_file)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path


if __name__ == "__main__":
    # 测试代码
    print("=" * 80)
    print("威胁可视化工具测试")
    print("=" * 80)
    
    # 创建可视化工具
    visualizer = ThreatVisualizer(output_dir="examples")
    
    # 模拟评估结果数据
    mock_results = [
        {
            'enemy_id': 1,
            'comprehensive_threat_score': 0.75,
            'threat_level': 'high',
            'distance': 15.0,
            'ifs_values': {'membership': 0.85, 'non_membership': 0.10, 'hesitancy': 0.05},
            'indicator_details': {
                'distance': {'threat_score': 0.8, 'threat_level': 'high'},
                'type': {'threat_score': 0.85, 'threat_level': 'high', 'type': 'ifv'},
                'speed': {'threat_score': 0.6, 'threat_level': 'medium'},
                'angle': {'threat_score': 0.9, 'threat_level': 'high'},
                'visibility': {'threat_score': 0.75, 'threat_level': 'high'},
                'environment': {'threat_score': 0.5, 'threat_level': 'medium'}
            },
            'weighted_aggregation': {
                'contributions': {
                    'distance': {'weight': 0.30, 'contribution': 0.24, 'percentage': 32},
                    'type': {'weight': 0.25, 'contribution': 0.21, 'percentage': 28},
                    'speed': {'weight': 0.20, 'contribution': 0.12, 'percentage': 16},
                    'angle': {'weight': 0.15, 'contribution': 0.14, 'percentage': 18},
                    'visibility': {'weight': 0.06, 'contribution': 0.05, 'percentage': 4},
                    'environment': {'weight': 0.04, 'contribution': 0.02, 'percentage': 2}
                }
            }
        },
        {
            'enemy_id': 2,
            'comprehensive_threat_score': 0.35,
            'threat_level': 'medium',
            'distance': 30.0,
            'ifs_values': {'membership': 0.60, 'non_membership': 0.25, 'hesitancy': 0.15},
            'indicator_details': {
                'distance': {'threat_score': 0.4, 'threat_level': 'medium'},
                'type': {'threat_score': 0.6, 'threat_level': 'medium', 'type': 'soldier'},
                'speed': {'threat_score': 0.3, 'threat_level': 'low'},
                'angle': {'threat_score': 0.2, 'threat_level': 'low'},
                'visibility': {'threat_score': 0.5, 'threat_level': 'medium'},
                'environment': {'threat_score': 0.4, 'threat_level': 'medium'}
            },
            'weighted_aggregation': {
                'contributions': {
                    'distance': {'weight': 0.30, 'contribution': 0.12, 'percentage': 34},
                    'type': {'weight': 0.25, 'contribution': 0.15, 'percentage': 43},
                    'speed': {'weight': 0.20, 'contribution': 0.06, 'percentage': 17},
                    'angle': {'weight': 0.15, 'contribution': 0.03, 'percentage': 9},
                    'visibility': {'weight': 0.06, 'contribution': 0.03, 'percentage': 9},
                    'environment': {'weight': 0.04, 'contribution': 0.02, 'percentage': 6}
                }
            }
        }
    ]
    
    print("\n【测试1】生成威胁排名柱状图...")
    ranking_path = visualizer.plot_threat_ranking(mock_results, "test_ranking.png")
    print(f"✓ 保存至: {ranking_path}")
    
    print("\n【测试2】生成雷达图...")
    radar_path = visualizer.plot_radar_chart(mock_results[0], "test_radar.png")
    print(f"✓ 保存至: {radar_path}")
    
    print("\n【测试3】生成指标贡献饼图...")
    pie_path = visualizer.plot_indicator_contributions(mock_results[0], "test_contributions.png")
    print(f"✓ 保存至: {pie_path}")
    
    print("\n【测试4】生成对比分析图...")
    comparison_path = visualizer.plot_comparison(mock_results, "test_comparison.png")
    print(f"✓ 保存至: {comparison_path}")
    
    print("\n" + "=" * 80)
    print("测试完成！生成的图片保存在 examples/ 文件夹中")

