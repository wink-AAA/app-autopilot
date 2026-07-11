# 自定义指南

本文档介绍如何根据你的具体需求自定义 App Autopilot 框架。

---

## 1. 自定义打分规则

### 添加新的评分维度

在 YAML 配置中添加维度即可：

```yaml
scoring:
  dimensions:
    - name: work_life_balance
      weight: 0.8
      is_hard_requirement: false
      rules:
        - type: contains
          field: description
          value: "flexible hours"
          score: 10
        - type: contains
          field: description
          value: "remote"
          score: 15
```

### 自定义评分规则类型

如果内置的 5 种规则类型不够用，可以注册自定义评估器：

```python
from app_autopilot.core.scoring import ScoringEngine

engine = ScoringEngine(config.scoring)

def eval_semantic_similarity(rule, data):
    """自定义语义相似度评分规则。"""
    field = rule.get("field", "")
    target = rule.get("target", "")
    score = float(rule.get("score", 0))
    
    # 你的语义匹配逻辑
    similarity = compute_similarity(data.get(field, ""), target)
    if similarity > 0.8:
        return score
    elif similarity > 0.5:
        return score * 0.5
    return 0.0

engine.register_evaluator("semantic", eval_semantic_similarity)
```

然后在配置中使用：

```yaml
rules:
  - type: semantic
    field: job_description
    target: "machine learning and data science"
    score: 20
```

---

## 2. 自定义匹配规则

### 使用自定义谓词

```python
from app_autopilot.rules.matcher import RuleSet, Matcher

ruleset = RuleSet()

# 添加自定义判断函数
def is_weekday_posting(data):
    """只在周末发布的职位才感兴趣（可能是紧急需求）。"""
    import datetime
    post_date = data.get("posted_date")
    if post_date:
        dt = datetime.datetime.fromisoformat(post_date)
        return dt.weekday() >= 5  # Saturday or Sunday
    return False

ruleset.add_predicate(is_weekday_posting, label="weekend_posting")
```

### 组合多个规则集

```python
from app_autopilot.rules.matcher import MatchLogic, Matcher

matcher = Matcher()

# 必须满足的条件
must_have = RuleSet(logic=MatchLogic.AND)
must_have.add_rule(Rule(field="salary_min", operator=MatchOperator.GTE, value=10000))
must_have.add_rule(Rule(field="city", operator=MatchOperator.IN, value=["Shanghai", "Beijing"]))
matcher.add_filter("requirements", must_have, mode="include")

# 排除条件
exclude = RuleSet(logic=MatchLogic.OR)
exclude.add_rule(Rule(field="title", operator=MatchOperator.CONTAINS, value="intern"))
exclude.add_rule(Rule(field="company", operator=MatchOperator.IN, value=["BlockedCorp"]))
matcher.add_filter("exclusions", exclude, mode="exclude")
```

---

## 3. 自定义消息分类

### 添加分类规则

```python
from app_autopilot.rules.classifier import MessageClassifier, ClassificationRule, Action

classifier = MessageClassifier()

classifier.add_rule(ClassificationRule(
    category="salary_negotiation",
    keywords=["salary", "compensation", "pay", "package"],
    patterns=[r"\d+[kK]"],
    action=Action.FLAG,
    priority=20,
))
```

### 使用自定义分类器

```python
from app_autopilot.rules.classifier import ClassificationResult

def my_ai_classifier(text: str):
    """集成外部 AI 服务进行消息分类。"""
    # 调用你的 AI 分类服务
    result = call_ai_service(text)
    if result.confidence > 0.9:
        return ClassificationResult(
            category=result.category,
            action=Action.NOTIFY,
            confidence=result.confidence,
        )
    return None

classifier.add_custom_classifier(my_ai_classifier)
```

---

## 4. 自定义隐私规则

### 配置信息隔离

```yaml
privacy:
  persona_name: TechExplorer
  sensitive_fields:
    - real_name
    - phone
    - email
    - home_address
  blocked_keywords:
    - confidential
    - internal_only
  isolation_rules:
    - field_name: phone
      contexts: ["job_application", "social_post"]
      replacement: "via email only"
    - field_name: workplace
      contexts: ["social_post"]
      replacement: "a tech company"
```

### 在代码中使用

```python
from app_autopilot.rules.privacy import PrivacyGuard, Persona, IsolationRule

guard = PrivacyGuard()

# 注册人设
guard.add_persona(Persona(
    name="TechExplorer",
    title="Software Engineer",
    bio="Passionate about building great software.",
), context="social_platform")

# 注册敏感信息
guard.add_sensitive_field("real_name", "Your Name Here")
guard.add_sensitive_field("phone", "13800000000")

# 发送消息前脱敏
safe_text = guard.sanitize(raw_text, context="job_application")

# 检查是否有违规
violations = guard.check(raw_text, context="social_post")
if violations:
    print(f"Privacy violations found: {violations}")
```

---

## 5. 自定义通知渠道

### 实现新通知渠道

```python
from app_autopilot.notifications.base import NotificationChannel, NotificationPayload

class SlackChannel(NotificationChannel):
    """Slack 通知渠道。"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    @property
    def channel_name(self) -> str:
        return "slack"

    async def send(self, payload: NotificationPayload) -> bool:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(self.webhook_url, json={
                "text": f"*{payload.title}*\n{payload.body}"
            }) as resp:
                return resp.status == 200
```

### 配置通知路由

```python
from app_autopilot.notifications.base import NotificationRouter

router = NotificationRouter()
router.add_channel("email", email_channel)
router.add_channel("slack", slack_channel)
router.add_channel("webhook", webhook_channel)

# 不同类型的事件路由到不同渠道
router.add_route("high_score_match", "email")
router.add_route("high_score_match", "slack")  # 同时发送到两个渠道
router.add_route("application_sent", "webhook")
router.set_default_channel("email")  # 默认渠道
```

---

## 6. 自定义任务流水线

```python
from app_autopilot.core.task_runner import TaskRunner

def browse_jobs(context, previous_output):
    """阶段1：浏览职位。"""
    jobs = context["adapter"].browse(limit=50)
    context["jobs"] = jobs
    return jobs

def score_jobs(context, previous_output):
    """阶段2：打分。"""
    engine = context["scoring_engine"]
    scored = []
    for job in previous_output.items:
        result = engine.score(job["id"], job)
        if result.passed:
            scored.append((job, result))
    return scored

def apply_jobs(context, previous_output):
    """阶段3：投递。"""
    for job, score in previous_output:
        context["adapter"].interact("apply", job["id"])
    return len(previous_output)

def notify_result(context, previous_output):
    """阶段4：通知。"""
    count = previous_output
    context["notifier"].send(f"Applied to {count} jobs")

runner = TaskRunner()
runner.add_stage("browse", browse_jobs, retries=2)
runner.add_stage("score", score_jobs)
runner.add_stage("apply", apply_jobs, fallback=lambda ctx, err: print(f"Apply failed: {err}"))
runner.add_stage("notify", notify_result)

result = runner.run(initial_context={"adapter": adapter, "scoring_engine": engine})
```

---

## 7. 配置文件继承

配置文件支持层级继承，子配置只需写差异部分：

```yaml
# configs/base.yaml
app_name: app-autopilot
log_level: INFO
scoring:
  min_score_threshold: 0.0
state:
  storage_path: data/state.json

# configs/my_scenario.yaml（只写差异）
app_name: my-scenario
scoring:
  min_score_threshold: 50.0  # 覆盖基础配置
  dimensions:
    - name: custom_dim
      weight: 1.0
      rules: [...]
```

加载时自动合并：

```python
config = load_config(
    "configs/my_scenario.yaml",
    base_config_path="configs/base.yaml",
)
```
