# tranlsate — AutoTranslate

好用的做题 / 翻译软件。Windows 桌面自动翻译工具，支持接入多种大模型 API（默认 DeepSeek）。

## 规划路线

- [x] **阶段 0**：核心骨架（配置系统、翻译引擎、Provider 适配器、CLI 验证）
- [x] **阶段 1**：核心 GUI（主窗口双语互译、设置页、系统托盘）
- [x] **阶段 2**：屏幕框选截图 + OCR 翻译（离线 RapidOCR，全局热键 Ctrl+Alt+Z）
- [ ] 阶段 3：文档批量翻译（TXT/SRT/DOCX/PDF）
- [ ] 阶段 4：题目识别 + 大模型作答 + 自动填充
- [ ] 阶段 5：输入框实时翻译
- [ ] 阶段 6：浏览器插件 + 本地服务

## 环境

- Python 3.12（虚拟环境 `.venv`）

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env` 并填入 API key，或在 GUI 设置页填写（保存至
`%APPDATA%\AutoTranslate\config.json`）。环境变量优先级高于配置文件。

| 变量 | 说明 | 默认 |
|------|------|------|
| `AUTOTRANSLATE_API_KEY` | 大模型 API key | 空 |
| `AUTOTRANSLATE_BASE_URL` | API 基址 | `https://api.deepseek.com` |
| `AUTOTRANSLATE_MODEL` | 模型名 | `deepseek-chat` |
| `AUTOTRANSLATE_PROVIDER` | Provider 类型 | `openai` |
| `AUTOTRANSLATE_SOURCE_LANG` | 默认源语言 | `auto` |
| `AUTOTRANSLATE_TARGET_LANG` | 默认目标语言 | `zh` |

## 使用（CLI 验证）

```powershell
python -m app.cli --text "Hello, world" --to zh
python -m app.cli --to en --from zh          # 从 stdin 读取
python -m app.cli --show-config
```

## 使用（GUI）

```powershell
python -m app.main
```

首次运行请在菜单 `File → Settings`（Ctrl+,）填入 API key。窗口关闭后最小化到
系统托盘，双击托盘图标可显示/隐藏。

## 屏幕翻译（阶段 2）

- 点击主窗口「屏幕翻译」按钮、托盘菜单，或按全局热键 **Ctrl+Alt+Z**
- 拖动鼠标框选屏幕区域 → 自动 OCR 识别 → 翻译 → 弹窗显示译文（可复制）
- OCR 使用 RapidOCR（离线 ONNX，支持中英文），首次识别会加载模型
- 全局热键依赖 `keyboard`，如未生效请以管理员权限运行

## 项目结构

```
app/
├─ cli.py                # 命令行入口
├─ main.py               # GUI 入口 + 系统托盘
├─ core/
│  ├─ config.py          # 配置读写
│  ├─ engine.py          # 翻译调度器
│  └─ providers/
│     ├─ base.py         # Provider 抽象基类
│     ├─ openai_api.py   # OpenAI 兼容适配器（DeepSeek 默认）
│     └─ registry.py     # Provider 注册表
└─ ui/
   ├─ main_window.py     # 主窗口：双语互译
   ├─ settings_dialog.py # 设置页
   ├─ tray.py            # 系统托盘
   └─ worker.py          # 后台翻译线程
```
