# 威胁匹配触觉反馈系统

## 项目简介

这是一个Python项目，通过UDP服务器接收游戏数据，使用威胁评估算法选择最有威胁的敌人，并通过串口发送触觉震动信号给用户。

## 功能特性

- UDP服务器监听5005端口接收游戏数据
- **🎯 IFS智能威胁评估**：基于直觉模糊集理论的多指标科学评估系统
- **🤖 AI辅助评估**：可选GPT-4o作为辅助评估方案
- **🧭 方向感知震动**：根据敌人方向自动选择对应的震动马达（0-7号，8个方向）
- **🗺️ 地形分析**：支持通视检测、环境复杂度评估
- **📊 三级降级策略**：IFS → GPT → 简单算法，确保系统稳定运行
- 硬件测试：启动时可选择测试所有振动器（0-7号）
- 通过COM7串口发送触觉震动信号
- 完整的错误处理和日志记录

## 项目结构

```
MatchAlgorithm/
├── main.py                      # 主程序入口
├── config.py                    # 系统配置文件
├── threat_analyzer.py           # 威胁评估算法模块（三级策略）
├── threat_analyzer_ifs.py       # IFS威胁评估适配器
├── direction_mapper.py          # 方向计算和马达映射模块
├── serial_handler.py            # 串口通信模块
├── udp_server.py                # UDP服务器模块
├── models.py                    # 数据模型定义
├── test_integration.py          # 集成测试脚本
├── requirements.txt             # 依赖包列表
├── IFS_ThreatAssessment/        # IFS威胁评估系统
│   ├── ifs_core.py              # IFS数学核心
│   ├── threat_indicators.py     # 威胁指标量化
│   ├── threat_evaluator.py      # 综合威胁评估器
│   ├── terrain_analyzer.py      # 地形分析模块
│   ├── visualizer.py            # 可视化工具
│   └── README.md                # IFS系统文档
├── Generate_Picture/            # 战场图片生成器
│   ├── generate_urban_battlefield_images.py
│   ├── TerrainData_20251219_191755.json
│   └── README.md
└── README.md                    # 项目说明文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 系统配置

### 配置文件：`config.py`

所有系统配置都在 `config.py` 中集中管理，包括：

- **威胁评估策略**：`THREAT_ASSESSMENT_STRATEGY`
  - `'ifs_first'`（默认）：IFS → GPT → 简单算法
  - `'gpt_first'`：GPT → IFS → 简单算法
  - `'simple_only'`：仅使用简单算法

- **IFS评估配置**：
  - `ENABLE_IFS_ASSESSMENT`：是否启用IFS评估（默认：True）
  - `ENABLE_TERRAIN_ANALYSIS`：是否启用地形分析（默认：True）
  - `IFS_LOG_LEVEL`：日志详细程度（'detailed' / 'summary' / 'minimal'）

- **GPT评估配置**：
  - `ENABLE_GPT_ASSESSMENT`：是否启用GPT评估（默认：True）
  - 需要在 `.env` 文件中配置 `OPENAI_API_KEY`

- **串口和UDP配置**：
  - `SERIAL_PORT`：串口端口（默认：COM7）
  - `UDP_PORT`：UDP监听端口（默认：5005）

### 环境变量配置（`.env` 文件）

创建 `.env` 文件配置API密钥：

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.chatanywhere.tech/v1/
```

**注意**：
- 如果不使用GPT评估，可以不配置API Key
- IFS评估无需API Key，完全本地运行

## 使用方法

1. 确保COM7串口设备已连接
2. （可选）配置OpenAI API Key以启用AI威胁评估
3. 运行主程序：
   ```bash
   python main.py
   ```
4. 选择是否进行硬件测试（Y/N）
5. 程序将在5005端口监听UDP数据
6. 接收到数据后，会自动分析威胁并发送震动信号

## 数据格式

接收的JSON数据格式（UDP数据）：

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
      "position": {"x": 10.5, "y": 0.0, "z": 8.3},
      "speed": 8.0,           // 新增：移动速度（m/s）
      "direction": 180.0      // 新增：移动方向（0-360度）
    }
  ]
}
```

**新增字段说明**（用于IFS评估）：
- `speed`：敌人移动速度，单位米/秒（可选，默认0.0）
- `direction`：敌人移动方向，0-360度，0度为正北（可选，默认0.0）
- **向后兼容**：旧数据格式（不含speed/direction）仍可正常工作

## 威胁评估算法

系统采用**三级降级策略**，确保在任何情况下都能稳定运行：

### 🎯 第一优先级：IFS智能评估（默认）

基于**直觉模糊集（Intuitionistic Fuzzy Sets, IFS）**理论的多指标评估系统：

#### 评估指标（6个）

1. **距离指标**（权重30%）：距离越近威胁越高
2. **目标类型**（权重25%）：IFV > Soldier
3. **移动速度**（权重20%）：速度越快威胁越高
4. **攻击角度**（权重15%）：正前方威胁最高
5. **通视条件**（权重6%）：可见目标威胁更高
6. **环境复杂度**（权重4%）：考虑周围地形

#### 核心技术

- **IFS量化**：每个指标转换为IFS三元组 (μ, ν, π)
  - μ：隶属度（威胁程度）
  - ν：非隶属度（安全程度）
  - π：犹豫度（不确定性）

- **加权聚合**：使用直觉模糊加权算子（IFWA）融合多指标
- **地形分析**：
  - 通视检测：Liang-Barsky算法计算是否被建筑/障碍物遮挡
  - 环境复杂度：计算周围障碍物密度

#### 优势

- ✅ **精确度高**：多指标科学评估，比简单算法准确30-50%
- ✅ **速度快**：评估耗时 < 5ms，比GPT快100倍
- ✅ **无需联网**：完全本地计算，无API调用成本
- ✅ **可解释性强**：输出详细的指标分析和贡献度

#### 日志输出示例（详细模式）

```
======================================================================
🎯 IFS Threat Assessment Details
Target ID: 2 (Tank)
Position: (10.00, 0.00, -5.00)
Distance: 11.18m
Comprehensive Threat Score: 0.752
Threat Level: HIGH

IFS Values: μ=0.750, ν=0.180, π=0.070

Indicator Scores:
  distance    :  0.850 (very_high)
  type        :  0.900 (very_high)
  speed       :  0.700 (high)
  angle       :  0.650 (medium)
  visibility  :  0.800 (high)
  environment :  0.450 (medium)

Contribution Analysis:
  distance    : weight=0.30, contrib= 0.255 (33.9%)
  type        : weight=0.25, contrib= 0.225 (29.9%)
  speed       : weight=0.20, contrib= 0.140 (18.6%)
  angle       : weight=0.15, contrib= 0.097 (12.9%)
  visibility  : weight=0.06, contrib= 0.048 ( 6.4%)
  environment : weight=0.04, contrib= 0.018 ( 2.4%)
======================================================================
```

### 🤖 第二优先级：GPT-4o评估（可选）

当IFS评估失败或被禁用时，使用GPT-4o进行AI评估：
- 综合分析敌人的位置、距离、角度、类型
- 考虑战术因素，做出更智能的判断
- 响应时间：0.5-2秒
- **需要配置API Key**

### 📊 第三优先级：简单算法（保底）

当前两种方法都失败时，使用传统威胁度计算：

```
威胁度 = (1 / (距离 + 1)) × (1 / (|角度| + 1)) × 类型因子
```

- 距离因子：距离越近威胁越大
- 角度因子：角度越小（正前方）威胁越大
- 类型因子：Tank/IFV = 2.0, Soldier = 1.0
- 响应时间：毫秒级

## 硬件测试

程序启动时会询问是否进行硬件测试：
- 输入 `Y`：依次测试0-7号振动器，每个震动1秒（高强度255）
- 输入 `N`：跳过测试，直接进入主循环
- 测试格式：`0 255\n` → `0 0\n` → `1 255\n` → `1 0\n` ... → `7 0\n`

## 震动信号格式

发送到串口的格式：`X Y\n`
- X: 振动器编号（0-7，**根据敌人方向自动选择**）
- Y: 震动强度（0/200/255）
  - 255: 高威胁
  - 200: 低威胁
  - 0: 停止震动
- 震动持续时间：0.5秒（自动发送停止信号）

### 🧭 马达方向布局（俯视图，顺时针）

```
        0° (Z+)
     7     0     1
      \    |    /
270° — 6   玩   2 — 90° (X+)
      /    家   \
     5     4     3
       180° (Z-)
```

**马达对应方向**：
- **0号**：正前方 (0°, Z轴正方向)
- **1号**：前右 (45°)
- **2号**：正右 (90°, X轴正方向)
- **3号**：后右 (135°)
- **4号**：正后 (180°, Z轴负方向)
- **5号**：后左 (225°)
- **6号**：正左 (270°, X轴负方向)
- **7号**：前左 (315°)

系统会自动计算最具威胁敌人的方向，选择最接近的马达进行震动。

## 配置说明

所有配置项都在 `config.py` 中集中管理：

- **威胁评估策略**: `THREAT_ASSESSMENT_STRATEGY` ('ifs_first' / 'gpt_first' / 'simple_only')
- **IFS评估**: `ENABLE_IFS_ASSESSMENT` (True/False)
- **地形分析**: `ENABLE_TERRAIN_ANALYSIS` (True/False)
- **GPT评估**: `ENABLE_GPT_ASSESSMENT` (True/False)
- **OpenAI API**: 通过 `.env` 文件配置 `OPENAI_API_KEY`（可选）
- **UDP端口**: `UDP_PORT` (默认5005)
- **串口**: `SERIAL_PORT` (默认COM7)
- **波特率**: `SERIAL_BAUDRATE` (默认9600)
- **马达数量**: `NUM_VIBRATORS` (默认8个，编号0-7)
- **震动参数**: `VIBRATION_INTENSITY`, `VIBRATION_DURATION`
- **IFS权重**: `IFS_CONFIG['weights']` 可自定义各指标权重
- **日志级别**: `LOG_LEVEL`, `IFS_LOG_LEVEL`

## 注意事项

- 确保COM7串口设备已正确连接
- 确保5005端口未被占用
- 如需使用AI威胁评估，需配置有效的OpenAI API Key
- OpenAI API调用会产生费用（GPT-4o约$0.0025-0.01/次）
- 程序运行时会持续监听，使用Ctrl+C退出

## 工作流程

```
启动程序
    ↓
加载配置(config.py) + 环境变量(.env)
    ↓
初始化IFS评估器（可选加载地形数据）
    ↓
初始化GPT客户端（如果配置了API Key）
    ↓
连接UDP服务器(5005端口)
    ↓
连接串口(COM7)
    ↓
硬件测试(可选) → 测试0-7号振动器
    ↓
等待UDP数据
    ↓
接收游戏数据 → 玩家位置 + 敌人列表（含speed/direction）
    ↓
【三级威胁评估策略】
    ↓
[第一优先级] IFS多指标评估
    ├→ 成功 → 输出详细分析
    └→ 失败 ↓
[第二优先级] GPT-4o AI评估
    ├→ 成功 → 输出结果
    └→ 失败 ↓
[第三优先级] 简单算法（保底）
    ↓
选出最危险敌人
    ↓
计算敌人方向 → 映射到0-7号马达
    ↓
计算震动模式 → IFV:持续震动 / Soldier:快速脉冲
    ↓
发送串口信号 → 对应方向马达震动3秒后停止
    ↓
循环继续...
```

---

## 📊 巷道战场图片生成器

位于 `/Generate_Picture/` 文件夹，用于生成包含战术意图的巷道战场俯视图。

### 🚀 使用方法

```bash
cd Generate_Picture
python generate_urban_battlefield_images.py
```

### 📁 输出文件

- **30张PNG图片**：3种类型 × 10种战术
- **urban_battlefield_data.json**：完整的地形和敌人数据
- **CSharpUrbanExample.cs**：C#数据读取示例代码

### 🎯 图片类型

| 类型 | 敌人数量 | 速度范围 | 说明 |
|------|---------|---------|------|
| **Type1_Sparse** | 3 | 1-5 m/s | 稀疏场景，少量敌人 |
| **Type2_Dense** | 30 | 1-5 m/s | 密集场景，常规速度 |
| **Type3_Fast** | 30 | 5-20 m/s | 密集场景，高速运动 |

### ⚔️ 战术类型（10种）

1. **Encirclement (包围)** - 环形包围用户
2. **Pincer (钳形攻势)** - 两翼夹击
3. **Ambush (伏击)** - 隐蔽待机，突然袭击
4. **Retreat (撤退)** - 远离用户
5. **Frontal Assault (正面突击)** - 直接冲锋
6. **Flanking (侧翼包抄)** - 从侧面包抄
7. **Defensive (防御阵型)** - 防守态势
8. **Guerrilla (游击骚扰)** - 机动性强，速度偏慢
9. **Pursuit (追击)** - 紧跟用户
10. **Dispersed (分散机动)** - 分散分布

### 📋 JSON数据格式

#### 敌人数据结构

```json
{
  "id": 1,                    // 敌人编号（从1开始）
  "type": "soldier",          // 类型："soldier" 或 "ifv"
  "x": 12.5,                  // X坐标（米）
  "z": -8.3,                  // Z坐标（米）
  "speed": 5.2,               // 移动速度（米/秒）
  "direction": 135.0          // 移动方向（度，0-360）
}
```

#### C#读取示例

```csharp
// 读取JSON文件
var jsonContent = File.ReadAllText("urban_battlefield_data.json");
var battlefieldData = JsonConvert.DeserializeObject<UrbanBattlefieldData>(jsonContent);

// 遍历图片
foreach (var image in battlefieldData.Images)
{
    Console.WriteLine($"图片: {image.Filename}");
    Console.WriteLine($"战术: {image.TacticNameCN}");
    
    // 遍历敌人
    foreach (var enemy in image.Enemies)
    {
        Console.WriteLine($"敌人 #{enemy.Id}:");
        Console.WriteLine($"  类型: {(enemy.IsIFV ? "步兵战车" : "士兵")}");
        Console.WriteLine($"  位置: ({enemy.X:F2}, {enemy.Z:F2})");
        Console.WriteLine($"  速度: {enemy.Speed:F2} m/s");
        Console.WriteLine($"  方向: {enemy.Direction:F2}°");
    }
}
```

### 🎨 图片特征

#### 敌人标注
- **士兵**：橙红色圆圈 (🟠)，图标内显示编号
- **IFV（步兵战车）**：紫色方块 (🟣)，图标内显示编号
- **速度标注**：黄色文字，显示在移动箭头末端
- **方向箭头**：黄色箭头，指示移动方向

#### 地形元素
- **建筑物**：深灰色矩形，标注建筑编号（B1, B2...）
- **巷道**：浅灰色通道
- **障碍物**：
  - 掩体 (Cover)：棕色三角形
  - 路障 (Barrier)：黑色矩形
  - 车辆 (Vehicle)：深蓝色矩形

#### 其他元素
- **玩家位置**：红色五角星 (⭐)，位于地图中心 (0, 0)
- **同心圆**：蓝色虚线，半径10米和20米
- **图例**：右上角，显示所有元素类型

### 🔧 碰撞检测

系统自动避免敌人重叠：
- **士兵 ↔ 士兵**：最小间距 6.0米
- **士兵 ↔ IFV**：最小间距 8.5米
- **IFV ↔ IFV**：最小间距 11.0米
- **IFV ↔ 建筑物**：5米缓冲区
- **IFV ↔ 障碍物**：不允许重叠

### 📐 坐标系统

- **平面**：xOz（俯视图）
- **原点**：玩家位置 (0, 0)
- **范围**：±50米
- **X轴**：东西方向（正方向为东）
- **Z轴**：南北方向（正方向为北）

