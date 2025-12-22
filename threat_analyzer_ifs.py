"""IFS威胁评估适配器模块"""
import logging
import os
from typing import Optional, Tuple, Dict, List
from models import Target, GameData

logger = logging.getLogger(__name__)


class IFSThreatAnalyzerAdapter:
    """IFS威胁评估器的适配层，连接现有系统和IFS模块"""
    
    def __init__(self, terrain_data_path: str = None):
        """
        初始化IFS评估器
        
        Args:
            terrain_data_path: 地形数据JSON文件路径（可选）
        """
        try:
            # 导入IFS模块
            from IFS_ThreatAssessment.threat_evaluator import IFSThreatEvaluator
            from IFS_ThreatAssessment.terrain_analyzer import TerrainAnalyzer
            
            self.evaluator = IFSThreatEvaluator()
            self.terrain_analyzer = None
            
            # 加载地形分析器（如果提供了路径）
            if terrain_data_path and os.path.exists(terrain_data_path):
                try:
                    self.terrain_analyzer = TerrainAnalyzer(terrain_data_path)
                    logger.info(f"✓ Terrain analyzer loaded: {terrain_data_path}")
                except Exception as e:
                    logger.warning(f"Failed to load terrain analyzer: {e}")
                    self.terrain_analyzer = None
            
            logger.info("✓ IFS Threat Analyzer Adapter initialized successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import IFS modules: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize IFS adapter: {e}")
            raise
    
    def convert_target_to_enemy(self, target: Target) -> Dict:
        """
        转换Target对象为IFS所需的enemy字典
        
        Args:
            target: Target对象
            
        Returns:
            enemy字典，包含IFS评估所需的字段
        """
        # 类型映射: Tank -> ifv, Soldier -> soldier
        enemy_type = 'ifv' if target.type.lower() == 'tank' else 'soldier'
        
        return {
            'id': target.id,
            'type': enemy_type,
            'x': target.position.x,
            'z': target.position.z,
            'speed': target.speed,
            'direction': target.direction
        }
    
    def find_most_threatening(
        self, 
        game_data: GameData
    ) -> Tuple[Optional[Target], Optional[Dict]]:
        """
        使用IFS评估找出最高威胁目标
        
        Args:
            game_data: 游戏数据对象
            
        Returns:
            (最高威胁的Target对象, IFS评估详情字典) 或 (None, None)
        """
        if not game_data.targets:
            logger.warning("No targets to evaluate")
            return None, None
        
        try:
            # 转换数据格式
            enemies = [self.convert_target_to_enemy(t) for t in game_data.targets]
            player_pos = (game_data.playerPosition.x, game_data.playerPosition.z)
            
            logger.debug(f"Evaluating {len(enemies)} enemies at player position {player_pos}")
            
            # 地形分析（如果可用）
            terrain_data = None
            if self.terrain_analyzer:
                try:
                    terrain_data = self.terrain_analyzer.batch_analyze_enemies(
                        enemies, 
                        player_pos
                    )
                    logger.debug(f"Terrain analysis completed for {len(enemies)} enemies")
                except Exception as e:
                    logger.warning(f"Terrain analysis failed: {e}, continuing without terrain data")
                    terrain_data = None
            
            # IFS评估
            result = self.evaluator.find_most_threatening(
                enemies, 
                player_pos, 
                terrain_data
            )
            
            if not result:
                logger.warning("IFS evaluator returned no result")
                return None, None
            
            # 转换回Target对象
            enemy_id = result['enemy_id']
            for target in game_data.targets:
                if target.id == enemy_id:
                    logger.info(
                        f"IFS selected target ID={enemy_id}, "
                        f"Score={result['comprehensive_threat_score']:.3f}, "
                        f"Level={result['threat_level']}"
                    )
                    return target, result
            
            logger.error(f"IFS returned invalid enemy ID: {enemy_id}")
            return None, None
            
        except Exception as e:
            logger.error(f"IFS evaluation failed: {e}", exc_info=True)
            return None, None
    
    def evaluate_all_targets(
        self, 
        game_data: GameData
    ) -> List[Tuple[Target, Dict]]:
        """
        评估所有目标并返回排序列表
        
        Args:
            game_data: 游戏数据对象
            
        Returns:
            [(Target对象, 评估详情), ...] 按威胁度降序排列
        """
        if not game_data.targets:
            return []
        
        try:
            # 转换数据格式
            enemies = [self.convert_target_to_enemy(t) for t in game_data.targets]
            player_pos = (game_data.playerPosition.x, game_data.playerPosition.z)
            
            # 地形分析（如果可用）
            terrain_data = None
            if self.terrain_analyzer:
                try:
                    terrain_data = self.terrain_analyzer.batch_analyze_enemies(
                        enemies, 
                        player_pos
                    )
                except Exception as e:
                    logger.warning(f"Terrain analysis failed: {e}")
                    terrain_data = None
            
            # 评估所有目标
            ranked_results = self.evaluator.rank_targets(
                enemies, 
                player_pos, 
                terrain_data
            )
            
            # 转换为Target对象列表
            results = []
            target_map = {t.id: t for t in game_data.targets}
            
            for result in ranked_results:
                enemy_id = result['enemy_id']
                if enemy_id in target_map:
                    results.append((target_map[enemy_id], result))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to evaluate all targets: {e}", exc_info=True)
            return []


def log_ifs_details(target: Target, ifs_details: Dict):
    """
    输出IFS评估的详细信息
    
    Args:
        target: 目标对象
        ifs_details: IFS评估详情字典
    """
    logger.info("=" * 70)
    logger.info("🎯 IFS Threat Assessment Details")
    logger.info(f"Target ID: {target.id} ({target.type})")
    logger.info(
        f"Position: ({target.position.x:.2f}, {target.position.y:.2f}, "
        f"{target.position.z:.2f})"
    )
    logger.info(f"Distance: {ifs_details['distance']:.2f}m")
    logger.info(
        f"Comprehensive Threat Score: "
        f"{ifs_details['comprehensive_threat_score']:.3f}"
    )
    logger.info(f"Threat Level: {ifs_details['threat_level'].upper()}")
    
    # IFS值
    ifs_vals = ifs_details['ifs_values']
    logger.info(
        f"IFS Values: μ={ifs_vals['membership']:.3f}, "
        f"ν={ifs_vals['non_membership']:.3f}, "
        f"π={ifs_vals['hesitancy']:.3f}"
    )
    
    # 各指标得分
    logger.info("\nIndicator Scores:")
    for indicator, data in ifs_details['indicator_details'].items():
        logger.info(
            f"  {indicator:12s}: {data['threat_score']:6.3f} "
            f"({data['threat_level']})"
        )
    
    # 贡献度分析
    logger.info("\nContribution Analysis:")
    contributions = ifs_details['weighted_aggregation']['contributions']
    sorted_contribs = sorted(
        contributions.items(), 
        key=lambda x: x[1]['contribution'], 
        reverse=True
    )
    
    for indicator, contrib in sorted_contribs:
        logger.info(
            f"  {indicator:12s}: weight={contrib['weight']:.2f}, "
            f"contrib={contrib['contribution']:6.3f} "
            f"({contrib['percentage']:5.1f}%)"
        )
    
    logger.info("=" * 70)

