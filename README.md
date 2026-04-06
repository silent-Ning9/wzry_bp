# 🎮 王者荣耀 BP 系统

一个基于 KPL（王者荣耀职业联赛）全局 BP 赛制的英雄选择辅助系统。

## ✨ 功能特性

- **多种赛制支持** - 支持 BO1/BO3/BO5/BO7/BO9 多种赛制
- **全局 BP 支持** - 符合 KPL 官方赛制，本队已用英雄不可再选
- **巅峰对决** - BO7 第 7 局、BO9 第 9 局自动触发巅峰对决（盲选模式）
- **败者选边** - 每局结束后败方可选择下一局阵营
- **智能推荐** - 基于阵容分析推荐最优英雄选择
- **阵容分析** - 实时分析双方阵容优劣势
- **多位置英雄** - 支持英雄多分路展示
- **图片 CDN 加速** - 优先使用腾讯 CDN 加载英雄头像

## 🗺️ 分路说明

| 分路 | 说明 |
|------|------|
| 对抗路 | 坦克/战士，承担前排和切后任务 |
| 打野 | 刺客/战士，负责野区资源和节奏 |
| 中路 | 法师，提供输出和控制 |
| 发育路 | 射手，团队核心输出 |
| 游走 | 辅助，保护队友和开团 |

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Flask

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行项目

```bash
python app.py
```

访问 http://localhost:5000 即可使用。

## 📁 项目结构

```
wzry_bp/
├── app.py              # Flask 主应用
├── crawler/            # 数据爬虫
│   ├── hero_spider.py  # 英雄数据爬虫
│   └── kpl_spider.py   # KPL 分路数据爬虫
├── data/               # 数据文件
│   ├── heroes.json     # 英雄数据
│   └── counters.json   # 克制关系数据
├── services/           # 业务逻辑
│   ├── bp_engine.py    # BP 流程引擎
│   ├── recommend.py    # 推荐服务
│   └── analysis.py     # 阵容分析
├── static/             # 静态资源
│   ├── css/
│   ├── js/
│   └── img/            # 英雄头像
├── templates/          # HTML 模板
│   └── index.html
└── requirements.txt    # 依赖列表
```

## 🎯 BP 流程

### 常规 BP

采用 KPL 全局 BP 赛制：

1. **Ban 阶段 1** - 双方各禁 2 个英雄
2. **Pick 阶段 1** - 蓝1→红1,2→蓝2,3→红3
3. **Ban 阶段 2** - 双方各禁 3 个英雄
4. **Pick 阶段 2** - 红4→蓝4,5→红5
5. **全局禁用** - 本队已选英雄后续不可再选

### 巅峰对决（BO7 第 7 局 / BO9 第 9 局）

巅峰对决为盲选模式，规则如下：

- **无禁用阶段** - 直接进入 Pick
- **任选英雄** - 可选择任意英雄，包括：
  - 本队之前比赛已用英雄
  - 对方已选英雄
  - 双方可选相同英雄
- **盲选机制** - 双方选择互不可见，BP 结束后同时揭晓

## 📡 API 接口

### 英雄数据

```
GET /api/heroes          # 获取所有英雄
GET /api/heroes/:id      # 获取单个英雄
GET /api/counters        # 获取克制关系
```

### BP 流程

```
POST /api/bp/start                    # 开始 BP 会话 (body: {series_type: "BO1"|"BO3"|"BO5"|"BO7"|"BO9"})
POST /api/bp/:session_id/action       # 执行 Ban/Pick
POST /api/bp/:session_id/undo         # 撤销操作
POST /api/bp/:session_id/set-teams    # 设置队名
POST /api/bp/:session_id/set-winner   # 设置胜者
POST /api/bp/:session_id/select-side  # 败者选边
POST /api/bp/:session_id/new-game     # 开始新一局
GET  /api/bp/:session_id/recommend    # 获取推荐
GET  /api/bp/:session_id/state        # 获取状态
```

### 阵容分析

```
POST /api/analyze       # 分析双方阵容
POST /api/analyze/team  # 分析单队阵容
```

## 🔧 技术栈

- **后端**: Flask, Python
- **前端**: HTML5, CSS3, JavaScript
- **数据**: JSON 文件存储

## 📝 更新日志

### v1.1.0
- 新增 BO1/BO3/BO5/BO7/BO9 多种赛制支持
- 实现巅峰对决（盲选模式）功能
  - BO7 第 7 局、BO9 第 9 局自动触发
  - 无禁用阶段，双方任选英雄
  - 支持双方选择相同英雄
- 优化赛制选择界面布局

### v1.0.0
- 实现完整 BP 流程
- 支持全局 BP 赛制
- 添加败者选边功能
- 支持 KPL 2026 春季赛英雄分路数据
- 优化图片 CDN 加载

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
