"""威胁评估算法模块"""
import logging
import os
import json
from typing import Optional
from models import Target, GameData
from openai import OpenAI
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

logger = logging.getLogger(__name__)

# 初始化OpenAI客户端
client = None
try:
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.chatanywhere.tech/v1/")
    
    if api_key:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        logger.info(f"OpenAI client initialized successfully with base_url: {base_url}")
    else:
        logger.warning("OPENAI_API_KEY not found in environment variables, will use fallback algorithm")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    client = None


def calculate_threat_score(target: Target, player_pos) -> float:
    """
    计算单个目标的威胁度
    
    Args:
        target: 目标对象
        player_pos: 玩家位置（当前未使用，但保留接口）
    
    Returns:
        威胁度分数，分数越高威胁越大
    """
    # 距离因子（距离越近威胁越大）
    # 使用反比例关系，避免除零错误
    distance_factor = 1.0 / (target.distance + 1)
    
    # 角度因子（角度越小威胁越大，0度正前方）
    # 将角度转换为绝对值，正前方（0度）威胁最大
    angle_factor = 1.0 / (abs(target.angle) + 1)
    
    # 类型因子（Tank=2.0, Soldier=1.0）
    type_factor = 2.0 if target.type == "Tank" else 1.0
    
    # 综合威胁度
    threat_score = distance_factor * angle_factor * type_factor
    
    logger.debug(
        f"Target {target.id} ({target.type}): "
        f"distance={target.distance:.2f}, angle={target.angle:.2f}, "
        f"threat_score={threat_score:.4f}"
    )
    
    return threat_score


def find_most_threatening_target_with_gpt(game_data: GameData) -> Optional[Target]:
    """
    使用GPT-4o分析并找出最有威胁的目标
    
    Args:
        game_data: 游戏数据对象
    
    Returns:
        最有威胁的目标对象，如果分析失败则返回None
    """
    if not client:
        logger.warning("OpenAI client not available, falling back to algorithm-based method")
        return None
    
    try:
        # 构建发送给GPT的数据
        player_pos = game_data.playerPosition
        targets_info = []
        
        for target in game_data.targets:
            targets_info.append({
                "id": target.id,
                "type": target.type,
                "position": {
                    "x": target.position.x,
                    "y": target.position.y,
                    "z": target.position.z
                },
                "distance": round(target.distance, 2),
                "angle": round(target.angle, 2)
            })
        
        # 构建提示词
        prompt = f"""你是一个战术威胁评估AI。请分析以下战场情况，判断哪个敌人对玩家威胁最大。

玩家位置: X={player_pos.x:.2f}, Y={player_pos.y:.2f}, Z={player_pos.z:.2f}

敌人列表:
{json.dumps(targets_info, indent=2, ensure_ascii=False)}

考虑因素：
1. 距离：越近越危险
2. 角度：越接近正前方（0度）越危险
3. 类型：Tank（坦克）比Soldier（士兵）更危险

请回复最有威胁的敌人ID（只回复数字ID，不要其他内容）。"""

        logger.info("Sending data to GPT-4o for threat analysis...")
        logger.debug(f"Prompt: {prompt}")
        
        # 调用GPT-4o API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的战术威胁评估AI。你需要分析战场情况，快速准确地判断最危险的敌人。只回复敌人的ID数字，不要任何解释。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=10
        )
        
        # 解析GPT响应
        gpt_response = response.choices[0].message.content.strip()
        logger.info(f"GPT-4o response: {gpt_response}")
        
        # 提取目标ID
        try:
            target_id = int(gpt_response)
        except ValueError:
            # 尝试从响应中提取数字
            import re
            numbers = re.findall(r'\d+', gpt_response)
            if numbers:
                target_id = int(numbers[0])
            else:
                logger.error(f"Could not parse target ID from GPT response: {gpt_response}")
                return None
        
        # 找到对应的目标对象
        for target in game_data.targets:
            if target.id == target_id:
                logger.info(
                    f"[GPT-4o] Most threatening target: ID={target.id}, "
                    f"Type={target.type}, "
                    f"Distance={target.distance:.2f}, "
                    f"Angle={target.angle:.2f}"
                )
                return target
        
        logger.error(f"GPT returned invalid target ID: {target_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error calling GPT-4o API: {e}", exc_info=True)
        return None


def find_most_threatening_target(game_data: GameData) -> Optional[Target]:
    """
    找出最有威胁的目标（优先使用GPT-4o，失败则使用算法）
    
    Args:
        game_data: 游戏数据对象
    
    Returns:
        最有威胁的目标对象，如果没有目标则返回None
    """
    if not game_data.targets:
        logger.warning("No targets found in game data")
        return None
    
    # 首先尝试使用GPT-4o
    gpt_result = find_most_threatening_target_with_gpt(game_data)
    if gpt_result:
        return gpt_result
    
    # GPT失败时使用传统算法作为备用
    logger.info("Using fallback algorithm for threat assessment")
    max_threat_score = -1
    most_threatening = None
    
    for target in game_data.targets:
        threat_score = calculate_threat_score(target, game_data.playerPosition)
        if threat_score > max_threat_score:
            max_threat_score = threat_score
            most_threatening = target
    
    if most_threatening:
        logger.info(
            f"[Algorithm] Most threatening target: ID={most_threatening.id}, "
            f"Type={most_threatening.type}, "
            f"Distance={most_threatening.distance:.2f}, "
            f"Angle={most_threatening.angle:.2f}, "
            f"ThreatScore={max_threat_score:.4f}"
        )
    
    return most_threatening

