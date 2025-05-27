from PIL import Image, ImageOps

def flip_gif_horizontal(input_path, output_path):
    """
    将输入的GIF文件水平翻转并保存为新的GIF
    :param input_path: 输入GIF文件路径
    :param output_path: 输出GIF文件路径
    """
    with Image.open(input_path) as img:
        # 提取GIF参数
        frames = []
        durations = []
        loop = img.info.get('loop', 0)
        
        try:
            while True:
                # 处理每一帧
                frame = img.copy()
                flipped_frame = ImageOps.mirror(frame)  # 水平翻转
                frames.append(flipped_frame)
                durations.append(img.info['duration'])
                
                # 跳转到下一帧
                img.seek(img.tell() + 1)
                
        except EOFError:
            pass  # 已处理所有帧

        # 保存翻转后的GIF
        if frames:
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=loop
            )

# 使用示例
if __name__ == "__main__":
    flip_gif_horizontal("walk_right.gif", "output.gif")
