"""
战场地图批量测试脚本
测试urban_battlefield_data(8).json中20张地图的威胁态势评估
"""

import json
import logging
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import math

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入必要的模块
from models import Target, Position, GameData
from threat_analyzer import find_most_threatening_target
from situation_awareness import calculate_all_directions_threat


def load_battlefield_json(json_path: str) -> dict:
    """加载战场JSON数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def convert_enemy_to_target(enemy: dict, player_pos: Position) -> Target:
    """
    将JSON中的敌人数据转换为Target对象
    
    Args:
        enemy: JSON中的敌人字典
        player_pos: 玩家位置
    
    Returns:
        Target对象
    """
    # 敌人位置（JSON使用x, z坐标）
    enemy_pos = Position(x=enemy['x'], y=0.0, z=enemy['z'])
    
    # 计算距离
    dx = enemy_pos.x - player_pos.x
    dz = enemy_pos.z - player_pos.z
    distance = (dx**2 + dz**2) ** 0.5
    
    # 计算角度（相对于玩家的正北方向）
    angle = math.degrees(math.atan2(dx, dz))
    if angle < 0:
        angle += 360
    
    # 类型映射：uav -> Drone, soldier -> Soldier
    enemy_type = "Drone" if enemy['type'].lower() == 'uav' else "Soldier"
    
    return Target(
        id=enemy['id'],
        type=enemy_type,
        position=enemy_pos,
        distance=distance,
        angle=angle,
        velocity=enemy.get('speed'),
        direction=enemy.get('direction'),
        speed=enemy.get('speed')
    )


def find_most_threatening_direction(direction_threats: Dict[int, float]) -> Tuple[int, float]:
    """
    找出最具威胁的方向
    
    Args:
        direction_threats: 16个方向的威胁度字典
    
    Returns:
        (方向ID, 威胁度值)
    """
    max_direction = max(direction_threats.items(), key=lambda x: x[1])
    return max_direction


def get_direction_name(direction_id: int) -> str:
    """获取方向名称"""
    direction_names = [
        "正北(0°)", "北偏东(22.5°)", "东北(45°)", "东偏北(67.5°)",
        "正东(90°)", "东偏南(112.5°)", "东南(135°)", "南偏东(157.5°)",
        "正南(180°)", "南偏西(202.5°)", "西南(225°)", "西偏南(247.5°)",
        "正西(270°)", "西偏北(292.5°)", "西北(315°)", "北偏西(337.5°)"
    ]
    return direction_names[direction_id] if 0 <= direction_id < 16 else "未知"


def test_single_battlefield(
    image_data: dict,
    player_pos: Position,
    terrain_data: Optional[dict] = None
) -> dict:
    """
    测试单张战场地图
    
    Args:
        image_data: 图像数据字典
        player_pos: 玩家位置
        terrain_data: 地形数据（可选）
    
    Returns:
        测试结果字典
    """
    # 转换敌人数据为Target对象
    targets = [convert_enemy_to_target(enemy, player_pos) for enemy in image_data['enemies']]
    
    # 创建GameData对象
    game_data = GameData(
        round=image_data['imageId'],
        playerPosition=player_pos,
        targets=targets,
        situationAwareness=False
    )
    
    # 1. 计算最具威胁的敌人（使用IFS）
    most_threatening = find_most_threatening_target(game_data)
    
    # 2. 计算16个方向的综合威胁（使用IFS）
    direction_threats = calculate_all_directions_threat(game_data)
    
    # 3. 找出最具威胁的方向
    most_threatening_dir_id, most_threatening_dir_score = find_most_threatening_direction(direction_threats)
    
    # 构建结果
    result = {
        'imageId': image_data['imageId'],
        'tacticType': image_data.get('tacticType', 'unknown'),
        'tacticNameCN': image_data.get('tacticNameCN', '未知'),
        'enemyCount': len(targets),
        'most_threatening_enemy': {
            'id': most_threatening.id if most_threatening else None,
            'type': most_threatening.type if most_threatening else None,
            'distance': round(most_threatening.distance, 2) if most_threatening else None,
            'angle': round(most_threatening.angle, 2) if most_threatening else None,
            'position': {
                'x': round(most_threatening.position.x, 2) if most_threatening else None,
                'z': round(most_threatening.position.z, 2) if most_threatening else None
            } if most_threatening else None
        },
        'most_threatening_direction': {
            'id': most_threatening_dir_id,
            'name': get_direction_name(most_threatening_dir_id),
            'threat_score': round(most_threatening_dir_score, 4)
        },
        'direction_threats': {i: round(direction_threats[i], 4) for i in range(16)}
    }
    
    return result


def save_results_to_json(results: List[dict], output_path: str):
    """保存结果到JSON文件"""
    output_data = {
        'metadata': {
            'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_maps': len(results),
            'evaluation_method': 'IFS (Intuitionistic Fuzzy Set)'
        },
        'results': results
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Results saved to: {output_path}")


def print_summary_table(results: List[dict]):
    """打印结果摘要表格"""
    print("\n" + "=" * 150)
    print(f"{'图像ID':<25} {'战术':<12} {'敌人数':<8} {'最威胁敌人':<15} {'距离':<8} {'最威胁方向':<20} {'方向威胁':<10}")
    print("=" * 150)
    
    for result in results:
        image_id = result['imageId']
        tactic = result['tacticNameCN']
        enemy_count = result['enemyCount']
        
        threat_enemy = result['most_threatening_enemy']
        enemy_info = f"ID{threat_enemy['id']}({threat_enemy['type']})" if threat_enemy['id'] else "N/A"
        distance = f"{threat_enemy['distance']:.1f}m" if threat_enemy['distance'] else "N/A"
        
        threat_dir = result['most_threatening_direction']
        dir_info = f"{threat_dir['name']}"
        dir_score = f"{threat_dir['threat_score']:.4f}"
        
        print(f"{image_id:<25} {tactic:<12} {enemy_count:<8} {enemy_info:<15} {distance:<8} {dir_info:<20} {dir_score:<10}")
    
    print("=" * 150 + "\n")


def main():
    """主函数"""
    # 配置路径
    json_path = "Generate_Picture/urban_battlefield_data(8).json"
    output_path = "test_results_ifs_battlefield.json"
    
    # 检查文件是否存在
    if not os.path.exists(json_path):
        logger.error(f"JSON file not found: {json_path}")
        return
    
    logger.info("=" * 80)
    logger.info("战场地图威胁态势评估测试")
    logger.info("=" * 80)
    logger.info(f"输入文件: {json_path}")
    logger.info(f"评估方法: IFS (Intuitionistic Fuzzy Set)")
    logger.info("=" * 80)
    
    # 加载JSON数据
    logger.info("Loading battlefield data...")
    data = load_battlefield_json(json_path)
    
    images = data.get('images', [])
    terrain = data.get('terrain')
    
    logger.info(f"Total images to test: {len(images)}")
    
    # 玩家位置（默认在原点）
    player_pos = Position(x=0.0, y=0.0, z=0.0)
    
    # 批量测试
    results = []
    for i, image_data in enumerate(images, 1):
        logger.info(f"\n[{i}/{len(images)}] Testing: {image_data['imageId']}")
        
        try:
            result = test_single_battlefield(image_data, player_pos, terrain)
            results.append(result)
            
            # 打印简要结果
            logger.info(f"  战术: {result['tacticNameCN']}")
            logger.info(f"  最威胁敌人: ID{result['most_threatening_enemy']['id']} "
                       f"({result['most_threatening_enemy']['type']}), "
                       f"距离 {result['most_threatening_enemy']['distance']}m")
            logger.info(f"  最威胁方向: {result['most_threatening_direction']['name']} "
                       f"(威胁度 {result['most_threatening_direction']['threat_score']:.4f})")
            
        except Exception as e:
            logger.error(f"  Error testing {image_data['imageId']}: {e}")
            continue
    
    # 保存结果
    logger.info("\n" + "=" * 80)
    logger.info("Saving results...")
    save_results_to_json(results, output_path)
    
    # 打印摘要表格
    print_summary_table(results)
    
    logger.info("=" * 80)
    logger.info("Test completed!")
    logger.info(f"Total maps tested: {len(results)}/{len(images)}")
    logger.info(f"Results saved to: {output_path}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

