# Xuexitong Automation

[![tests](https://github.com/2498950046/xuexitong-concurrent-answer/actions/workflows/tests.yml/badge.svg)](https://github.com/2498950046/xuexitong-concurrent-answer/actions/workflows/tests.yml)

基于 Python + Selenium 的超星学习通/Chaoxing 课程与作业自动化辅助脚本。项目支持登录、课程作业页扫描、ChromeDriver 自动匹配、批量作业窗口并发处理，以及关键逻辑的单元测试。

> 请只在你有权限操作的账号和课程中使用。本项目不内置题库、账号、密码或 API Key；涉及作业提交的结果应由使用者自行核对，并遵守学校、课程和平台规则。

## 项目结构

```text
.
├── batch_homework.py              # 推荐入口：登录后扫描未提交作业，并发打开 worker 窗口处理
├── finish_work.py                 # 单个作业 URL 的答题入口
├── xuexitong.py                   # 课程/作业导航入口
├── scripts/
│   └── download_chromedriver.py   # 手动下载或刷新项目内 ChromeDriver
├── tests/                         # 单元测试
├── utils/
│   ├── ai.py                      # DeepSeek/OpenAI 兼容接口调用
│   ├── answers.py                 # 答案解析、数量校验、选项归一化
│   ├── browser_cookies.py         # 主控浏览器登录态捕获与 worker 注入
│   ├── chromedriver_manager.py    # Chrome/ChromeDriver 版本检测与下载
│   ├── click_answer.py            # Selenium 点击答案
│   ├── config.py                  # .env 和环境变量配置
│   ├── concurrent_runner.py       # 并发作业调度与 Ctrl+C 中断
│   ├── find_questions.py          # 页面题目读取
│   ├── homework_list.py           # 作业列表、iframe、分页扫描
│   └── homework_runner.py         # 单个作业的完整答题流程
├── .env.example                   # 配置模板，可以提交
├── .gitignore                     # 本地密钥、驱动、缓存、截图等忽略规则
└── requirements.txt
```

## 环境要求

- Python 3.10+
- Google Chrome
- Windows PowerShell、CMD、macOS 或 Linux Shell 均可运行，示例以 PowerShell 为主

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

## 配置

复制配置模板：

```powershell
Copy-Item .env.example .env
```

填写 `.env`。真实账号、密码、API Key 只放在本地 `.env` 或系统环境变量中，不要提交到公开仓库。

必填登录配置：

- `XUEXITONG_PHONE`
- `XUEXITONG_PASSWORD`

AI 配置：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`，默认 `https://api.deepseek.com`
- `DEEPSEEK_MODEL`，默认 `deepseek-v4-pro`

作业与浏览器配置：

- `XUEXITONG_WORK_URL`：单作业入口 `finish_work.py` 使用
- `XUEXITONG_BATCH_SIZE`：每批发给模型的题目数量，默认 `20`
- `XUEXITONG_WORKER_COUNT`：并发 worker 数，默认 `4`
- `XUEXITONG_CHROMEDRIVER`：可选；留空时自动下载匹配版本到 `.drivers/`
- `XUEXITONG_BROWSER_DETACH`：`1` 保持浏览器窗口，`0` 跟随 WebDriver 生命周期关闭

环境变量优先级高于 `.env`。

## 使用方式

推荐使用并发作业入口：

```powershell
python batch_homework.py
```

流程：

1. 主控浏览器自动登录。
2. 你手动进入课程的作业列表页。
3. 在终端输入 `y`。
4. 程序扫描所有分页中的未提交作业。
5. 程序按 `XUEXITONG_WORKER_COUNT` 并发打开 worker 浏览器窗口。
6. 每个 worker 完成自动选择后，你人工检查并提交，随后关闭该 worker 窗口。
7. 主控页刷新后可继续扫描下一轮。

中断程序：

```text
Ctrl+C
```

程序会通知 worker 停止，并尽量关闭已打开的浏览器窗口。

单个作业入口：

```powershell
python finish_work.py
```

启动后会优先在终端询问作业网址：输入网址后使用本次输入；直接回车则使用 `.env` 中的 `XUEXITONG_WORK_URL`。

课程导航入口：

```powershell
python xuexitong.py
```

手动刷新 ChromeDriver：

```powershell
python scripts/download_chromedriver.py
```

## 测试

运行全部测试：

```powershell
python -m pytest tests -q
```

编译检查：

```powershell
python -m compileall -q utils tests
```

## 公开仓库上传前检查

提交前建议执行：

```powershell
git status --short
git ls-files
python -m pytest tests -q
```

确认以下内容没有进入仓库：

- `.env`
- `.drivers/`
- `.venv/`
- `.idea/`、`.vscode/`
- `__pycache__/`、`*.pyc`
- `error.png`、截图、日志
- 真实手机号、密码、Cookie、API Key

如果某个敏感文件已经被 Git 跟踪，先从索引移除，例如：

```powershell
git rm --cached error.png
git rm --cached -r utils/__pycache__ .vscode docs/superpowers
```

如果真实 API Key 曾经提交到 Git 历史中，请立即到服务商后台作废并重新生成。`.gitignore` 只能防止未来误提交，不能清除已经存在的历史记录。

## 贡献与安全

- 贡献说明见 [CONTRIBUTING.md](CONTRIBUTING.md)
- 安全与隐私问题见 [SECURITY.md](SECURITY.md)
- 开源许可证需要仓库所有者确认后再添加 `LICENSE`
