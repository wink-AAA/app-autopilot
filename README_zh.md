# App Autopilot

**一个可配置的通用 App 自动运营框架 —— 从求职自动投递到社交平台运营。**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 什么是 App Autopilot？

App Autopilot 是一个**框架级工具包**，抽象了各类 App 重复性操作背后的通用模式。你只需为目标平台编写**适配器**和**规则**，框架会自动处理打分、调度、状态管理、隐私保护和通知。

### 来源

本框架抽象自两个真实生产场景：

1. **招聘平台自动投递** —— 浏览职位列表，根据个人偏好打分，自动投递高分职位，跟踪投递状态。
2. **社交平台自动运营** —— 定时发布内容，管理互动，对收到的消息进行分类，跨平台维护一致的人设。

> ⚠️ **重要提示：** App Autopilot 是一个**框架**，不包含任何具体平台的自动化实现代码。你需要自行编写目标平台的适配器。

---

## 核心特性

- 🎯 **多维度打分引擎** —— 可配置的加权打分系统，支持硬性条件和加分项
- 🔧 **平台适配器系统** —— 统一的抽象接口，支持接入任何 App 或网站
- 📋 **规则过滤引擎** —— 可组合的 AND/OR 规则集，支持匹配和排除
- 💬 **消息分类器** —— 基于关键词 + 正则的消息分类，支持自动回复
- 🔒 **隐私保护** —— 信息隔离、敏感数据脱敏、人设管理
- 📊 **状态管理** —— 轻量级 JSON 存储，支持去重和排除名单
- 📅 **灵活调度** —— 支持间隔、cron、手动三种触发模式
- 📬 **多通道通知** —— 邮件、Webhook 及可扩展的通知路由
- 🔄 **任务流水线** —— 多阶段编排器，支持重试和回退
- 📝 **YAML 配置** —— 分层配置，支持继承和验证

---

## 🤖 Coze 技能版

如果你使用 [扣子（Coze）](https://www.coze.cn) 平台，可以直接使用 [`coze-skill/`](./coze-skill/) 目录下的技能版本——无需写代码，用自然语言即可驱动所有自动化功能。

- **安装**：在扣子「我的技能」中搜索"App自动运营"，或手动上传 zip
- **使用**：直接说"帮我自动投简历"或"帮我代运营社交平台"
- **文档**：详见 [coze-skill/README.md](./coze-skill/README.md)

---

## 快速开始

### 安装

```bash
pip install -e ".[dev]"
```

### 基本用法

```python
from app_autopilot.core.config import load_config
from app_autopilot.core.scoring import ScoringEngine
from app_autopilot.core.state import StateStore

# 1. 加载配置
config = load_config("configs/examples/job_hunter.yaml", base_config_path="configs/base.yaml")

# 2. 初始化组件
engine = ScoringEngine(config.scoring)
store = StateStore(config.state.storage_path)

# 3. 对候选项打分
result = engine.score("job-12345", {
    "title": "Senior Python Engineer",
    "salary_min": 15000,
    "city": "Shanghai",
})

if result.passed:
    print(f"得分: {result.total_score} — 继续投递！")
else:
    print(f"得分: {result.total_score} — 跳过")
```

---

## 编写平台适配器

```python
from app_autopilot.adapters.base import PlatformAdapter, BrowseResult, InteractionResult, Message

class MyPlatformAdapter(PlatformAdapter):

    @property
    def platform_name(self) -> str:
        return "我的平台"

    async def setup(self, config):
        # 初始化会话/认证
        pass

    async def browse(self, **kwargs) -> BrowseResult:
        # 从平台获取数据
        return BrowseResult(items=[...])

    async def interact(self, action, item_id, **kwargs) -> InteractionResult:
        # 执行操作（投递、点赞、关注等）
        return InteractionResult(success=True, action=action, item_id=item_id)

    async def read_messages(self, **kwargs) -> list[Message]:
        return []

    async def send_message(self, recipient_id, text, **kwargs) -> bool:
        return True

    async def post_content(self, content, **kwargs) -> InteractionResult:
        return InteractionResult(success=True, action="post")

    async def teardown(self):
        pass
```

参见 `platforms/` 目录中的骨架示例。

---

## 项目结构

```
app-autopilot/
├── app_autopilot/          # 核心框架包
│   ├── core/               # 配置、打分、状态、调度、任务编排
│   ├── rules/              # 匹配、分类、隐私
│   ├── adapters/           # 平台适配器抽象基类和注册表
│   ├── notifications/      # 邮件、Webhook 通知渠道
│   └── utils/              # 日志和工具
├── configs/                # YAML 配置模板
├── platforms/              # 平台适配器骨架
├── docs/                   # 文档
├── tests/                  # 单元测试
└── pyproject.toml          # 项目元数据和依赖
```

---

## 开发

```bash
git clone https://github.com/your_org_here/app-autopilot.git
cd app-autopilot
pip install -e ".[dev]"
pytest
```

---

## 免责声明

本框架仅供**学习和提升效率**之用。使用者需自行负责：
- 遵守目标平台的服务条款
- 尊重频率限制和使用政策
- 确保自动化行为不违反任何法律法规

维护者不对本软件的任何滥用行为负责。

---

## 许可证

本项目基于 MIT 许可证开源 —— 详见 [LICENSE](LICENSE) 文件。
