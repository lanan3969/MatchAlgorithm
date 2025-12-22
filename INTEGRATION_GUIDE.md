# IFS威胁评估系统集成指南

## 目录

1. [系统架构](#系统架构)
2. [快速开始](#快速开始)
3. [游戏端数据接口](#游戏端数据接口)
4. [配置详解](#配置详解)
5. [地形数据集成](#地形数据集成)
6. [IFS权重调整](#ifs权重调整)
7. [性能优化](#性能优化)
8. [故障排查](#故障排查)
9. [API参考](#api参考)

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        游戏引擎 (Unity/UE)                     │
│                                                               │
│  ┌─────────────┐     ┌─────────────┐     ┌──────────────┐  │
│  │  玩家位置    │     │  敌人列表    │     │   地形数据    │  │
│  │  (x, y, z)  │     │ (含speed等) │     │ (建筑/障碍)   │  │
│  └──────┬──────┘     └──────┬──────┘     └──────┬───────┘  │
│         │                    │                    │          │
│         └────────────────────┴────────────────────┘          │
│                              │                                │
│                         UDP (JSON)                            │
└──────────────────────────────┼────────────────────────────────┘
                               │ Port 5005
┌──────────────────────────────┼────────────────────────────────┐
│                    Python威胁评估系统                           │
│                              │                                │
│         ┌───────────────────┴────────────────────┐           │
│         │        UDP Server (udp_server.py)       │           │
│         └───────────────────┬────────────────────┘           │
│                              │                                │
│                    ┌────────▼─────────┐                      │
│                    │  GameData对象     │                      │
│                    │  (models.py)     │                      │
│                    └────────┬─────────┘                      │
│                              │                                │
│         ┌───────────────────┴────────────────────┐           │
│         │  威胁评估 (threat_analyzer.py)          │           │
│         │                                         │           │
│         │  ┌────────────────────────────────┐   │           │
│         │  │  【第一优先级】IFS评估器        │   │           │
│         │  │  - 6指标IFS量化                │   │           │
│         │  │  - 地形分析（可选）             │   │           │
│         │  │  - 加权聚合                    │   │           │
│         │  │  - 响应时间: <5ms              │   │           │
│         │  └────────────┬───────────────────┘   │           │
│         │               │ 失败？                  │           │
│         │  ┌────────────▼───────────────────┐   │           │
│         │  │  【第二优先级】GPT-4o评估       │   │           │
│         │  │  - AI智能分析                  │   │           │
│         │  │  - 响应时间: 0.5-2s            │   │           │
│         │  └────────────┬───────────────────┘   │           │
│         │               │ 失败？                  │           │
│         │  ┌────────────▼───────────────────┐   │           │
│         │  │  【第三优先级】简单算法（保底） │   │           │
│         │  │  - 距离×角度×类型               │   │           │
│         │  │  - 响应时间: <1ms              │   │           │
│         │  └────────────┬───────────────────┘   │           │
│         └───────────────┼────────────────────────┘           │
│                         │                                    │
│                    最高威胁目标                              │
│                         │                                    │
│         ┌───────────────┴────────────────────┐              │
│         │  方向映射 (direction_mapper.py)     │              │
│         │  计算0-7号马达                      │              │
│         └───────────────┬────────────────────┘              │
│                         │                                    │
│         ┌───────────────┴────────────────────┐              │
│         │  串口输出 (serial_handler.py)       │              │
│         │  COM7 @ 9600 bps                   │              │
│         └───────────────┬────────────────────┘              │
└──────────────────────────┼────────────────────────────────────┘
                          │
                     ┌────▼────┐
                     │ 触觉马达 │
                     │ 阵列(8个)│
                     └─────────┘
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置系统

创建 `.env` 文件（可选，用于GPT评估）：

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.chatanywhere.tech/v1/
```

### 3. 配置评估策略

编辑 `config.py`：

```python
# 威胁评估策略
THREAT_ASSESSMENT_STRATEGY = 'ifs_first'  # IFS优先（推荐）

# 启用/禁用各评估方法
ENABLE_IFS_ASSESSMENT = True      # IFS评估（推荐启用）
ENABLE_GPT_ASSESSMENT = True      # GPT评估（可选）
ENABLE_TERRAIN_ANALYSIS = True    # 地形分析（推荐启用）

# IFS日志详细程度
IFS_LOG_LEVEL = 'detailed'  # 'detailed' / 'summary' / 'minimal'
```

### 4. 运行系统

```bash
python main.py
```

### 5. 运行集成测试

```bash
python test_integration.py
```

---

## 游戏端数据接口

### UDP数据格式（JSON）

游戏端需要通过UDP发送JSON数据到 `127.0.0.1:5005`（或配置的地址）。

#### 完整数据格式（推荐）

```json
{
  "round": 1,
  "playerPosition": {
    "x": 0.0,
    "y": 0.0,
    "z": 0.0
  },
  "targets": [
    {
      "id": 1,
      "angle": 45.23,
      "distance": 12.50,
      "type": "Tank",
      "position": {
        "x": 10.5,
        "y": 0.0,
        "z": 8.3
      },
      "speed": 8.0,           // 【新增】移动速度（m/s）
      "direction": 180.0,     // 【新增】移动方向（0-360度）
      "velocity": {           // 【可选】速度矢量
        "x": 0.0,
        "y": 0.0,
        "z": -8.0
      }
    }
  ]
}
```

#### 最小数据格式（向后兼容）

```json
{
  "round": 1,
  "playerPosition": {"x": 0.0, "y": 0.0, "z": 0.0},
  "targets": [
    {
      "id": 1,
      "angle": 45.23,
      "distance": 12.50,
      "type": "Soldier",
      "position": {"x": 10.5, "y": 0.0, "z": 8.3}
      // speed和direction将使用默认值0.0
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `round` | int | ✅ | 回合编号 |
| `playerPosition` | object | ✅ | 玩家3D坐标 |
| `targets` | array | ✅ | 敌人列表 |
| `targets[].id` | int | ✅ | 敌人唯一ID |
| `targets[].angle` | float | ✅ | 相对玩家的角度（度） |
| `targets[].distance` | float | ✅ | 距离玩家的距离（米） |
| `targets[].type` | string | ✅ | 类型："Tank"、"Soldier"、"IFV" |
| `targets[].position` | object | ✅ | 敌人3D坐标 |
| `targets[].speed` | float | ⭕ | 移动速度（m/s），默认0.0 |
| `targets[].direction` | float | ⭕ | 移动方向（0-360度），默认0.0 |
| `targets[].velocity` | object | ❌ | 速度矢量（可选） |

### Unity C# 发送示例

```csharp
using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using Newtonsoft.Json;

public class ThreatSystemSender : MonoBehaviour
{
    private UdpClient udpClient;
    private IPEndPoint endPoint;
    
    void Start()
    {
        udpClient = new UdpClient();
        endPoint = new IPEndPoint(IPAddress.Parse("127.0.0.1"), 5005);
    }
    
    public void SendGameData(Vector3 playerPos, List<Enemy> enemies)
    {
        var data = new
        {
            round = Time.frameCount,
            playerPosition = new { x = playerPos.x, y = playerPos.y, z = playerPos.z },
            targets = enemies.Select(e => new
            {
                id = e.id,
                angle = CalculateAngle(playerPos, e.position),
                distance = Vector3.Distance(playerPos, e.position),
                type = e.type,  // "Tank", "Soldier", "IFV"
                position = new { x = e.position.x, y = e.position.y, z = e.position.z },
                speed = e.velocity.magnitude,  // 【推荐】速度大小
                direction = CalculateDirection(e.velocity)  // 【推荐】移动方向
            }).ToList()
        };
        
        string json = JsonConvert.SerializeObject(data);
        byte[] bytes = Encoding.UTF8.GetBytes(json);
        udpClient.Send(bytes, bytes.Length, endPoint);
    }
    
    float CalculateDirection(Vector3 velocity)
    {
        // 计算速度方向（0-360度，0度为正北）
        float angle = Mathf.Atan2(velocity.x, velocity.z) * Mathf.Rad2Deg;
        if (angle < 0) angle += 360f;
        return angle;
    }
}
```

---

## 配置详解

### 威胁评估策略配置

在 `config.py` 中设置评估优先级：

```python
# 策略选项：
# 'ifs_first'   - IFS → GPT → 简单算法（推荐，最准确）
# 'gpt_first'   - GPT → IFS → 简单算法（需要API Key）
# 'simple_only' - 仅使用简单算法（最快，但精度低）
THREAT_ASSESSMENT_STRATEGY = 'ifs_first'
```

### IFS评估器配置

```python
# 是否启用IFS评估
ENABLE_IFS_ASSESSMENT = True

# IFS指标权重配置（总和必须为1.0）
IFS_CONFIG = {
    'weights': {
        'distance': 0.30,      # 距离指标
        'type': 0.25,          # 目标类型
        'speed': 0.20,         # 移动速度
        'angle': 0.15,         # 攻击角度
        'visibility': 0.06,    # 通视条件
        'environment': 0.04    # 环境复杂度
    }
}

# IFS日志详细程度
# 'detailed' - 输出各指标得分、IFS值、贡献度分析（适合调试）
# 'summary'  - 只输出最终威胁得分和等级（适合生产环境）
# 'minimal'  - 只输出选中的目标ID（最简洁）
IFS_LOG_LEVEL = 'detailed'
```

### 地形分析配置

```python
# 是否启用地形分析（通视检测、环境复杂度）
ENABLE_TERRAIN_ANALYSIS = True

# 地形数据JSON文件路径
TERRAIN_DATA_PATH = "Generate_Picture/TerrainData_20251219_191755.json"
```

**注意**：
- 如果没有地形数据文件，系统会自动禁用地形分析
- 通视指标和环境指标的权重会被分配到其他指标

---

## 地形数据集成

### 地形数据格式

IFS系统支持从JSON文件加载地形数据，用于通视检测和环境复杂度计算。

#### JSON格式示例

```json
{
  "generatedTime": "2024-12-19 19:17:55",
  "terrain": {
    "size": {"x": 100, "z": 100},
    "center": {"x": 0, "y": 0, "z": 0}
  },
  "buildings": [
    {
      "id": 1,
      "position": {"x": 15.0, "y": 0.0, "z": 20.0},
      "size": {"x": 10.0, "z": 8.0},
      "height": 12.0
    }
  ],
  "obstacles": [
    {
      "id": 1,
      "type": "Cover",
      "position": {"x": 5.0, "y": 0.0, "z": 10.0},
      "size": {"x": 2.0, "y": 1.5, "z": 2.0}
    }
  ],
  "alleys": [
    {
      "id": 1,
      "startPosition": {"x": 0.0, "y": 0.0, "z": -50.0},
      "endPosition": {"x": 0.0, "y": 0.0, "z": 50.0},
      "width": 8.0
    }
  ]
}
```

### 在Unity中导出地形数据

```csharp
public class TerrainExporter : MonoBehaviour
{
    public void ExportTerrainData(string filePath)
    {
        var terrain = new
        {
            generatedTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
            terrain = new
            {
                size = new { x = 100f, z = 100f },
                center = new { x = 0f, y = 0f, z = 0f }
            },
            buildings = GameObject.FindGameObjectsWithTag("Building")
                .Select(b => new
                {
                    id = b.GetInstanceID(),
                    position = new { x = b.transform.position.x, y = b.transform.position.y, z = b.transform.position.z },
                    size = new { x = b.transform.localScale.x, z = b.transform.localScale.z },
                    height = b.transform.localScale.y
                }).ToList(),
            obstacles = GameObject.FindGameObjectsWithTag("Obstacle")
                .Select(o => new
                {
                    id = o.GetInstanceID(),
                    type = o.GetComponent<ObstacleType>().typeName,  // "Cover", "Barrier", "Vehicle"
                    position = new { x = o.transform.position.x, y = o.transform.position.y, z = o.transform.position.z },
                    size = new { x = o.transform.localScale.x, y = o.transform.localScale.y, z = o.transform.localScale.z }
                }).ToList()
        };
        
        string json = JsonConvert.SerializeObject(terrain, Formatting.Indented);
        File.WriteAllText(filePath, json);
        Debug.Log($"Terrain data exported to {filePath}");
    }
}
```

---

## IFS权重调整

根据不同场景需求，可以调整IFS指标权重。

### 预设方案

#### 1. 默认方案（全面均衡）

```python
IFS_CONFIG = {
    'weights': {
        'distance': 0.30,
        'type': 0.25,
        'speed': 0.20,
        'angle': 0.15,
        'visibility': 0.06,
        'environment': 0.04
    }
}
```

适用场景：通用战场，平衡考虑所有因素

#### 2. 距离优先方案

```python
IFS_CONFIG = {
    'weights': {
        'distance': 0.50,      # ↑ 提高距离权重
        'type': 0.20,
        'speed': 0.15,
        'angle': 0.10,
        'visibility': 0.03,
        'environment': 0.02
    }
}
```

适用场景：近战场景，最近的敌人威胁最大

#### 3. 速度敏感方案

```python
IFS_CONFIG = {
    'weights': {
        'distance': 0.25,
        'type': 0.20,
        'speed': 0.35,         # ↑ 提高速度权重
        'angle': 0.15,
        'visibility': 0.03,
        'environment': 0.02
    }
}
```

适用场景：高速战场（如车辆战），快速移动的敌人更危险

#### 4. 地形重视方案

```python
IFS_CONFIG = {
    'weights': {
        'distance': 0.25,
        'type': 0.20,
        'speed': 0.15,
        'angle': 0.10,
        'visibility': 0.15,    # ↑ 提高通视权重
        'environment': 0.15    # ↑ 提高环境权重
    }
}
```

适用场景：巷战、室内战，地形因素非常重要

### 权重调整原则

1. **总和必须为1.0**：所有权重之和必须等于1.0
2. **关键指标优先**：将更多权重分配给对当前场景最重要的指标
3. **测试验证**：调整后使用 `test_integration.py` 或实战数据验证效果
4. **渐进调整**：每次只调整10-20%，避免大幅改动

---

## 性能优化

### IFS评估性能

- **典型评估时间**：1-5ms（单目标）
- **多目标评估**：30目标约 30-150ms
- **瓶颈**：地形分析（通视检测）

### 优化建议

#### 1. 禁用地形分析（如果不需要）

```python
ENABLE_TERRAIN_ANALYSIS = False
```

性能提升：约50-70%

#### 2. 降低日志详细程度

```python
IFS_LOG_LEVEL = 'minimal'  # 或 'summary'
```

性能提升：约10-20%

#### 3. 简化地形数据

- 减少建筑物和障碍物数量
- 合并小障碍物为大障碍物
- 只保留关键地形要素

#### 4. 使用简单算法（极端情况）

```python
THREAT_ASSESSMENT_STRATEGY = 'simple_only'
ENABLE_IFS_ASSESSMENT = False
ENABLE_GPT_ASSESSMENT = False
```

评估时间：<1ms，但精度大幅下降

---

## 故障排查

### 问题1：IFS评估失败，降级为GPT/简单算法

**日志示例**：
```
WARNING - IFS evaluation failed: <error>, falling back to GPT
```

**可能原因**：
1. IFS模块导入失败
2. 地形数据格式错误
3. 目标数据缺失必需字段

**排查步骤**：
```bash
# 1. 检查IFS模块是否完整
python -c "from IFS_ThreatAssessment.threat_evaluator import IFSThreatEvaluator"

# 2. 运行集成测试
python test_integration.py

# 3. 检查配置
python -c "import config; print(config.ENABLE_IFS_ASSESSMENT)"
```

**解决方案**：
- 确保 `IFS_ThreatAssessment/` 文件夹完整
- 检查地形数据JSON格式
- 查看详细错误日志

### 问题2：地形分析不生效

**症状**：通视指标和环境指标始终为默认值

**排查**：
```python
# 检查地形分析器是否加载
import os
from config import TERRAIN_DATA_PATH, ENABLE_TERRAIN_ANALYSIS

print(f"Terrain analysis enabled: {ENABLE_TERRAIN_ANALYSIS}")
print(f"Terrain data path: {TERRAIN_DATA_PATH}")
print(f"File exists: {os.path.exists(TERRAIN_DATA_PATH)}")
```

**解决方案**：
- 确认 `ENABLE_TERRAIN_ANALYSIS = True`
- 检查 `TERRAIN_DATA_PATH` 路径正确
- 验证JSON文件格式符合规范

### 问题3：权重不生效

**症状**：修改 `IFS_CONFIG` 权重后评估结果未变化

**原因**：代码已经加载旧配置

**解决方案**：
```bash
# 重启Python进程
# 或者在代码中动态更新权重
from threat_analyzer_ifs import ifs_adapter
ifs_adapter.evaluator.weights = new_weights
```

### 问题4：性能下降

**排查**：
```bash
# 启用详细日志查看各步骤耗时
# 在config.py中设置
LOG_LEVEL = "DEBUG"
```

**常见原因**：
- 地形数据过于复杂（100+建筑物）
- 同时评估大量目标（50+）
- 详细日志输出过多

**解决方案**：参考[性能优化](#性能优化)章节

---

## API参考

### IFSThreatAnalyzerAdapter

主要的IFS评估适配器类。

#### 初始化

```python
from threat_analyzer_ifs import IFSThreatAnalyzerAdapter

# 不加载地形数据
adapter = IFSThreatAnalyzerAdapter()

# 加载地形数据
adapter = IFSThreatAnalyzerAdapter(terrain_data_path="path/to/terrain.json")
```

#### find_most_threatening()

找出最高威胁目标。

```python
target, details = adapter.find_most_threatening(game_data)

# 返回值
target: Target对象或None
details: dict，包含：
    - enemy_id: int
    - distance: float
    - comprehensive_threat_score: float
    - threat_level: str ('very_low' / 'low' / 'medium' / 'high' / 'very_high')
    - ifs_values: dict {membership, non_membership, hesitancy}
    - indicator_details: dict {indicator_name: {threat_score, threat_level}}
    - weighted_aggregation: dict {contributions: ...}
```

#### evaluate_all_targets()

评估所有目标并返回排序列表。

```python
ranked_results = adapter.evaluate_all_targets(game_data)

# 返回值：[(Target对象, details字典), ...]，按威胁度降序
for target, details in ranked_results:
    print(f"Target {target.id}: {details['comprehensive_threat_score']:.3f}")
```

### log_ifs_details()

输出详细的IFS评估日志。

```python
from threat_analyzer_ifs import log_ifs_details

log_ifs_details(target, ifs_details)
```

---

## 总结

IFS威胁评估系统提供了科学、准确、快速的威胁评估能力。通过合理配置和优化，可以在各种战场场景下实现最佳性能。

如有问题，请查阅：
- `IFS_ThreatAssessment/README.md` - IFS系统详细文档
- `test_integration.py` - 集成测试示例
- 主README.md - 项目整体说明

---

**版本**: v2.0  
**最后更新**: 2024-12-23

