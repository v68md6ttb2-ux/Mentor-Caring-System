# Mentor Caring System (MCS)

BNBU 导师关怀系统（Mentor Caring System），基于 Flask + SQLAlchemy + SQLite，采用严格的三层 MVC 架构实现。

## 仓库内容

| 路径 | 说明 |
|------|------|
| `B07_Code/B07_code/` | 项目源代码、端到端测试与详细 README |
| `B07_PPT.pptx` / `B07_PPT.pdf` | 项目答辩演示文稿 |
| `B07_RecordedDemo/` | 功能演示录屏 |
| `B07_checklist.xlsx` | 项目检查表 |

## 快速开始

```bash
cd B07_Code/B07_code
pip install -r requirements.txt
python seed_data.py     # 创建并填充演示数据库
python teamwork.py      # 启动应用
```

打开 http://127.0.0.1:5000

演示账号（密码均为 `123456`）：

| 角色 | 用户名 |
|------|--------|
| Admin | `admin` |
| Faculty Consultant | `faculty` |
| Faculty Member | `faculty_member` |
| Mentor | `mentor1` / `mentor2` / `mentor3` |
| Coordinator | `coordinator` |
| Student | `2330000010` / `2330000020` / `2330000030` |

## 测试

```bash
python test_e2e.py
```

包含 84 个端到端测试，覆盖 7 种角色与 21 项功能需求。

## 邮件通知

SMTP 通过环境变量配置（`MAIL_SERVER`、`MAIL_PORT`、`MAIL_USERNAME`、`MAIL_PASSWORD`、`MAIL_DEFAULT_SENDER`）。未配置时邮件发送静默失败，不影响其他功能。

详细设计与实现说明见 [B07_Code/B07_code/README.md](B07_Code/B07_code/README.md)。
