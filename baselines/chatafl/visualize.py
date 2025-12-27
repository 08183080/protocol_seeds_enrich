#!/usr/bin/env python3
"""
ChatAFL 种子可视化工具 - 极简实现
提供Web界面展示初始种子和丰富后种子的差异
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

# 协议消息类型字典（从chatafl_enricher复制）
PROTOCOL_MESSAGE_TYPES = {
    "FTP": {"USER", "PASS", "ACCT", "CWD", "CDUP", "SMNT", "QUIT", "REIN",
            "PORT", "PASV", "TYPE", "STRU", "MODE", "RETR", "STOR", "STOU",
            "APPE", "ALLO", "REST", "RNFR", "RNTO", "ABOR", "DELE", "RMD",
            "MKD", "PWD", "LIST", "NLST", "SITE", "SYST", "STAT", "HELP",
            "NOOP", "FEAT", "OPTS", "MLSD", "MLST", "SIZE", "MDTM", "XCUP",
            "XMKD", "XPWD", "XCWD"},
    "RTSP": {"DESCRIBE", "ANNOUNCE", "GET_PARAMETER", "OPTIONS", "PAUSE",
             "PLAY", "RECORD", "REDIRECT", "SETUP", "SET_PARAMETER", "TEARDOWN"},
    "HTTP": {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH",
             "TRACE", "CONNECT", "PROPFIND", "PROPPATCH", "MKCOL", "COPY",
             "MOVE", "LOCK", "UNLOCK", "SEARCH"},
    "SMTP": {"HELO", "EHLO", "MAIL", "RCPT", "DATA", "RSET", "VRFY",
             "EXPN", "HELP", "NOOP", "QUIT", "STARTTLS", "AUTH"},
    "SIP": {"INVITE", "ACK", "BYE", "CANCEL", "REGISTER", "OPTIONS",
            "INFO", "PRACK", "UPDATE", "REFER", "SUBSCRIBE", "NOTIFY",
            "PUBLISH", "MESSAGE"},
    "DAAP": {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"}
}


def extract_message_types(content: str, protocol: str) -> Set[str]:
    """从种子内容中提取消息类型"""
    pattern = r'^([A-Z]+)\s+'
    message_types = set()
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        match = re.match(pattern, line)
        if match:
            msg_type = match.group(1).upper()
            if protocol.upper() in PROTOCOL_MESSAGE_TYPES:
                if msg_type in PROTOCOL_MESSAGE_TYPES[protocol.upper()]:
                    message_types.add(msg_type)
            else:
                message_types.add(msg_type)
    
    return message_types


def extract_commands(content: str) -> List[Dict]:
    """提取命令列表，每行一个命令"""
    commands = []
    for i, line in enumerate(content.split('\n'), 1):
        line = line.strip()
        if not line:
            continue
        # 提取命令和参数
        parts = line.split(None, 1)
        cmd = parts[0] if parts else ""
        param = parts[1] if len(parts) > 1 else ""
        commands.append({
            "line": i,
            "command": cmd,
            "parameter": param,
            "full": line
        })
    return commands


def compare_seeds(original: str, enriched: str, protocol: str) -> Dict:
    """比较两个种子文件的差异"""
    orig_types = extract_message_types(original, protocol)
    enri_types = extract_message_types(enriched, protocol)
    
    orig_commands = extract_commands(original)
    enri_commands = extract_commands(enriched)
    
    # 找出新增的消息类型
    added_types = sorted(enri_types - orig_types)
    
    # 找出新增的命令
    # 创建原始命令的集合（用于快速查找）
    orig_lines_set = set(c["full"].strip() for c in orig_commands)
    
    # 标记新增的命令（在丰富后存在但原始中不存在的）
    added_commands = []
    for cmd in enri_commands:
        if cmd["full"].strip() not in orig_lines_set:
            added_commands.append(cmd)
    
    return {
        "original": {
            "content": original,
            "commands": orig_commands,
            "message_types": sorted(orig_types),
            "total_commands": len(orig_commands),
            "total_types": len(orig_types)
        },
        "enriched": {
            "content": enriched,
            "commands": enri_commands,
            "message_types": sorted(enri_types),
            "total_commands": len(enri_commands),
            "total_types": len(enri_types)
        },
        "differences": {
            "added_types": added_types,
            "added_commands": added_commands,
            "type_count_increase": len(enri_types) - len(orig_types),
            "command_count_increase": len(enri_commands) - len(orig_commands)
        }
    }


def find_matching_seeds(seed_dir: Path, enriched_dir: Path) -> List[Dict]:
    """找到初始种子和丰富后种子的对应关系"""
    matches = []
    
    # 获取所有初始种子文件
    if not seed_dir.exists():
        return []
    
    seed_files = [f for f in seed_dir.iterdir() if f.is_file()]
    
    # 获取所有丰富后的种子文件
    enriched_files = []
    if enriched_dir.exists():
        enriched_files = [f for f in enriched_dir.iterdir() if f.is_file()]
    
    # 建立对应关系
    for seed_file in seed_files:
        seed_name = seed_file.stem
        seed_ext = seed_file.suffix
        
        # 查找对应的丰富后文件
        # 格式可能是: enriched_{name} 或 enriched_{name}_1
        matching_enriched = []
        for enriched_file in enriched_files:
            if enriched_file.name.startswith(f"enriched_{seed_name}"):
                matching_enriched.append(enriched_file)
        
        if matching_enriched:
            matches.append({
                "seed_file": str(seed_file),
                "seed_name": seed_file.name,
                "enriched_files": [str(f) for f in matching_enriched]
            })
        else:
            # 没有找到对应的丰富文件，也列出初始种子
            matches.append({
                "seed_file": str(seed_file),
                "seed_name": seed_file.name,
                "enriched_files": []
            })
    
    return matches


@app.route('/')
def index():
    """主页面"""
    return send_from_directory('static', 'index.html')


@app.route('/api/load', methods=['POST'])
def load_seeds():
    """加载种子对比数据"""
    data = request.json
    seed_dir = Path(data.get('seed_dir', ''))
    enriched_dir = Path(data.get('enriched_dir', ''))
    protocol = data.get('protocol', 'HTTP')
    
    if not seed_dir.exists():
        return jsonify({"error": f"种子目录不存在: {seed_dir}"}), 400
    
    matches = find_matching_seeds(seed_dir, enriched_dir)
    
    # 读取并比较每个种子对
    results = []
    for match in matches:
        try:
            # 读取初始种子
            with open(match["seed_file"], 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            # 读取并比较每个丰富后的种子
            for enriched_file in match["enriched_files"]:
                try:
                    with open(enriched_file, 'r', encoding='utf-8', errors='ignore') as f:
                        enriched_content = f.read()
                    
                    comparison = compare_seeds(original_content, enriched_content, protocol)
                    results.append({
                        "seed_name": match["seed_name"],
                        "enriched_name": Path(enriched_file).name,
                        "comparison": comparison
                    })
                except Exception as e:
                    print(f"读取丰富种子失败 {enriched_file}: {e}")
        
        except Exception as e:
            print(f"读取初始种子失败 {match['seed_file']}: {e}")
    
    return jsonify({
        "protocol": protocol,
        "total_pairs": len(results),
        "seed_dir": str(seed_dir),
        "enriched_dir": str(enriched_dir),
        "results": results
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取当前配置文件的路径信息"""
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        return jsonify({"error": "配置文件不存在"}), 404
    
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        seed_dir = config.get('seed_dir', '')
        output_dir = config.get('output_dir', '')
        
        return jsonify({
            "protocol": config.get('protocol', 'HTTP'),
            "seed_dir": seed_dir,
            "enriched_dir": output_dir or str(Path(seed_dir) / "enriched")
        })
    except Exception as e:
        return jsonify({"error": f"读取配置失败: {e}"}), 500


if __name__ == '__main__':
    # 创建静态文件目录
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("ChatAFL 种子可视化工具")
    print("=" * 60)
    print(f"访问地址: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)

