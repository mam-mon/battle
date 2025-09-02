import os
import datetime

# --- 配置 ---
# 要搜索的根文件夹 ('.' 代表当前文件夹)
ROOT_DIR = '.'
# 要包含的文件扩展名
FILE_EXTENSIONS = ('.py', '.json')
# 输出文件名
OUTPUT_FILE = 'combined_code.txt'
# --- 结束配置 ---

def combine_files():
    """
    遍历指定目录及其子目录，将特定扩展名的文件内容合并到一个文件中。
    """
    print(f"开始扫描文件夹: {os.path.abspath(ROOT_DIR)}")
    print(f"将要合并的文件类型: {FILE_EXTENSIONS}")
    
    # 使用 with 语句确保文件被正确关闭
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        # 写入文件头部信息
        outfile.write(f"--- 代码合集生成于: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        outfile.write(f"--- 根目录: {os.path.abspath(ROOT_DIR)} ---\n\n")
        
        # os.walk() 会递归地遍历目录
        for dirpath, _, filenames in os.walk(ROOT_DIR):
            for filename in filenames:
                # 检查文件扩展名是否符合要求
                if filename.endswith(FILE_EXTENSIONS):
                    # 构建完整的文件路径
                    file_path = os.path.join(dirpath, filename)
                    # 获取相对路径，这样更清晰
                    relative_path = os.path.relpath(file_path, ROOT_DIR)
                    
                    print(f"正在添加文件: {relative_path}")
                    
                    # 写入文件分隔符和路径信息
                    outfile.write("=" * 80 + "\n")
                    outfile.write(f"### 文件路径: {relative_path}\n")
                    outfile.write("=" * 80 + "\n\n")
                    
                    try:
                        # 读取源文件内容并写入输出文件
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())
                        outfile.write("\n\n\n") # 在文件末尾添加一些空行以作区分
                    except Exception as e:
                        # 如果文件读取失败（例如因为编码问题），则记录错误信息
                        outfile.write(f"*** 无法读取文件: {relative_path} | 错误: {e} ***\n\n\n")

    print(f"\n成功！所有代码已整合到文件: {OUTPUT_FILE}")

if __name__ == '__main__':
    combine_files()