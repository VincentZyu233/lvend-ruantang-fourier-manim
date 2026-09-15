# 本机开发配置示例

此文件可提交，供其他开发机复制为根目录 `AGENTS.local.md`。实际文件已被 Git 忽略，不要写入账号、令牌或代理凭据。

```text
项目根目录: /path/to/lvend-ruantang-fourier-manim
Manim 虚拟环境: /path/to/lvend-ruantang-fourier-manim/.venv
JAnim 虚拟环境: /path/to/lvend-ruantang-fourier-manim/.venv-janim
字幕字体: /path/to/fonts/LXGWWenKai-Medium.ttf
FFmpeg: ffmpeg
素材目录: /path/to/lvend-ruantang-fourier-manim/素材捏
本机探索目录: /path/to/lvend-ruantang-fourier-manim/temp
```

运行包装脚本时，字体应显式传入，例如：

```powershell
uv run python temp/scripts/17/render_17_fourier_principles.py --font "/path/to/fonts/LXGWWenKai-Medium.ttf"
```
