#!/usr/bin/env python3
import os
import sys
import shutil
import zipfile
import json
import tempfile
import subprocess

def prompt_file_path(prompt):
    """提示用户输入存在的文件路径"""
    path = input(prompt).strip().strip('"')
    while not os.path.isfile(path):
        print("文件不存在，请重新输入。")
        path = input(prompt).strip().strip('"')
    return os.path.abspath(path)

def prompt_directory_path(prompt):
    """提示用户输入存在的目录路径"""
    path = input(prompt).strip().strip('"')
    while not os.path.isdir(path):
        print("目录不存在，请重新输入。")
        path = input(prompt).strip().strip('"')
    return os.path.abspath(path)

def ensure_pipreqs_installed():
    """确保 pipreqs 已安装，如果未安装则自动安装"""
    try:
        import pipreqs  # 尝试导入
    except ImportError:
        print("pipreqs 未安装，正在自动安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pipreqs"], timeout=60)
        except Exception as e:
            print("安装 pipreqs 失败，请先手动安装 pipreqs。")
            sys.exit(1)

def generate_requirements(src_dir):
    """
    使用 pipreqs 自动扫描 src_dir 目录生成 requirements.txt
    返回生成的 requirements.txt 文件路径
    """
    print("正在自动生成 requirements.txt ...")
    # 先尝试查找命令行中的 pipreqs 命令
    pipreqs_path = shutil.which("pipreqs")
    if pipreqs_path:
        cmd = [pipreqs_path, src_dir, "--force"]
    else:
        # 如果没有在 PATH 中找到，则尝试使用 python -m pipreqs.pipreqs
        cmd = [sys.executable, "-m", "pipreqs.pipreqs", src_dir, "--force"]
    try:
        subprocess.check_call(cmd, timeout=60)
    except subprocess.TimeoutExpired:
        print("生成 requirements.txt 超时，请检查网络环境和 pipreqs 是否正常工作。")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"生成 requirements.txt 时出错：{e}")
        sys.exit(1)
    
    req_file = os.path.join(src_dir, "requirements.txt")
    if not os.path.exists(req_file):
        print("requirements.txt 未生成，请检查 pipreqs 输出。")
        sys.exit(1)
    print(f"requirements.txt 生成成功：{req_file}")
    return req_file

def download_dependencies(requirements_file, dest_vendor):
    """
    使用 pip download 根据 requirements.txt 下载依赖到 dest_vendor 目录
    """
    print("开始下载依赖包...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "download", "-d", dest_vendor, "-r", requirements_file],
            timeout=120
        )
    except subprocess.TimeoutExpired:
        print("下载依赖超时，请检查网络环境。")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"下载依赖时出错：{e}")
        sys.exit(1)
    print("依赖包下载完成。")

def main():
    print("====================================")
    print("欢迎使用 OttoPie 插件打包工具")
    print("====================================")
    print("该工具将引导您将插件脚本、依赖及插件信息打包成 .ottopie 文件。")
    print()
    
    # 1. 输入插件主脚本路径
    script_path = prompt_file_path("请输入插件主脚本文件的完整路径（例如：plugin.py）：")
    
    # 2. 输入插件的基本信息
    default_name = os.path.splitext(os.path.basename(script_path))[0]
    plugin_name = input(f"请输入插件名称（默认：{default_name}）：").strip() or default_name
    plugin_version = input("请输入插件版本（例如：1.0.0，默认：1.0.0）：").strip() or "1.0.0"
    plugin_description = input("请输入插件描述：").strip()
    entry_point = input(f"请输入插件入口模块文件名（默认：{os.path.basename(script_path)}）：").strip() or os.path.basename(script_path)
    
    # 3. 指定输出插件包的文件名（不含扩展名）
    output_name = input(f"请输入生成插件包的文件名（默认：{plugin_name}）：").strip() or plugin_name
    output_file = os.path.abspath(output_name + ".ottopie")
    
    print("\n开始打包插件……")
    # 4. 创建临时目录构建插件包目录结构
    temp_dir = tempfile.mkdtemp(prefix="ottopie_pack_")
    print(f"创建临时工作目录：{temp_dir}")
    
    # 在临时目录内创建插件包根目录
    package_root = os.path.join(temp_dir, plugin_name)
    os.makedirs(package_root, exist_ok=True)
    
    # 4.1 复制插件主脚本到包中，命名为 entry_point
    dest_script_path = os.path.join(package_root, entry_point)
    shutil.copy2(script_path, dest_script_path)
    print(f"复制插件主脚本到：{dest_script_path}")
    
    # 4.2 自动生成 requirements.txt（在插件包根目录中生成）
    ensure_pipreqs_installed()
    req_file = generate_requirements(package_root)
    
    # 4.3 创建 vendor 目录，并下载依赖到该目录
    dest_vendor_path = os.path.join(package_root, "vendor")
    os.makedirs(dest_vendor_path, exist_ok=True)
    download_dependencies(req_file, dest_vendor_path)
    
    # 4.4 生成 plugin.json 文件，保存插件元数据
    plugin_metadata = {
        "name": plugin_name,
        "version": plugin_version,
        "entry_point": entry_point,
        "description": plugin_description
    }
    metadata_path = os.path.join(package_root, "plugin.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(plugin_metadata, f, ensure_ascii=False, indent=4)
    print(f"生成插件元数据文件：{metadata_path}")
    
    # 5. 将整个 package_root 目录打包为 zip 文件，再改名为 .ottopie
    zip_filename = os.path.join(temp_dir, plugin_name + ".zip")
    print("正在打包插件目录...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_root):
            for file in files:
                abs_file = os.path.join(root, file)
                # 保持相对路径（相对于 package_root）
                rel_path = os.path.relpath(abs_file, package_root)
                zipf.write(abs_file, arcname=rel_path)
    shutil.move(zip_filename, output_file)
    
    print("====================================")
    print(f"插件打包完成，生成文件：{output_file}")
    print("临时文件将被清理。")
    print("====================================")
    
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
