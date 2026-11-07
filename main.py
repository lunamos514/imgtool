"""图片信息查看与简单编辑工具（命令行版）。

作业要求：读取图片基础信息 + 缩放/裁剪/旋转/翻转/灰度/格式转换，
不覆盖原图，出错时给明确提示而不是崩溃。
"""

import argparse
import os
import sys

import cv2


# ---------- 基础工具 ----------

def load_image(path):
    """读取图片。文件不存在或不是有效图片时抛出带中文说明的异常。"""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"文件不存在：{path}")
    # IMREAD_UNCHANGED 保留透明通道，否则 PNG 的 alpha 会被丢掉
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"不是有效的图片文件：{path}")
    return image


def human_size(num_bytes):
    """把字节数转成 KB / MB，保留 2 位小数。"""
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / 1024 / 1024:.2f} MB"
    return f"{num_bytes / 1024:.2f} KB"


def save_image(image, src_path, suffix, out_path=None):
    """另存为新文件，绝不覆盖原图；返回保存路径。"""
    if out_path is None:
        stem, ext = os.path.splitext(src_path)
        out_path = f"{stem}_{suffix}{ext}"
    if os.path.abspath(out_path) == os.path.abspath(src_path):
        raise ValueError("输出路径不能和原图相同，避免覆盖原图")
    if not cv2.imwrite(out_path, image):
        raise ValueError(f"保存失败，请检查目录是否存在：{out_path}")
    print(f"已保存：{os.path.abspath(out_path)}")
    return out_path


# ---------- 3.1 读取图片信息 ----------

def cmd_info(args):
    image = load_image(args.path)
    height, width = image.shape[:2]

    if image.ndim == 2:
        color_mode = "灰度 (Gray)"
    elif image.shape[2] == 4:
        color_mode = "RGBA（带透明通道）"
    else:
        color_mode = "RGB"

    fmt = os.path.splitext(args.path)[1].lstrip(".").upper() or "未知"

    print(f"文件名    : {os.path.basename(args.path)}")
    print(f"图片格式  : {fmt}")
    print(f"宽度      : {width} px")
    print(f"高度      : {height} px")
    print(f"颜色模式  : {color_mode}")
    print(f"文件大小  : {human_size(os.path.getsize(args.path))}")


# ---------- 3.2 简单编辑 ----------

def cmd_resize(args):
    """缩放：宽高都给按指定尺寸，只给一个则按比例缩放。"""
    image = load_image(args.path)
    height, width = image.shape[:2]

    if args.width is None and args.height is None:
        raise ValueError("至少指定 --width 或 --height 其中一个")

    if args.width and args.height:
        new_w, new_h = args.width, args.height
    elif args.width:
        new_w = args.width
        new_h = max(1, round(height * args.width / width))
    else:
        new_h = args.height
        new_w = max(1, round(width * args.height / height))

    if new_w <= 0 or new_h <= 0:
        raise ValueError(f"宽高必须大于 0，当前为 {new_w}x{new_h}")

    # 缩小时用 INTER_AREA 更清晰，放大时用 INTER_CUBIC
    interp = cv2.INTER_AREA if new_w < width else cv2.INTER_CUBIC
    result = cv2.resize(image, (new_w, new_h), interpolation=interp)
    print(f"尺寸：{width}x{height} → {new_w}x{new_h}")
    save_image(result, args.path, "resized", args.out)


def cmd_crop(args):
    """裁剪：按左、上、右、下坐标切割，越界时报错。"""
    image = load_image(args.path)
    height, width = image.shape[:2]
    left, top, right, bottom = args.left, args.top, args.right, args.bottom

    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError(
            f"裁剪区域越界：图片尺寸 {width}x{height}，"
            f"要求 0<=left<right<={width} 且 0<=top<bottom<={height}，"
            f"当前 left={left} top={top} right={right} bottom={bottom}"
        )

    result = image[top:bottom, left:right]
    print(f"裁剪区域：({left},{top}) - ({right},{bottom})，"
          f"结果尺寸 {right - left}x{bottom - top}")
    save_image(result, args.path, "cropped", args.out)


def cmd_rotate(args):
    """旋转：只支持 90 / 180 / 270 度（顺时针）。"""
    if args.degree not in (90, 180, 270):
        raise ValueError("旋转角度只支持 90、180、270")
    image = load_image(args.path)
    codes = {
        90: cv2.ROTATE_90_CLOCKWISE,
        180: cv2.ROTATE_180,
        270: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }
    result = cv2.rotate(image, codes[args.degree])
    print(f"已顺时针旋转 {args.degree} 度")
    save_image(result, args.path, f"rot{args.degree}", args.out)


def cmd_flip(args):
    """翻转：h 水平（左右镜像），v 垂直（上下镜像）。"""
    image = load_image(args.path)
    code = 1 if args.mode == "h" else 0
    result = cv2.flip(image, code)
    print(f"已{'水平' if args.mode == 'h' else '垂直'}翻转")
    save_image(result, args.path, f"flip{args.mode}", args.out)


def cmd_gray(args):
    """灰度化：彩色图转单通道灰度图。"""
    image = load_image(args.path)
    if image.ndim == 2:
        raise ValueError("这张图已经是灰度图，无需转换")
    code = cv2.COLOR_BGRA2GRAY if image.shape[2] == 4 else cv2.COLOR_BGR2GRAY
    result = cv2.cvtColor(image, code)
    print("已转换为灰度图")
    save_image(result, args.path, "gray", args.out)


def cmd_convert(args):
    """格式转换：PNG 与 JPG 互转；带透明通道转 JPG 时先转 RGB。"""
    target = args.format.lower().lstrip(".")
    if target not in ("png", "jpg", "jpeg"):
        raise ValueError("目标格式只支持 png、jpg、jpeg")

    image = load_image(args.path)
    has_alpha = image.ndim == 3 and image.shape[2] == 4

    if target in ("jpg", "jpeg") and has_alpha:
        # JPEG 不支持透明通道，必须先把 BGRA 转成 BGR
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        print("检测到透明通道，已转换为 RGB 后保存（JPG 不支持透明）")

    if args.out:
        out_path = args.out
    else:
        stem = os.path.splitext(args.path)[0]
        out_path = f"{stem}.{target}"

    if os.path.abspath(out_path) == os.path.abspath(args.path):
        raise ValueError("输出路径不能和原图相同，避免覆盖原图")

    if not cv2.imwrite(out_path, image):
        raise ValueError(f"保存失败，请检查目录是否存在：{out_path}")
    print(f"已保存：{os.path.abspath(out_path)}")


# ---------- 命令行入口 ----------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="imgtool", description="图片信息查看与简单编辑工具")
    sub = parser.add_subparsers(dest="command", required=True, help="子命令")

    p = sub.add_parser("info", help="查看图片基本信息")
    p.add_argument("path", help="图片路径")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("resize", help="缩放图片")
    p.add_argument("path", help="图片路径")
    p.add_argument("-w", "--width", type=int, help="目标宽度（像素）")
    p.add_argument("--height", type=int, help="目标高度（像素）")
    p.add_argument("-o", "--out", help="输出路径，默认 原名_resized.扩展名")
    p.set_defaults(func=cmd_resize)

    p = sub.add_parser("crop", help="裁剪图片")
    p.add_argument("path", help="图片路径")
    p.add_argument("-l", "--left", type=int, required=True, help="左边界 x")
    p.add_argument("-t", "--top", type=int, required=True, help="上边界 y")
    p.add_argument("-r", "--right", type=int, required=True, help="右边界 x")
    p.add_argument("-b", "--bottom", type=int, required=True, help="下边界 y")
    p.add_argument("-o", "--out", help="输出路径")
    p.set_defaults(func=cmd_crop)

    p = sub.add_parser("rotate", help="旋转图片")
    p.add_argument("path", help="图片路径")
    p.add_argument("-d", "--degree", type=int, required=True,
                   choices=[90, 180, 270], help="旋转角度（顺时针）")
    p.add_argument("-o", "--out", help="输出路径")
    p.set_defaults(func=cmd_rotate)

    p = sub.add_parser("flip", help="翻转图片")
    p.add_argument("path", help="图片路径")
    p.add_argument("-m", "--mode", required=True, choices=["h", "v"],
                   help="h=水平翻转，v=垂直翻转")
    p.add_argument("-o", "--out", help="输出路径")
    p.set_defaults(func=cmd_flip)

    p = sub.add_parser("gray", help="灰度化")
    p.add_argument("path", help="图片路径")
    p.add_argument("-o", "--out", help="输出路径")
    p.set_defaults(func=cmd_gray)

    p = sub.add_parser("convert", help="格式转换（png/jpg）")
    p.add_argument("path", help="图片路径")
    p.add_argument("-f", "--format", required=True, choices=["png", "jpg", "jpeg"],
                   help="目标格式")
    p.add_argument("-o", "--out", help="输出路径")
    p.set_defaults(func=cmd_convert)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (FileNotFoundError, ValueError) as exc:
        # 统一兜住可预期的错误，不让程序抛堆栈崩溃
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
