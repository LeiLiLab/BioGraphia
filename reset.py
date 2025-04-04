#!/usr/bin/env python3
import os
import json
import shutil
from pathlib import Path

def main():
    # 添加确认提示
    print("警告: 即将重置系统，此操作将会:")
    print("  1. 清空 Main_dir 和 Temp_dir 目录下的所有内容")
    print("  2. 删除 graph_debug.json, original_output.json, All_list.txt, temp_test_list.txt 和 test.py 文件")
    print("  3. 清空 statistic.json 和 user_access.json 文件内容")
    print("  注意: Prompt.json, users.json 和 type_name_database.json 文件不会被修改")
    print("\n请确认是否继续? (输入 'yes' 或 'y' 确认，输入其他内容取消): ", end="")
    
    confirmation = input().strip().lower()
    if confirmation not in ["yes", "y"]:
        print("操作已取消。")
        return
    
    # Get the directory this script is in
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Data directory path
    data_dir = script_dir / "data"
    
    print("\n开始系统重置...")
    
    # 1. 清空 Main_dir 和 Temp_dir 目录
    print("1. 清空 Main_dir 和 Temp_dir 目录...")
    main_dir = data_dir / "Main_dir"
    temp_dir = data_dir / "Temp_dir"
    
    # 确保目录存在
    for directory in [main_dir, temp_dir]:
        if directory.exists():
            # 删除目录内所有内容但保留目录本身
            for item in directory.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    os.remove(item)
            print(f"  - 成功清空 {directory.name} 目录")
        else:
            print(f"  - 警告: {directory.name} 目录不存在，已跳过")
    
    # 2. 删除指定的文件
    print("2. 删除指定的文件...")
    files_to_delete = [
        "graph_debug.json",
        "original_output.json",
        "All_list.txt",
        "temp_test_list.txt",
        "test.py"
    ]
    
    for file_name in files_to_delete:
        file_path = data_dir / file_name
        if file_path.exists():
            os.remove(file_path)
            print(f"  - 成功删除 {file_name}")
        else:
            print(f"  - 警告: {file_name} 不存在，已跳过")
    
    # 4. 清空 statistic.json 和 user_access.json 但保留结构
    print("3. 清空 statistic.json 和 user_access.json 文件...")
    
    # 处理 statistic.json
    statistic_path = data_dir / "statistic.json"
    if statistic_path.exists():
        # 清空为一个空字典
        with open(statistic_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=2)
        print("  - 成功清空 statistic.json")
    else:
        print("  - 警告: statistic.json 不存在，已跳过")
    
    # 处理 user_access.json
    user_access_path = data_dir / "user_access.json"
    if user_access_path.exists():
        # 清空为一个空字典
        with open(user_access_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=2)
        print("  - 成功清空 user_access.json")
    else:
        print("  - 警告: user_access.json 不存在，已跳过")
    
    print("系统重置完成！")

if __name__ == "__main__":
    main() 