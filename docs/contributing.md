# 贡献指南

感谢你对 App Autopilot 的关注！我们欢迎各种形式的贡献。

---

## 行为准则

请保持友善和专业的交流氛围。我们致力于提供一个开放、包容的社区环境。

---

## 如何贡献

### 报告 Bug

1. 在 GitHub Issues 中创建新 Issue
2. 使用清晰的标题描述问题
3. 包含以下信息：
   - Python 版本
   - 操作系统
   - 复现步骤
   - 期望行为 vs 实际行为
   - 相关的错误日志

### 提出新功能

1. 先在 Issues 中讨论你的想法
2. 描述使用场景和期望的 API 设计
3. 如果有多个方案，列出各自的优缺点

### 提交代码

1. Fork 仓库
2. 创建功能分支：`git checkout -b feature/your-feature-name`
3. 编写代码（遵循下面的代码规范）
4. 编写/更新测试
5. 确保所有测试通过：`pytest`
6. 提交 PR 并描述你的改动

---

## 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/your_org_here/app-autopilot.git
cd app-autopilot

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black app_autopilot/ tests/

# 代码检查
ruff check app_autopilot/ tests/

# 类型检查
mypy app_autopilot/
```

---

## 代码规范

### Python 风格

- 使用 **Python 3.10+** 语法
- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 风格指南
- 使用 **Black** 格式化（行宽 100 字符）
- 使用 **Ruff** 进行 lint 检查
- 所有公共函数和类必须有 **类型注解**
- 使用 **Google 风格** 的 docstring

### Docstring 示例

```python
def my_function(param1: str, param2: int = 10) -> bool:
    """Brief one-line description.

    Longer description if needed, explaining the purpose
    and any important details.

    Args:
        param1: Description of param1.
        param2: Description of param2. Defaults to 10.

    Returns:
        Description of what the function returns.

    Raises:
        ValueError: When param1 is empty.
    """
```

### 测试规范

- 每个核心模块都需要对应的单元测试
- 测试文件命名：`test_<module_name>.py`
- 使用 `pytest` 框架
- 使用 `pytest.fixture` 管理测试依赖
- 测试命名：`test_<what_is_being_tested>`
- 异步测试使用 `pytest-asyncio`

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
feat: add new scoring rule type 'semantic'
fix: correct state file atomic write on Windows
docs: update architecture diagram
test: add unit tests for privacy guard
refactor: simplify config merge logic
```

---

## 贡献检查清单

提交 PR 前请确认：

- [ ] 代码通过所有测试 (`pytest`)
- [ ] 代码已格式化 (`black`)
- [ ] 无 lint 错误 (`ruff check`)
- [ ] 类型检查通过 (`mypy`)
- [ ] 新功能有对应的测试
- [ ] 文档已更新（如适用）
- [ ] 不包含敏感信息（密钥、个人信息等）
- [ ] 提交信息符合 Conventional Commits 格式

---

## 发布流程

（仅维护者）

1. 更新 `pyproject.toml` 中的版本号
2. 更新 CHANGELOG
3. 创建 Git tag：`git tag v0.x.x`
4. 推送到远程：`git push --tags`
5. 发布到 PyPI：`python -m build && twine upload dist/*`

---

## 联系

如有问题，请通过 GitHub Issues 联系。
