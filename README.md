# 威胁匹配触觉反馈系统

## 项目简介

这是一个Python项目，通过UDP服务器接收游戏数据，使用威胁评估算法选择最有威胁的敌人，并通过串口发送触觉震动信号给用户。

## 功能特性

- UDP服务器监听5005端口接收游戏数据
- **🤖 AI智能威胁评估**：使用GPT-4o分析战场情况，智能判断最危险的敌人
- 备用算法：当API不可用时自动切换到传统算法
- 硬件测试：启动时可选择测试所有振动器（0-7号）
- 通过COM7串口发送触觉震动信号
- 完整的错误处理和日志记录

## 项目结构

```
MatchAlgorithm/
├── main.py              # 主程序入口
├── threat_analyzer.py   # 威胁评估算法模块
├── serial_handler.py    # 串口通信模块
├── udp_server.py        # UDP服务器模块
├── models.py            # 数据模型定义
├── requirements.txt     # 依赖包列表
└── README.md           # 项目说明文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置OpenAI API Key（可选）

为了使用GPT-4o智能威胁评估功能，需要配置OpenAI API Key：

### Windows:
```bash
set OPENAI_API_KEY=your-api-key-here
set OPENAI_BASE_URL=https://api.chatanywhere.tech/v1/
```

### Linux/Mac:
```bash
export OPENAI_API_KEY=your-api-key-here
export OPENAI_BASE_URL=https://api.chatanywhere.tech/v1/
```

### 永久配置（推荐）:
在系统环境变量中添加：
- `OPENAI_API_KEY`: 你的API密钥
- `OPENAI_BASE_URL`: API基础URL（默认: `https://api.chatanywhere.tech/v1/`）

**注意**: 
- 如果未配置API Key，系统会自动使用传统算法作为备用方案
- Base URL默认使用 `https://api.chatanywhere.tech/v1/`，也可以使用官方API `https://api.openai.com/v1`

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

接收的JSON数据格式：

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
      "position": {"x": 10.5, "y": 0.0, "z": 8.3}
    }
  ]
}
```

## 威胁评估算法

### 🤖 AI模式（GPT-4o）

当配置了OpenAI API Key时，系统会使用GPT-4o进行智能威胁评估：
- 综合分析敌人的位置、距离、角度、类型
- 考虑战术因素，做出更智能的判断
- 响应时间：通常0.5-2秒

### 📊 传统算法模式（备用）

当API不可用时，使用传统威胁度计算公式：

```
威胁度 = (1 / (距离 + 1)) × (1 / (|角度| + 1)) × 类型因子
```

- 距离因子：距离越近威胁越大
- 角度因子：角度越小（正前方）威胁越大
- 类型因子：Tank = 2.0, Soldier = 1.0
- 响应时间：毫秒级

## 硬件测试

程序启动时会询问是否进行硬件测试：
- 输入 `Y`：依次测试0-7号振动器，每个震动1秒（高强度255）
- 输入 `N`：跳过测试，直接进入主循环
- 测试格式：`0 255\n` → `0 0\n` → `1 255\n` → `1 0\n` ... → `7 0\n`

## 震动信号格式

发送到串口的格式：`X Y\n`
- X: 振动器编号（0-7）
- Y: 震动强度（0/200/255）
  - 255: 高威胁
  - 200: 低威胁
  - 0: 停止震动

## 配置说明

- **OpenAI API**: 通过环境变量 `OPENAI_API_KEY` 配置（可选）
- **UDP端口**: 5005（可在`udp_server.py`中修改）
- **串口**: COM7（可在`main.py`中修改）
- **波特率**: 9600（可在`main.py`中修改）
- **振动器数量**: 8个，编号0-7
- **振动器编号**: 默认使用0号（可在`main.py`中修改）

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
连接UDP服务器(5005端口)
    ↓
连接串口(COM7)
    ↓
硬件测试(可选) → 测试0-7号振动器
    ↓
等待UDP数据
    ↓
接收游戏数据 → 玩家位置 + 敌人列表
    ↓
威胁分析 → [GPT-4o AI分析] 或 [传统算法]
    ↓
选出最危险敌人
    ↓
计算震动强度 → 255(高威胁) 或 200(低威胁)
    ↓
发送串口信号 → 振动0.5秒后停止
    ↓
循环继续...
```

