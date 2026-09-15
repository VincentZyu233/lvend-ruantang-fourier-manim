# 项目协作约定

## 运行环境

- 从项目根目录运行命令，Python 依赖通过 `uv` 与 `pyproject.toml` 管理。
- 常规验证使用 `uv run python ...`；Manim、OpenCV 与 PSD 工具均由锁定的 Python 环境提供。
- 本机字体、JAnim 虚拟环境、代理和绝对路径只读取 `AGENTS.local.md`，不得提交其中内容。
- 可选数学字体名称：STIX Two Math。

## 目录边界

- `src/` 是可复现的正式源码；根目录 `output/` 是受版本控制的展示产物。
- `素材捏/` 是项目输入素材，除非任务明确要求，不移动或重写其中文件。
- `temp/` 是本机探索区，不提交到 Git。探索源码按编号放在 `temp/scripts/NN/`。
- 探索成片只能写入 `temp/output/NN/`，其中 `NN` 与探索脚本编号一致。
- Manim/JAnim 原生渲染、smoke 文件和重复中间 MP4 只能写入 `temp/media/NN/`。
- 几何 JSON、PSD 分层、颜色层、检查图只能写入 `temp/artifacts/NN/`；命令输出只写入 `temp/logs/`。
- 不得在 `temp/`、`temp/output/`、`temp/media/` 或 `temp/artifacts/` 根层新增未分类文件。
- `temp/scripts/shared/` 仅放至少被两个编号实验复用的模块；非渲染工具只能放入 `temp/scripts/tools/`。
- `temp/scripts/` 根层不放 Python 源码或 `__pycache__`；新编号先创建 `scripts/NN`、`output/NN`、`media/NN`、`artifacts/NN` 与 `logs/NN`。

## 新探索与验证

- 新探索脚本命名为 `temp/scripts/NN/NN_主题.py`；需要包装渲染时使用同目录的 `render.py` 或 `render_NN_主题.py`。
- 写入新产物前创建对应的 `output/NN`、`media/NN`、`artifacts/NN` 或 `logs/NN` 子目录。
- 路径调整后至少运行 `python -m py_compile`；视频产物使用 `ffprobe` 检查可读性、尺寸和时长。
- 保留历史探索媒体。清理或删除 `temp/` 内容需要用户明确要求并确认精确目标。
