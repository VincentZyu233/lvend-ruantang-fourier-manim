# 🎞️ lvend-ruantang-fourier-manim

> [▶️ 点击跳转原始素材视频](https://www.bilibili.com/video/BV1y7QwBgEHc) [![略nd-某种软糖](https://img.shields.io/badge/Bilibili-%E7%95%A5nd--%E6%9F%90%E7%A7%8D%E8%BD%AF%E7%B3%96-B7AEC9?logo=bilibili&logoColor=white&labelColor=00AEEC&style=flat-square)](https://www.bilibili.com/video/BV1y7QwBgEHc)

本仓库将一张动画中间帧、视频采样帧与 PSD 分层姿态转成几何轮廓，并用 Manim 重现频率圆链、线稿绘制、傅里叶平滑和姿态展示动画。

`output/` 按版本整理成品：00 是原生动态公式页脚版本，直接提交到 `output/captioned/`；`output/no_captioned/` 是 01-03 的本地无字幕原版，已被 Git 忽略；`output/captioned/` 同时保留 01-03 的固定底部说明栏版本。

## 🧰 环境

只需要 Python、[uv](https://docs.astral.sh/uv/) 和系统可执行的 `ffmpeg`。按系统安装 FFmpeg：

```powershell
# Windows (Scoop)
scoop install ffmpeg
```

```bash
# Debian / Ubuntu
sudo apt update && sudo apt install ffmpeg

# Fedora / Red Hat 系
sudo dnf install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

```bash
# macOS
brew install ffmpeg
```

安装后确认 `ffmpeg -version` 可运行。

```powershell
git clone https://github.com/VincentZyu233/lvend-ruantang-fourier-manim.git
cd lvend-ruantang-fourier-manim
uv venv --python 3.13
uv sync
uv run python -c "import manim, cv2, psd_tools; print(manim.__version__)"
```

视觉素材已在仓库中：`素材捏/略ndoc的软糖动画/midpoint.png` 用于 00/01，`某种软糖.mp4` 用于 02/03 的视频姿态，`1775818328351.psd` 用于 03 的 PSD 姿态。`素材捏/music/mimi十周年专辑.md` 保留曲目资料；体积较大的 FLAC 仅保留在本机，若要复现 Bili 合成版，需自行准备下文列出的三首文件。

## ▶️ 复现

以下命令会覆盖对应编号的成片。00 直接更新 `output/captioned/` 的动态页脚版本；01-03 更新 `output/no_captioned/` 中的单片、MP4/GIF 和 grid。Manim 的中间帧与提取数据写入被忽略的 `build/`，不会污染 Git。

```powershell
uv run python src/00/render.py --font "<LXGWWenKai-Medium.ttf 的绝对路径>"
uv run python src/01/render.py
uv run python src/02/render.py
uv run python src/03/render.py
```

渲染质量与已提交成品一致：00 为 1080x920、20 FPS，底部额外 100px 显示当前部分和；01 的单片为 720x720、grid 为 1080x1080，02/03 的 grid 为 1080x720。完整生成需要一些时间，尤其是 00 的动态频率公式与 02 的高采样傅里叶曲线。

字幕包装不重渲染 Manim scene，而是从上面的原始产物生成独立版本。安装 [霞鹜文楷](https://github.com/lxgw/LxgwWenKai) 后传入 Medium 字体文件路径：

```powershell
uv run python src/captioned/render.py --font "<LXGWWenKai-Medium.ttf 的绝对路径>"
```

00 现由 `00a–00e` 组成：保留 Ribbon Wand 成果页，并依次讲解闭合曲线与 `t`、复平面与旋转向量、等距采样与解旋、以及按 `|c[k]|` 重建。准备本机的《科学-サイエンス-mimi》《花束-ハナタバ-mimi》《悲伤的间隙-哀の隙間-mimi》后，下列命令会生成新的长版 `output/bili/bili-video-20260915.mp4`；三段 BGM 以 0.8 秒交叉淡化，结尾接入 01–03：

```powershell
uv run python src/00/render.py --font "<LXGWWenKai-Medium.ttf 的绝对路径>" --bili
```

完成 01-03 的静态字幕包装后，`src/captioned/render.py --bili` 仍可独立复现 20260913 正片。20260913 与冻结的 20260914 已归档在 [GitHub Release](https://github.com/VincentZyu233/lvend-ruantang-fourier-manim/releases/tag/bili-video-20260914)。

## ✨ 高规格成片

普通版保留为 1080x920、20 FPS。下列命令将 00-03 全部重新渲染为 2160x1840、60 FPS 的 Bili 成片，单片写入被忽略的 `output/high/`，最终文件写入被忽略的 `output/bili/bili-video-20260915-high.mp4`：

```powershell
uv run python src/render_high.py --font "<LXGWWenKai-Medium.ttf 的绝对路径>"
```

高规格版本的 MP4 通过 GitHub Release 发布，仓库内继续只保存 GIF 预览。

## 🗂️ 源码索引

所有脚本从项目根目录运行，使用 `uv run python src/0x/render.py`。

| 目录 | 输入 | 单片 | Grid | 核心方法 |
| --- | --- | --- | --- | --- |
| `src/00/` | `midpoint.png` | 频率圆链与 00a–00e 原理讲解 | 无 | DFT 排序、闭合曲线参数化、复平面、解旋平均、截断部分和 |
| `src/01/` | `midpoint.png` | 9 种线稿出现效果 | 3x3 | 阈值轮廓、K-means 色块、单条轮廓的 DFT 重建 |
| `src/02/` | `某种软糖.mp4` | 6 种姿态变换效果 | 3x2 | 五帧采样、轮廓重采样、FFT 平滑、Manim 变换 |
| `src/03/` | 视频和 `1775818328351.psd` | 6 种描线姿态展示 | 3x2 | 原生 `Create`、onion skin、PSD 图层组轮廓 |
| `src/captioned/` | `output/no_captioned/` 原始成片 | 21 段单片 | 3 个 grid | 霞鹜文楷底部说明栏、FFmpeg 成片拼接 |

00 的 `render.py` 直接输出动态页脚成品并制作 GIF；`fourier_principles.py` 将 00b–00e 拆成独立场景，方便单独调试。01-03 的每个 `render.py` 都将自己的 scene 输出到 `output/no_captioned/`，用 `ffmpeg` 同时制作 GIF 和 grid；`src/captioned/render.py` 再将它们包装为带字幕版本。若只想调试某一个 scene，可直接调用 Manim，例如：

```powershell
uv run manim src/02/video_transform.py VideoFourierSmoothTransform -pql
```

## 🖼️ Grid 对比

### 0️⃣ 傅里叶频率圆链重建

![00 Ribbon Wand 动态表达式版](output/captioned/00_16g_ribbon_wand.gif)

### 1️⃣ 静帧线稿出现效果

#### 🅰️ Write

![01a Write 字幕版](output/captioned/01_02a_write.gif)

![01 的九种线稿出现效果 字幕版](output/captioned/01_02_nine_grid.gif)

### 2️⃣ 视频傅里叶轮廓变换

#### 🅰️ Transform

![02a Transform 字幕版](output/captioned/02_06a_manimce_transform.gif)

![02 的六种傅里叶轮廓变换 字幕版](output/captioned/02_06abcdef_grid.gif)

### 3️⃣ 视频与 PSD 的原生 Create 展示

#### 🅰️ Video Single

![03a Video Single 字幕版](output/captioned/03_10a_video_single.gif)

![03 的六种视频与 PSD 描线展示 字幕版](output/captioned/03_10abcdef_onionskin_grid.gif)

更多已提交的字幕版 MP4/GIF 请查看仓库内的 [output/captioned/](output/captioned/) 文件夹；本机执行渲染后可在 `output/no_captioned/` 查看无字幕原版。
