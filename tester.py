#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import csv
import tempfile
import subprocess
import base64
import math
import resource
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========== 配置 ==========
XRAY_KNIFE_PATH = "xray-knife"
NODES_FILE = "data/list_raw.txt"
OUTPUT_VALID_RAW = "data/valid_raw.txt"
OUTPUT_VALID_B64 = "data/valid.txt"
CONCURRENT = 10          # xray-knife 内部并发数（一次测试多个节点）
BATCH_SIZE = 200         # 每批节点数

os.makedirs("data", exist_ok=True)
os.makedirs("data/tmp", exist_ok=True)

def set_child_limits():
    """设置子进程资源限制"""
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
        resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))
    except Exception:
        pass

def test_chunk(uri_list, max_workers):
    """测试一批节点，返回通过的 URI 列表"""
    if not uri_list:
        return []
    fd, tmp_file = tempfile.mkstemp(suffix=".txt", dir="data/tmp")
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(uri_list))
    cmd = [XRAY_KNIFE_PATH, "http", "-f", tmp_file, "-t", str(max_workers), "-x", "csv", "-o", tmp_file+".csv"]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=300, preexec_fn=set_child_limits)
        valid = []
        if os.path.exists(tmp_file+".csv"):
            with open(tmp_file+".csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("status", "").strip().lower() == "passed":
                        link = row.get("link", "").strip()
                        if link:
                            valid.append(link)
        return valid
    except Exception as e:
        print(f"批次测试失败: {e}")
        return []
    finally:
        for f in [tmp_file, tmp_file+".csv"]:
            if os.path.exists(f):
                os.unlink(f)

def main():
    if not os.path.exists(NODES_FILE):
        print(f"错误: 节点文件 {NODES_FILE} 不存在，请先运行 fetch.py")
        sys.exit(1)
    with open(NODES_FILE, "r") as f:
        all_uris = [line.strip() for line in f if line.strip()]
    print(f"从 {NODES_FILE} 读取到 {len(all_uris)} 个节点")

    # 分批测试
    total = len(all_uris)
    num_batches = math.ceil(total / BATCH_SIZE)
    valid_uris = []
    for i in range(num_batches):
        chunk = all_uris[i*BATCH_SIZE : (i+1)*BATCH_SIZE]
        print(f"批次 {i+1}/{num_batches}，测试 {len(chunk)} 个节点...")
        batch_valid = test_chunk(chunk, CONCURRENT)
        valid_uris.extend(batch_valid)
        print(f"  本批次可用: {len(batch_valid)}，累计: {len(valid_uris)}")

    # 写入明文文件
    with open(OUTPUT_VALID_RAW, "w") as f:
        f.write("\n".join(valid_uris))
    # 写入 Base64 编码的订阅文件
    if valid_uris:
        b64_content = base64.b64encode("\n".join(valid_uris).encode()).decode()
        with open(OUTPUT_VALID_B64, "w") as f:
            f.write(b64_content)
    else:
        open(OUTPUT_VALID_B64, "w").close()
    print(f"测试完成，可用节点数: {len(valid_uris)}")
    print(f"明文: {OUTPUT_VALID_RAW}")
    print(f"订阅: {OUTPUT_VALID_B64}")

if __name__ == "__main__":
    main()
