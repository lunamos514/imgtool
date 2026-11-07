# imgtool - 图片信息查看与简单编辑

一个用 Python + OpenCV 写的命令行小工具，可以查看图片的基本信息，并对图片做缩放、裁剪、旋转、翻转、灰度化和格式转换。

## 项目介绍

- **做什么**：读取图片的文件名、格式、宽高、颜色模式、文件大小；并对图片做常见编辑。
- **支持的功能**：
  - 查看信息：文件名 / 格式 / 宽 / 高 / 颜色模式 / 文件大小（KB 或 MB，保留 2 位小数）
  - 缩放：指定宽高，或只给一边按比例缩放
  - 裁剪：按左、上、右、下坐标裁剪，越界会提示
  - 旋转：90 / 180 / 270 度（顺时针）
  - 翻转：水平、垂直
  - 灰度化：彩色转灰度
  - 格式转换：PNG / JPG 互转，透明通道自动处理
- **程序形式**：命令行（CLI），用 `argparse` 分子命令。
- **安全策略**：所有编辑结果都另存为新文件，**绝不覆盖原图**，并在终端打印保存位置。
- **出错处理**：文件不存在、不是有效图片、宽高非法、裁剪越界等情况都只打印中文提示，不抛 Traceback。

## 环境配置

### 前置要求

| 项目 | 版本 | 检查命令 |
|---|---|---|
| Python | 3.10 或更高 | `python3 --version` |
| uv（推荐） | 0.13 或更高 | `uv --version` |
| OpenCV | 由 `uv sync` 自动安装（当前锁定 5.0.0.93） | `uv run python -c "import cv2; print(cv2.__version__)"` |

Ubuntu 22.04 自带的 `python3` 就是 3.10，无需另装。

### 安装步骤

**第 1 步：安装 uv**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
```

（想让 PATH 永久生效：`echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc`）

**第 2 步：安装依赖**

仓库里已经有 `pyproject.toml` 和 `uv.lock`，直接同步即可，版本会被锁定成和开发时完全一致：

```bash
uv sync
```

这一步会自动创建 `.venv/` 虚拟环境，并安装 `opencv-python`（含 `numpy`）。

**如果网络较慢**，先切国内镜像再同步（国内镜像对境外 IP 可能握手失败，开了代理就用官方源）：

```bash
export UV_DEFAULT_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
uv sync
```

### 不使用 uv 的替代方案

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install opencv-python
```

之后把下文所有 `uv run main.py` 换成 `python main.py` 即可。

## 运行方式

所有命令都在项目根目录执行。用 `uv run` 可以免激活虚拟环境：

```bash
uv run main.py <子命令> [参数]
```

查看所有子命令：

```bash
uv run main.py --help
```

### 1. 查看图片信息

```bash
uv run main.py info demo.png
```

预期输出：

```
文件名    : demo.png
图片格式  : PNG
宽度      : 4096 px
高度      : 2304 px
颜色模式  : RGB
文件大小  : 1.95 MB
```

> 大小按 1024 进制换算，超过 1 MB 显示 MB，否则显示 KB，统一保留 2 位小数。

### 2. 缩放

```bash
uv run main.py resize demo.png -w 300
```

只给宽度时，高度按原始比例自动计算。预期输出：

```
尺寸：4096x2304 → 300x169
已保存：/home/moya0721/imgtool/demo_resized.png
```

宽高都指定：

```bash
uv run main.py resize demo.png -w 800 --height 600
```

### 3. 裁剪

参数 `-l -t -r -b` 分别是左、上、右、下坐标（左上角为原点）：

```bash
uv run main.py crop demo.png -l 50 -t 50 -r 250 -b 250
```

预期输出：

```
裁剪区域：(50,50) - (250,250)，结果尺寸 200x200
已保存：/home/moya0721/imgtool/demo_cropped.png
```

区域越界时给提示而不是崩溃：

```bash
uv run main.py crop demo.png -l 0 -t 0 -r 99999 -b 99999
```

```
错误：裁剪区域越界：图片尺寸 4096x2304，要求 0<=left<right<=4096 且 0<=top<bottom<=2304，当前 left=0 top=0 right=99999 bottom=99999
```

### 4. 旋转

只支持 90 / 180 / 270 度，顺时针方向：

```bash
uv run main.py rotate demo.png -d 90
```

预期输出：

```
已顺时针旋转 90 度
已保存：/home/moya0721/imgtool/demo_rot90.png
```

### 5. 翻转

`-m h` 水平翻转，`-m v` 垂直翻转：

```bash
uv run main.py flip demo.png -m h
uv run main.py flip demo.png -m v
```

预期输出：

```
已水平翻转
已保存：/home/moya0721/imgtool/demo_fliph.png
```

### 6. 灰度化

```bash
uv run main.py gray demo.png
```

预期输出：

```
已转换为灰度图
已保存：/home/moya0721/imgtool/demo_gray.png
```

### 7. 格式转换

```bash
uv run main.py convert demo.png -f jpg
uv run main.py convert demo.jpg -f png
```

预期输出：

```
已保存：/home/moya0721/imgtool/demo.jpg
```

带透明通道的 PNG 转 JPG 时会先转成 RGB，并额外提示：

```
检测到透明通道，已转换为 RGB 后保存（JPG 不支持透明）
已保存：/home/moya0721/imgtool/demo.jpg
```

### 出错时

```bash
uv run main.py info not_exist.jpg
```

```
错误：文件不存在：not_exist.jpg
```

```bash
uv run main.py resize demo.png -w 0
```

```
错误：宽高必须大于 0，当前为 0x2304
```

## 输出文件命名规则

不指定 `-o` 时，结果保存在原图同目录，文件名加后缀，原图保持不动：

| 功能 | 输出文件 |
|---|---|
| 缩放 | `demo_resized.png` |
| 裁剪 | `demo_cropped.png` |
| 旋转 | `demo_rot90.png` / `demo_rot180.png` / `demo_rot270.png` |
| 翻转 | `demo_fliph.png` / `demo_flipv.png` |
| 灰度 | `demo_gray.png` |
| 格式转换 | `demo.jpg` / `demo.png` |

想指定输出路径，任何子命令都可以加 `-o 文件名`。

## 项目结构

```
imgtool/
├── main.py          # 主程序，所有功能按子命令拆分
├── pyproject.toml   # 项目与依赖声明
├── uv.lock          # uv 锁定的依赖版本
├── .gitignore       # 排除虚拟环境、缓存和测试图片
└── README.md
```

## 开发说明

- 每个功能对应一个 `cmd_*` 函数，通过 `argparse` 的子命令分发，新增功能只需再加一个子命令。
- `load_image()` 统一负责读图和错误提示，`save_image()` 统一负责另存新文件并校验不覆盖原图。
- `main()` 里集中捕获 `FileNotFoundError` / `ValueError`，保证参数不合法时只打印友好提示。
- 开发过程在 `dev` 分支完成，功能验证通过后合并回 `main`。
