# OttoPie - 自动化 Python 任务管理平台 🐙🥧

![OttoPie Logo](image.webp)

**OttoPie** 是一款跨平台的 Python 自动化任务管理工具。它的名字来源于 "Otto"（八爪鱼 🐙，谐音 Auto，代表多任务与自动化）和 "Pie"（谐音派，代表 Python 生态）。OttoPie 让你像八爪鱼一样灵活管理多个 Python 自动化任务，并提供图形化界面、定时调度、脚本管理、日志记录以及插件化扩展功能。

---

## ✨ 功能特点

- **📋 脚本管理**：支持加载、删除、配置 Python 脚本，让任务管理更直观。
- **⏳ 任务调度**：支持定时执行 Python 脚本，自动化处理日常任务。
- **📂 文件监控**：可结合插件脚本，实现对文件夹变化的实时监控。
- **🖥️ 图形界面**：基于 PyQt 构建，无需命令行即可操作。
- **💾 任务日志**：集中记录脚本运行日志，方便查看执行状态。
- **🔌 插件式架构**：支持自定义插件扩展功能，只需实现简单接口，即可轻松扩展。
- **📦 插件打包**：插件开发者可将插件打包成自包含包，扩展名为 **.ottopie**，插件包内包含插件代码、元数据和所有依赖，保证离线环境下也能正常使用。

---

## 🚀 安装与运行

### 安装依赖

OttoPie 基于 Python 3 运行，请确保已安装 Python 3.x。

### 运行 OttoPie

该项目已包含虚拟环境文件 venv.zip，需要解压后使用。为了方便使用，已经添加了各平台一键启动脚本，存放于 run_scripts/ 目录中。
根据所在平台，使用相应脚本启动主程序：
Windows：双击 run_scripts/windows_main.bat
macOS：双击 run_scripts/macos_main.command
Linux：在终结中运行 ./run_scripts/linux_main.sh

如需要运行插件打包程序：
Windows：双击 run_scripts/windows_packager.bat
macOS：双击 run_scripts/macos_packager.command
Linux：在终结中运行 ./run_scripts/linux_packager.sh

运行脚本会自动检查并解压 venv.zip，使用虚拟环境运行 OttoPie。
---

## 🏗️ 使用指南

### 1️⃣ 添加任务

1. 打开 OttoPie，进入“脚本管理”页面。
2. 点击 **“添加任务”** 按钮，弹出脚本配置窗口：
   - **选择脚本文件**：你可以选择传统的 Python 脚本（`.py` 文件）或打包为 **.ottopie** 格式的插件包。
   - 选择 **源文件夹** 和 **目标文件夹**（如果任务需要）。
   - 设置 **执行间隔**，支持天、小时、分钟和秒的灵活设置。
3. 点击 **确定** 后，任务会添加到任务列表中。

### 2️⃣ 启动 / 停止任务

- 在“脚本管理”页面，点击 **“启动”** 按钮，任务将按照设定的间隔执行。
- 点击 **“停止”** 按钮，可暂停任务执行。

### 3️⃣ 编辑任务配置

- 点击 **“编辑配置”** 按钮，可重新配置任务参数（如脚本文件、执行间隔、源/目标文件夹等）。
- 编辑时任务会自动停止，修改完成后可重新启动任务。

### 4️⃣ 删除任务

- 点击 **“删除”** 按钮，可将任务从列表中移除（不会删除实际脚本文件）。

### 5️⃣ 查看日志

- 切换到 **“任务日志”** 选项卡，查看任务的运行状态和历史记录。

---

## 🔌 插件开发与打包

OttoPie 采用插件化架构，允许你扩展更多功能。插件必须以 **.py** 脚本或打包为 **.ottopie** 文件的形式加载。

### 1. 插件接口规范

每个插件（无论是单个 .py 脚本还是打包后的 .ottopie 插件包）都必须实现如下接口：

#### 必须实现 `run(params)` 函数

- **参数**：  
  - `params` 是一个字典，包含任务运行时传入的配置信息。  
    例如，对于文件同步任务，`params` 可能包含：
    - `"src"`：源文件夹路径
    - `"tgt"`：目标文件夹路径

- **返回值**：  
  - `run(params)` 函数必须返回一个字符串，用于记录任务执行结果（如成功信息或错误描述）。

#### 示例说明

以下示例展示了一个插件如何实现 `run(params)` 接口。插件功能为递归同步源文件夹与目标文件夹，并统计拷贝、更新、删除和跳过的文件数：

```python
import os
import shutil

def sync_folders(src, tgt, counters):
    """
    递归同步 src 与 tgt 文件夹，使 tgt 成为 src 的完整镜像。

    参数：
      - src: 源文件夹路径
      - tgt: 目标文件夹路径
      - counters: 统计操作次数的字典，包括 'copied', 'updated', 'deleted', 'skipped'
    """
    if not os.path.exists(tgt):
        os.makedirs(tgt)
    
    for entry in os.listdir(src):
        src_entry = os.path.join(src, entry)
        tgt_entry = os.path.join(tgt, entry)
        if os.path.isdir(src_entry):
            sync_folders(src_entry, tgt_entry, counters)
        else:
            if not os.path.exists(tgt_entry):
                shutil.copy2(src_entry, tgt_entry)
                counters["copied"] += 1
            else:
                if os.path.getmtime(src_entry) > os.path.getmtime(tgt_entry):
                    shutil.copy2(src_entry, tgt_entry)
                    counters["updated"] += 1
                else:
                    counters["skipped"] += 1

    for entry in os.listdir(tgt):
        tgt_entry = os.path.join(tgt, entry)
        src_entry = os.path.join(src, entry)
        if not os.path.exists(src_entry):
            if os.path.isdir(tgt_entry):
                shutil.rmtree(tgt_entry)
            else:
                os.remove(tgt_entry)
            counters["deleted"] += 1

def run(params):
    """
    同步任务接口，必须实现 run(params) 接口。

    参数：
      - params: 字典，必须包含 "src"（源文件夹路径）和 "tgt"（目标文件夹路径）

    返回：
      - 字符串，描述操作结果
    """
    src = params.get("src", "").strip()
    tgt = params.get("tgt", "").strip()
    
    if not src or not tgt:
        return "错误：请指定源文件夹和目标文件夹。"
    if not os.path.isdir(src):
        return "错误：源文件夹不存在。"
    
    counters = {"copied": 0, "updated": 0, "deleted": 0, "skipped": 0}
    
    try:
        sync_folders(src, tgt, counters)
        return ("同步完成：复制文件 {copied} 个，更新文件 {updated} 个，删除文件 {deleted} 个，跳过 {skipped} 个文件。"
                .format(**counters))
    except Exception as e:
        return "同步过程中发生错误: " + str(e)
```

### 2. 插件打包工具

为了方便插件开发者打包插件，OttoPie 提供了一个插件打包工具，该工具可以自动：
- 自动扫描插件代码生成 `requirements.txt`（对于依赖较多的插件）；
- 使用 `pip download` 下载依赖到 `vendor` 目录中（保证离线时可用）；
- 按照标准格式生成插件包，输出扩展名为 **.ottopie**。

#### 使用说明

1. **运行打包工具**  
   在命令行中执行：
   ```sh
   python ottopie_packager.py
   ```
   （请确保环境中已安装 Python、pip 和 pipreqs。）

2. **依次输入提示信息**  
   - 输入插件主脚本文件路径（例如 `plugin.py`）。
   - 填写插件基本信息（名称、版本、描述、入口模块文件名）。
   - 工具自动在临时插件目录中运行 pipreqs 生成 `requirements.txt`，然后自动下载依赖到 `vendor` 目录中。
   - 输入生成的插件包名称（不含扩展名），工具会生成扩展名为 `.ottopie` 的插件包。

3. **生成的插件包**  
   打包工具生成的插件包将包含：
   - 插件主脚本（入口模块）
   - 自动生成的 `requirements.txt`（可选，仅供参考）
   - `plugin.json`（插件元数据）
   - `vendor/` 目录（所有依赖包）

该插件包可直接在 OttoPie 中加载使用。

---

## 📜 许可证

OttoPie 遵循 MIT 许可证，你可以自由使用、修改和分发本软件。

---

OttoPie —— 让你的 Python 任务自动化管理变得更简单！🐙🥧

