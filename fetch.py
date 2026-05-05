#!/usr/bin/env python3
"""
完整输出 chengaopan/AutoMergePublicNodes 风格的所有文件
所有文件直接保存在 data 目录下（无子文件夹）
支持多个仓库及直接订阅链接，自动处理带日期的订阅（每天获取最新文件）
按真实身份去重（server:port:type:key）
未解析的节点不再输出到任何文件中
"""

import re
import base64
import csv
import json
import yaml
import requests
from pathlib import Path
from urllib.parse import unquote
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# ---------- 1. 下载源配置 ----------
# 静态仓库（直接指定文件路径）
SOURCES = {
    "Barabama": {
        "base_url": "https://raw.githubusercontent.com/Barabama/FreeNodes/main",
        "files": [
            "nodes/yudou66.txt",
            "nodes/nodev2ray.txt",
            "nodes/nodefree.txt",
            "nodes/v2rayshare.txt",
            "nodes/wenode.txt",
            "nodes/ndnode.txt",
            "nodes/blues.txt",
            "nodes/clashmeta.txt",
        ]
    },
    "chengaopan": {
        "base_url": "https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/master",
        "files": ["list_raw.txt"]
    },
    "free_nodes_v2rayfree": {
        "base_url": "https://raw.githubusercontent.com/free-nodes/v2rayfree/main",
        "files": ["README.md"]
    },
    "snakem982_proxypool": {
        "base_url": "https://raw.githubusercontent.com/snakem982/proxypool/main",
        "files": [
            "source/clash-meta.yaml",
            "source/clash-meta-2.yaml",
            "source/v2ray-2.txt"
        ]
    },
    "pachangcheng_mianfeijiedian": {
        "base_url": "https://raw.githubusercontent.com/pachangcheng/mianfeijiedian/main",
        "files": ["README.md"]
    },
    "ccpthisbigdog_freedomchina": {
        "base_url": "https://raw.githubusercontent.com/ccpthisbigdog/freedomchina/refs/heads/main",
        "files": ["clab.yaml", "subdom.txt"]
    },
    "bin1site1_V2rayFree": {
        "base_url": "https://raw.githubusercontent.com/bin1site1/V2rayFree/main",
        "files": ["config.txt"]
    },
    "V2RayAggregator": {
        "base_url": "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master",
        "files": ["Eternity.txt"]
    }
}

# ---------- 2. 直接订阅链接（固定 URL） ----------
DIRECT_SUBSCRIPTIONS = [
    "https://sub.proxygo.org/v2ray.php?key=da43ab0d00ced8482e442845cae7258d",
    "https://raw.githubusercontent.com/cxddgtb/dljdsjq/main/output/nodes.txt",
    "https://raw.githubusercontent.com/cxddgtb/dljdsjq/main/output/nodes_base64.txt",
    "https://raw.githubusercontent.com/cxddgtb/dljdsjq/main/output/easy_proxy_asia.txt",
    "https://raw.githubusercontent.com/cxddgtb/dljdsjq/main/output/easy_proxy_chatgpt.txt",
    "https://raw.githubusercontent.com/cxddgtb/dljdsjq/main/output/easy_proxy_europe.txt",
    "https://raw.githubusercontent.com/cxddgtb/dljdsjq/main/output/easy_proxy_nodes.txt",
    "https://raw.githubusercontent.com/cxddgtb/dljdsjq/main/output/easy_proxy_us_optimized.txt",
    "https://raw.githubusercontent.com/tglaoshiji/nodeshare/main/2026/v2ray.txt",
]

# 带日期的订阅（每天自动获取最新文件）
DATE_BASED_REPOS = [
    {
        "owner": "xibanyahu",
        "repo": "phppachong-freenode",
        "path": "feed",
        "extensions": [".yaml", ".txt"]
    },
    {
        "owner": "danmaifu",
        "repo": "mianfeijiedian",
        "path": "feed",
        "extensions": [".yaml", ".txt"]
    }
]

# ---------- 3. 辅助函数：从 GitHub 仓库目录获取最新文件 ----------
def get_latest_files_from_github(owner: str, repo: str, dir_path: str, extensions: List[str]) -> List[str]:
    """
    通过 GitHub API 获取指定目录下的文件列表，按文件名中的日期排序，返回每个扩展名的最新文件 raw 链接
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{dir_path}"
    try:
        resp = requests.get(api_url, timeout=10)
        resp.raise_for_status()
        items = resp.json()
        files = []
        for item in items:
            if item["type"] == "file":
                name = item["name"]
                if any(name.endswith(ext) for ext in extensions):
                    date_match = re.search(r'(\d{8})', name)
                    if date_match:
                        date_str = date_match.group(1)
                        try:
                            date = datetime.strptime(date_str, "%Y%m%d")
                            files.append((date, name, item["download_url"]))
                        except:
                            pass
        if not files:
            return []
        files.sort(key=lambda x: x[0], reverse=True)
        latest_date = files[0][0]
        latest_files = [url for date, name, url in files if date == latest_date]
        return latest_files
    except Exception as e:
        print(f"获取 {owner}/{repo}/{dir_path} 目录失败: {e}")
        return []

# ---------- 4. 下载文本 ----------
def download_text(url: str) -> Optional[str]:
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"下载失败 {url}: {e}")
        return None

# ---------- 5. 从内容中提取 URI 列表（自动处理 base64 整段）----------
def extract_uris(content: str) -> List[str]:
    uris = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        # 整行 base64 订阅
        if re.fullmatch(r'[A-Za-z0-9+/=]+', line) and len(line) % 4 == 0:
            try:
                decoded = base64.b64decode(line).decode('utf-8')
                if any(decoded.startswith(x) for x in ("vmess://", "trojan://", "vless://", "ss://", "ssr://", "hysteria2://")):
                    for sub in decoded.splitlines():
                        sub = sub.strip()
                        if sub:
                            uris.append(sub)
                    continue
            except:
                pass
        uris.append(line)
    return uris

# ---------- 6. 增强版节点解析器（返回节点详情 + 唯一标识键）----------
def parse_vmess(uri: str) -> Optional[Tuple[Dict, str]]:
    try:
        b64 = uri[8:]
        missing = len(b64) % 4
        if missing:
            b64 += '=' * (4 - missing)
        data = json.loads(base64.b64decode(b64).decode('utf-8'))
        node = {
            "name": data.get("ps", "vmess"),
            "type": "vmess",
            "server": data.get("add", ""),
            "port": int(data.get("port", 0)),
            "protocol": "vmess",
            "uri": uri,
            "uuid": data.get("id", ""),
            "alterId": data.get("aid", 0),
            "cipher": data.get("scy", "auto"),
            "tls": data.get("tls", ""),
        }
        key = f"{node['server']}:{node['port']}:vmess:{node['uuid']}"
        return node, key
    except:
        return None

def parse_trojan(uri: str) -> Optional[Tuple[Dict, str]]:
    try:
        pattern = r"trojan://([^@]+)@([^:]+):(\d+)(.*?)#?(.*)"
        match = re.match(pattern, uri)
        if match:
            pwd, server, port, query, name = match.groups()
            node = {
                "name": unquote(name) if name else "trojan",
                "type": "trojan",
                "server": server,
                "port": int(port),
                "protocol": "trojan",
                "uri": uri,
                "password": pwd,
            }
            key = f"{node['server']}:{node['port']}:trojan:{node['password']}"
            return node, key
    except:
        pass
    return None

def parse_vless(uri: str) -> Optional[Tuple[Dict, str]]:
    try:
        pattern = r"vless://([^@]+)@([^:]+):(\d+)(.*?)#?(.*)"
        match = re.match(pattern, uri)
        if match:
            uuid, server, port, query, name = match.groups()
            node = {
                "name": unquote(name) if name else "vless",
                "type": "vless",
                "server": server,
                "port": int(port),
                "protocol": "vless",
                "uri": uri,
                "uuid": uuid,
            }
            key = f"{node['server']}:{node['port']}:vless:{node['uuid']}"
            return node, key
    except:
        pass
    return None

def parse_ss(uri: str) -> Optional[Tuple[Dict, str]]:
    try:
        if not uri.startswith("ss://"):
            return None
        content = uri[5:]
        fragment = ''
        if '#' in content:
            content, fragment = content.split('#', 1)
        if '@' not in content:
            return None
        method_pass, server_part = content.split('@', 1)
        if ':' not in server_part:
            return None
        server, port_str = server_part.rsplit(':', 1)
        port = int(port_str)
        method = password = ''
        if re.fullmatch(r'[A-Za-z0-9+/=]+', method_pass):
            try:
                decoded = base64.b64decode(method_pass).decode('utf-8')
                if ':' in decoded:
                    method, password = decoded.split(':', 1)
                else:
                    method = method_pass
            except:
                method = method_pass
        else:
            if ':' in method_pass:
                method, password = method_pass.split(':', 1)
            else:
                method = method_pass
        name = unquote(fragment) if fragment else f"ss-{server[:8]}"
        node = {
            "name": name,
            "type": "ss",
            "server": server,
            "port": port,
            "protocol": "ss",
            "uri": uri,
            "method": method,
            "password": password,
        }
        key = f"{node['server']}:{node['port']}:ss:{node['method']}:{node['password']}"
        return node, key
    except:
        return None

def parse_ssr(uri: str) -> Optional[Tuple[Dict, str]]:
    try:
        b64 = uri[6:]
        missing = len(b64) % 4
        if missing:
            b64 += '=' * (4 - missing)
        decoded = base64.b64decode(b64).decode('utf-8')
        parts = decoded.split(":", 5)
        if len(parts) >= 6:
            server = parts[0]
            port = int(parts[1])
            protocol = parts[2]
            method = parts[3]
            obfs = parts[4]
            pwd_b64 = parts[5].split("/")[0] if "/" in parts[5] else parts[5]
            try:
                password = base64.b64decode(pwd_b64).decode('utf-8')
            except:
                password = pwd_b64
            node = {
                "name": "ssr",
                "type": "ssr",
                "server": server,
                "port": port,
                "protocol": "ssr",
                "uri": uri,
                "method": method,
                "password": password,
                "obfs": obfs,
                "protocol_param": protocol,
            }
            key = f"{node['server']}:{node['port']}:ssr:{node['method']}:{node['password']}:{node['obfs']}"
            return node, key
    except:
        pass
    return None

def parse_hysteria2(uri: str) -> Optional[Tuple[Dict, str]]:
    try:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(uri)
        if parsed.scheme != "hysteria2":
            return None
        server = parsed.hostname
        port = parsed.port
        query = parse_qs(parsed.query)
        name = unquote(parsed.fragment) if parsed.fragment else "hysteria2"
        node = {
            "name": name,
            "type": "hysteria2",
            "server": server,
            "port": port,
            "protocol": "hysteria2",
            "uri": uri,
            "auth": query.get("auth", [""])[0],
            "insecure": query.get("insecure", [False])[0] == "1",
            "sni": query.get("sni", [""])[0],
        }
        key = f"{node['server']}:{node['port']}:hysteria2:{node['auth']}"
        return node, key
    except:
        return None

def parse_uri(uri: str) -> Optional[Tuple[Dict, str]]:
    if uri.startswith("vmess://"):
        return parse_vmess(uri)
    elif uri.startswith("trojan://"):
        return parse_trojan(uri)
    elif uri.startswith("vless://"):
        return parse_vless(uri)
    elif uri.startswith("ss://"):
        return parse_ss(uri)
    elif uri.startswith("ssr://"):
        return parse_ssr(uri)
    elif uri.startswith("hysteria2://"):
        return parse_hysteria2(uri)
    else:
        return None

# ---------- 7. 主流程 ----------
def main():
    all_uris = set()

    # 处理静态仓库
    for repo, cfg in SOURCES.items():
        base = cfg["base_url"]
        for f in cfg["files"]:
            url = f"{base}/{f}"
            print(f"下载: {url}")
            text = download_text(url)
            if text:
                uris = extract_uris(text)
                print(f"  提取到 {len(uris)} 条")
                all_uris.update(uris)

    # 处理直接订阅链接（固定 URL）
    for url in DIRECT_SUBSCRIPTIONS:
        print(f"下载订阅: {url}")
        text = download_text(url)
        if text:
            uris = extract_uris(text)
            print(f"  提取到 {len(uris)} 条")
            all_uris.update(uris)

    # 处理带日期的订阅（自动获取最新文件）
    for repo_info in DATE_BASED_REPOS:
        owner = repo_info["owner"]
        repo = repo_info["repo"]
        dir_path = repo_info["path"]
        extensions = repo_info["extensions"]
        print(f"获取 {owner}/{repo}/{dir_path} 最新文件...")
        latest_urls = get_latest_files_from_github(owner, repo, dir_path, extensions)
        for url in latest_urls:
            print(f"下载最新订阅: {url}")
            text = download_text(url)
            if text:
                uris = extract_uris(text)
                print(f"  提取到 {len(uris)} 条")
                all_uris.update(uris)

    print(f"URI 字符串去重后共 {len(all_uris)} 条")

    # 解析所有 URI，按真实身份去重，未解析的直接丢弃
    node_dict = {}
    for uri in all_uris:
        parsed = parse_uri(uri)
        if parsed:
            node, key = parsed
            if key not in node_dict:
                node_dict[key] = node
        else:
            # 未解析的节点直接忽略，不保存
            continue
    unique_nodes = list(node_dict.values())
    print(f"按真实身份去重后得到 {len(unique_nodes)} 个有效节点（未解析的已丢弃）")

    # 准备输出目录
    out_dir = Path("./data")
    out_dir.mkdir(exist_ok=True)

    # 构建最终 raw 列表：仅包含有效节点的原始 URI
    raw_uris = [node['uri'] for node in unique_nodes]
    raw_uris.sort()

    # 1. list_raw.txt
    raw_path = out_dir / "list_raw.txt"
    with open(raw_path, "w", encoding="utf-8") as f:
        for uri in raw_uris:
            f.write(uri + "\n")
    print(f"生成 {raw_path} (共 {len(raw_uris)} 行，全部为可解析节点)")

    # 2. list_ray.txt (相同内容)
    ray_path = out_dir / "list_ray.txt"
    ray_path.write_bytes(raw_path.read_bytes())
    print(f"生成 {ray_path}")

    # 3. list.txt (base64)
    b64_path = out_dir / "list.txt"
    with open(raw_path, "rb") as f:
        raw_bytes = f.read()
    b64_str = base64.b64encode(raw_bytes).decode('ascii')
    with open(b64_path, "w") as f:
        f.write(b64_str)
    print(f"生成 {b64_path}")

    # 4. 构建 proxies 列表用于 YAML
    proxies = []
    for node in unique_nodes:
        p = {
            "name": node["name"],
            "type": node["type"],
            "server": node["server"],
            "port": node["port"],
        }
        if node["type"] == "vmess":
            p.update({
                "uuid": node.get("uuid", ""),
                "alterId": node.get("alterId", 0),
                "cipher": node.get("cipher", "auto"),
                "tls": node.get("tls") == "tls"
            })
        elif node["type"] == "trojan":
            p.update({
                "password": node.get("password", ""),
                "sni": "",
                "skip-cert-verify": True
            })
        elif node["type"] == "vless":
            p.update({
                "uuid": node.get("uuid", ""),
                "flow": "",
                "encryption": "none",
                "tls": False
            })
        elif node["type"] == "ss":
            p.update({
                "cipher": node.get("method", "chacha20-ietf-poly1305"),
                "password": node.get("password", "")
            })
        elif node["type"] == "ssr":
            p.update({
                "cipher": node.get("method", "chacha20-ietf"),
                "password": node.get("password", ""),
                "protocol": node.get("protocol_param", "origin"),
                "obfs": node.get("obfs", "plain")
            })
        elif node["type"] == "hysteria2":
            p.update({
                "auth": node.get("auth", ""),
                "sni": node.get("sni", ""),
                "skip-cert-verify": node.get("insecure", False)
            })
        proxies.append(p)

    # 5. list.yml
    yml_path = out_dir / "list.yml"
    with open(yml_path, "w", encoding="utf-8") as f:
        yaml.dump({"proxies": proxies}, f, allow_unicode=True, sort_keys=False)
    print(f"生成 {yml_path}")

    # 6. list.meta.yml
    groups = [
        {"name": "PROXY", "type": "select", "proxies": [p["name"] for p in proxies] + ["DIRECT"]},
        {"name": "Auto", "type": "url-test", "url": "http://www.gstatic.com/generate_204", "interval": 300, "proxies": [p["name"] for p in proxies]}
    ]
    meta_yml_path = out_dir / "list.meta.yml"
    with open(meta_yml_path, "w", encoding="utf-8") as f:
        yaml.dump({"proxies": proxies, "proxy-groups": groups}, f, allow_unicode=True, sort_keys=False)
    print(f"生成 {meta_yml_path}")

    # 7. list_result.csv
    csv_path = out_dir / "list_result.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "type", "server", "port", "protocol", "uri"])
        writer.writeheader()
        for node in unique_nodes:
            writer.writerow({
                "name": node["name"],
                "type": node["type"],
                "server": node["server"],
                "port": node["port"],
                "protocol": node["protocol"],
                "uri": node["uri"]
            })
    print(f"生成 {csv_path}")

    # 8. nodes.yml
    nodes_yml_path = out_dir / "nodes.yml"
    with open(nodes_yml_path, "w", encoding="utf-8") as f:
        yaml.dump({"proxies": proxies}, f, allow_unicode=True, sort_keys=False)
    print(f"生成 {nodes_yml_path}")

    # 9. adblock.yml (从原仓库下载)
    try:
        adblock_url = "https://raw.githubusercontent.com/chengaopan/AutoMergePublicNodes/master/snippets/adblock.yml"
        r = requests.get(adblock_url, timeout=10)
        if r.status_code == 200:
            (out_dir / "adblock.yml").write_text(r.text, encoding="utf-8")
            print("下载 adblock.yml 完成")
    except:
        pass

    print("\n全部输出完成！输出目录:", out_dir.absolute())
    print(f"去重效果: 原始 URI 字符串去重后 {len(all_uris)} 条，有效解析并去重后 {len(unique_nodes)} 个节点（未解析的已删除）")

if __name__ == "__main__":
    main()
