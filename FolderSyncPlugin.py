import os
import shutil

def sync_folders(src, tgt, counters):
    """
    递归同步 src 与 tgt 文件夹，使 tgt 成为 src 的完整镜像。

    参数：
      - src: 源文件夹路径
      - tgt: 目标文件夹路径
      - counters: 用于统计操作次数的字典，包含 'copied', 'updated', 'deleted', 'skipped'
    """
    # 确保目标文件夹存在
    if not os.path.exists(tgt):
        os.makedirs(tgt)
    
    # 1. 遍历源文件夹，处理新增和更新
    for entry in os.listdir(src):
        src_entry = os.path.join(src, entry)
        tgt_entry = os.path.join(tgt, entry)
        if os.path.isdir(src_entry):
            # 递归同步子文件夹
            sync_folders(src_entry, tgt_entry, counters)
        else:
            # 如果目标中不存在该文件，则拷贝
            if not os.path.exists(tgt_entry):
                shutil.copy2(src_entry, tgt_entry)
                counters["copied"] += 1
            else:
                # 如果目标中存在，但源文件更新，则覆盖
                if os.path.getmtime(src_entry) > os.path.getmtime(tgt_entry):
                    shutil.copy2(src_entry, tgt_entry)
                    counters["updated"] += 1
                else:
                    counters["skipped"] += 1

    # 2. 遍历目标文件夹，删除那些在源文件夹中不存在的文件或目录
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

    参数 params 为字典，必须包含：
      - "src": 源文件夹路径
      - "tgt": 目标文件夹路径

    返回字符串，描述操作结果。
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
