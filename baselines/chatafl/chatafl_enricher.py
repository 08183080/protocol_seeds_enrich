"""
ChatAFL 种子丰富方法复现
基于 LLM 的协议种子丰富化实现

核心流程：
1. 获取协议的所有消息类型
2. 从现有种子中提取已使用的消息类型
3. 识别缺失的消息类型
4. 使用 LLM 在合适位置添加缺失的消息类型
"""

import os
import re
import json
import requests
import subprocess
import random
from typing import List, Set, Dict, Optional
from collections import Counter
from pathlib import Path


def get_wsl_host_ip():
    """
    获取 WSL 宿主机的 IP 地址
    
    在 WSL2 环境中，访问 Windows localhost 服务的最佳方式是：
    1. 直接使用 localhost（WSL2 会自动转发到 Windows）
    2. 或者使用 Windows 主机的 IP 地址
    
    注意：WSL2 会自动将 localhost 转发到 Windows，所以通常不需要特殊处理。
    但如果需要显式使用 Windows IP，可以通过默认网关获取。
    
    Returns:
        宿主机 IP 地址，如果无法获取则返回 "localhost"
    """
    try:
        # 通过 ip route 命令获取默认网关（Windows 主机的 IP）
        result = subprocess.run(['ip', 'route'], capture_output=True, text=True, timeout=5)
        for line in result.stdout.splitlines():
            if 'default via' in line:
                parts = line.split()
                if len(parts) >= 3:
                    return parts[2]
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, Exception):
        pass
    # WSL2 中，localhost 会自动转发到 Windows，所以返回 localhost
    return "localhost"


class ChatAFLEnricher:
    """ChatAFL 种子丰富器"""
    
    # 配置常量（来自原始 C 代码）
    MAX_TOKENS = 2048
    CONFIDENT_TIMES = 3  # 用于一致性检查的查询次数
    MAX_ENRICHMENT_MESSAGE_TYPES = 2  # 每次最多添加的消息类型数
    MAX_ENRICHMENT_CORPUS_SIZE = 10  # 最多检查的种子数
    ENRICHMENT_RETRIES = 5
    MESSAGE_TYPE_RETRIES = 5
    MAX_ENRICHED_SEEDS_PER_FILE = 1  # 每个原始种子最多生成的丰富种子数量
    TEMPERATURE = 0.5  # LLM 温度参数（控制输出的随机性，0.0-2.0）
    
    # 协议消息类型硬编码字典
    PROTOCOL_MESSAGE_TYPES = {
        "FTP": {
            "USER", "PASS", "ACCT", "CWD", "CDUP", "SMNT", "QUIT", "REIN",
            "PORT", "PASV", "TYPE", "STRU", "MODE", "RETR", "STOR", "STOU",
            "APPE", "ALLO", "REST", "RNFR", "RNTO", "ABOR", "DELE", "RMD",
            "MKD", "PWD", "LIST", "NLST", "SITE", "SYST", "STAT", "HELP",
            "NOOP", "FEAT", "OPTS", "MLSD", "MLST", "SIZE", "MDTM", "XCUP",
            "XMKD", "XPWD", "XCWD"
        },
        "RTSP": {
            "DESCRIBE", "ANNOUNCE", "GET_PARAMETER", "OPTIONS", "PAUSE",
            "PLAY", "RECORD", "REDIRECT", "SETUP", "SET_PARAMETER", "TEARDOWN"
        },
        "HTTP": {
            "GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH",
            "TRACE", "CONNECT", "PROPFIND", "PROPPATCH", "MKCOL", "COPY",
            "MOVE", "LOCK", "UNLOCK", "SEARCH"
        },
        "SMTP": {
            "HELO", "EHLO", "MAIL", "RCPT", "DATA", "RSET", "VRFY",
            "EXPN", "HELP", "NOOP", "QUIT", "STARTTLS", "AUTH"
        },
        "SIP": {
            "INVITE", "ACK", "BYE", "CANCEL", "REGISTER", "OPTIONS",
            "INFO", "PRACK", "UPDATE", "REFER", "SUBSCRIBE", "NOTIFY",
            "PUBLISH", "MESSAGE"
        },
        "DAAP": {
            "GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"
        }
    }
    
    def __init__(self, api_key: Optional[str] = None, 
                 model: str = "gpt-3.5-turbo",
                 api_url: Optional[str] = None,
                 use_local: bool = False):
        """
        初始化 ChatAFL 丰富器
        
        Args:
            api_key: API key，如果为 None 则从环境变量获取
            model: 使用的模型名称
            api_url: 自定义 API URL（用于本地部署的模型，如 Ollama）
            use_local: 是否使用本地模型（如 Ollama），如果为 True，api_url 必须设置
        """
        self.use_local = use_local
        self.api_url = api_url
        
        if use_local:
            # 本地模型（如 Ollama）不需要 API key 或使用默认值
            if not api_url:
                # WSL2 中，localhost 会自动转发到 Windows，所以直接使用 localhost
                self.api_url = "http://localhost:11434/v1"
                print(f"使用默认 localhost（WSL2 会自动转发到 Windows）")
            elif "localhost" in api_url or "127.0.0.1" in api_url:
                # 在 WSL2 中，localhost 会自动转发到 Windows，所以保持 localhost
                # 只有在明确需要 Windows IP 时才替换
                self.api_url = api_url
                print(f"使用 localhost（WSL2 会自动转发到 Windows 上的 Ollama）")
            else:
                # 用户明确指定了其他地址，直接使用
                self.api_url = api_url
                print(f"使用指定的 API URL: {api_url}")
            self.api_key = api_key or "ollama"  # Ollama 不需要真实的 key
        else:
            # OpenAI 或其他远程 API
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("需要提供 API key (通过参数或环境变量 OPENAI_API_KEY)")
            
            # 如果提供了自定义 URL，使用它；否则使用 OpenAI 默认 URL
            if api_url:
                self.api_url = api_url
            else:
                self.api_url = "https://api.openai.com/v1"
        
        self.model = model
        
    def chat_with_llm(self, prompt: str, model_type: str = "chat", 
                     temperature: float = 0.5, max_retries: int = 5) -> Optional[str]:
        """
        与 LLM 交互（支持 OpenAI 和本地模型如 Ollama）
        
        Args:
            prompt: 提示词
            model_type: 模型类型 ("instruct" 或 "chat")
            temperature: 温度参数
            max_retries: 最大重试次数
            
        Returns:
            LLM 的响应文本，失败返回 None
        """
        for attempt in range(max_retries):
            try:
                if self.use_local:
                    # 使用本地模型（如 Ollama）
                    return self._call_local_llm(prompt, model_type, temperature)
                else:
                    # 使用 OpenAI 或其他兼容 API
                    return self._call_remote_llm(prompt, model_type, temperature)
            except Exception as e:
                print(f"LLM 调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2)
                else:
                    return None
        return None
    
    def _call_local_llm(self, prompt: str, model_type: str, temperature: float) -> Optional[str]:
        """
        调用本地模型（如 Ollama）
        
        Args:
            prompt: 提示词
            model_type: 模型类型 ("instruct" 或 "chat")
            temperature: 温度参数
            
        Returns:
            LLM 的响应文本
        """
        headers = {
            "Content-Type": "application/json",
        }
        
        # Ollama 不需要 Authorization header，但有些实现需要
        if self.api_key and self.api_key != "ollama":
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        if model_type == "instruct":
            # 使用 completions 端点
            url = f"{self.api_url}/completions"
            data = {
                "model": self.model,
                "prompt": prompt,
                "max_tokens": self.MAX_TOKENS,
                "temperature": temperature
            }
        else:
            # 使用 chat/completions 端点
            url = f"{self.api_url}/chat/completions"
            messages = json.loads(prompt) if isinstance(prompt, str) else prompt
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.MAX_TOKENS,
                "temperature": temperature
            }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            result = response.json()
            
            # 检查响应格式
            if "choices" not in result or len(result["choices"]) == 0:
                print(f"  错误: API 响应格式异常，未找到 choices 字段")
                print(f"  响应内容: {result}")
                return None
            
            if model_type == "instruct":
                if "text" not in result["choices"][0]:
                    print(f"  错误: API 响应格式异常，未找到 text 字段")
                    print(f"  响应内容: {result}")
                    return None
                answer = result["choices"][0]["text"].strip()
            else:
                if "message" not in result["choices"][0] or "content" not in result["choices"][0]["message"]:
                    print(f"  错误: API 响应格式异常，未找到 message.content 字段")
                    print(f"  响应内容: {result}")
                    return None
                answer = result["choices"][0]["message"]["content"].strip()
            
            # 移除开头的换行符
            if answer.startswith('\n'):
                answer = answer[1:]
            
            return answer
            
        except requests.exceptions.RequestException as e:
            print(f"  网络错误: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"  错误详情: {error_detail}")
                except:
                    print(f"  响应状态码: {e.response.status_code}")
                    print(f"  响应内容: {e.response.text[:200]}")
            return None
        except Exception as e:
            print(f"  未知错误: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _call_remote_llm(self, prompt: str, model_type: str, temperature: float) -> Optional[str]:
        """
        调用远程 API（OpenAI 或兼容 API）
        
        Args:
            prompt: 提示词
            model_type: 模型类型 ("instruct" 或 "chat")
            temperature: 温度参数
            
        Returns:
            LLM 的响应文本
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        if model_type == "instruct":
            # 使用 completions 端点
            url = f"{self.api_url}/completions"
            data = {
                "model": self.model,
                "prompt": prompt,
                "max_tokens": self.MAX_TOKENS,
                "temperature": temperature
            }
        else:
            # 使用 chat/completions 端点
            url = f"{self.api_url}/chat/completions"
            messages = json.loads(prompt) if isinstance(prompt, str) else prompt
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.MAX_TOKENS,
                "temperature": temperature
            }
        
        response = requests.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        if model_type == "instruct":
            answer = result["choices"][0]["text"].strip()
        else:
            answer = result["choices"][0]["message"]["content"].strip()
        
        # 移除开头的换行符
        if answer.startswith('\n'):
            answer = answer[1:]
        
        return answer
    
    def construct_prompt_for_message_types(self, protocol_name: str) -> str:
        """
        构建获取协议消息类型的提示词（chat 格式）
        
        注意：此方法已废弃，协议消息类型现在从硬编码字典 PROTOCOL_MESSAGE_TYPES 获取。
        保留此方法仅用于向后兼容。
        
        Args:
            protocol_name: 协议名称（如 "RTSP", "FTP"）
            
        Returns:
            Chat 格式的 messages（JSON 字符串）
        """
        user_message = (
            f"In the {protocol_name} protocol, the message types are: \n\n"
            f"Desired format:\n"
            f"<comma_separated_list_of_states_in_uppercase_and_without_whitespaces>"
        )
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_message}
        ]
        
        return json.dumps(messages)
    
    def construct_prompt_for_templates(self, protocol_name: str) -> str:
        """
        构建获取协议消息模板的提示词（Few-shot 方式）
        
        Args:
            protocol_name: 协议名称
            
        Returns:
            提示词字符串
        """
        rtsp_example = (
            "For the RTSP protocol, the DESCRIBE client request template is:\n"
            'DESCRIBE: ["DESCRIBE <<VALUE>>\\r\\n", "CSeq: <<VALUE>>\\r\\n", '
            '"User-Agent: <<VALUE>>\\r\\n", "Accept: <<VALUE>>\\r\\n", "\\r\\n"]'
        )
        
        http_example = (
            "For the HTTP protocol, the GET client request template is:\n"
            'GET: ["GET <<VALUE>>\\r\\n"]'
        )
        
        prompt = (
            f"{rtsp_example}\n"
            f"{http_example}\n"
            f"For the {protocol_name} protocol, all of client request templates are:"
        )
        return prompt
    
    def format_string(self, text: str) -> str:
        """
        格式化字符串：移除首尾的空白字符和换行符
        
        Args:
            text: 输入文本
            
        Returns:
            格式化后的文本
        """
        # 移除开头的空白字符
        text = text.lstrip('\n \t\r')
        # 移除结尾的空白字符和点号
        text = text.rstrip('\n\r .')
        return text
    
    def get_protocol_message_types(self, protocol_name: str) -> Set[str]:
        """
        获取协议的所有消息类型（从硬编码字典获取）
        
        Args:
            protocol_name: 协议名称
            
        Returns:
            消息类型集合
        """
        protocol_upper = protocol_name.upper()
        
        # 从硬编码字典获取
        if protocol_upper in self.PROTOCOL_MESSAGE_TYPES:
            message_types = self.PROTOCOL_MESSAGE_TYPES[protocol_upper]
            print(f"协议 {protocol_name} 的消息类型（从字典获取）: {sorted(message_types)}")
            return message_types
        else:
            print(f"警告: 协议 {protocol_name} 不在支持的协议列表中")
            print(f"支持的协议: {list(self.PROTOCOL_MESSAGE_TYPES.keys())}")
            print(f"返回空集合")
            return set()
    
    def extract_message_types_from_seed(self, seed_content: str, 
                                       protocol_name: str) -> Set[str]:
        """
        从种子内容中提取已使用的消息类型
        
        Args:
            seed_content: 种子文件内容
            protocol_name: 协议名称（用于特定协议的解析）
            
        Returns:
            提取到的消息类型集合
        """
        message_types = set()
        
        # 根据协议类型使用不同的解析方法
        if protocol_name.upper() == "RTSP":
            # RTSP: 提取第一行的命令（如 DESCRIBE, SETUP, PLAY）
            pattern = r'^([A-Z]+)\s+'
        elif protocol_name.upper() == "HTTP":
            # HTTP: 提取方法（GET, POST, PUT 等）
            pattern = r'^([A-Z]+)\s+'
        elif protocol_name.upper() == "FTP":
            # FTP: 提取命令（USER, PASS, LIST 等）
            pattern = r'^([A-Z]+)\s+'
        elif protocol_name.upper() == "SMTP":
            # SMTP: 提取命令（HELO, MAIL, RCPT 等）
            pattern = r'^([A-Z]+)\s+'
        elif protocol_name.upper() == "SIP":
            # SIP: 提取方法（INVITE, REGISTER, BYE 等）
            pattern = r'^([A-Z]+)\s+'
        else:
            # 通用模式：提取每行开头的单词（大写字母）
            pattern = r'^([A-Z]+)\s+'
        
        lines = seed_content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            match = re.match(pattern, line)
            if match:
                msg_type = match.group(1).upper()
                message_types.add(msg_type)
        
        return message_types
    
    def extract_message_types_from_seeds(self, seed_files: List[Path], 
                                        protocol_name: str) -> Set[str]:
        """
        从多个种子文件中提取所有已使用的消息类型
        
        Args:
            seed_files: 种子文件路径列表
            protocol_name: 协议名称
            
        Returns:
            所有已使用的消息类型集合
        """
        all_message_types = set()
        
        # 限制检查的种子数量
        seed_files = seed_files[:self.MAX_ENRICHMENT_CORPUS_SIZE]
        
        for seed_file in seed_files:
            try:
                with open(seed_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    message_types = self.extract_message_types_from_seed(
                        content, protocol_name
                    )
                    all_message_types.update(message_types)
            except Exception as e:
                print(f"读取种子文件 {seed_file} 失败: {e}")
        
        return all_message_types
    
    def construct_enrichment_prompt(self, sequence: str, 
                                   missing_message_types: List[str],
                                   protocol_name: str = "FTP") -> str:
        """
        构建种子丰富化的提示词（chat 格式）
        
        Args:
            sequence: 原始种子序列
            missing_message_types: 缺失的消息类型列表
            protocol_name: 协议名称（用于生成协议特定的示例）
            
        Returns:
            Chat 格式的 messages（JSON 字符串）
        """
        # 限制缺失消息类型的数量
        missing_types = missing_message_types[:self.MAX_ENRICHMENT_MESSAGE_TYPES]
        missing_types_str = ", ".join(missing_types)
        
        # 根据协议生成示例
        if protocol_name.upper() == "FTP":
            example = (
                "Example of correct FTP client request format:\n"
                "USER ubuntu\n"
                "PASS ubuntu\n"
                "LIST\n"
                "RETR test.txt\n"
                "QUIT\n\n"
                "Each line must be: COMMAND [parameter]\n"
                "Do NOT use 'COMMAND' or 'RESPONSE' keywords. Use actual FTP commands directly."
            )
        elif protocol_name.upper() == "RTSP":
            example = (
                "Example of correct RTSP client request format:\n"
                "DESCRIBE rtsp://example.com/test RTSP/1.0\n"
                "CSeq: 1\n"
                "User-Agent: TestClient\n\n"
                "SETUP rtsp://example.com/test/track1 RTSP/1.0\n"
                "CSeq: 2\n"
                "Transport: RTP/AVP;unicast;client_port=5000-5001\n\n"
            )
        else:
            example = (
                "Each line must be a valid protocol command with optional parameters, "
                "separated by spaces. Do NOT use placeholder keywords like 'COMMAND' or 'RESPONSE'."
            )
        
        # 计算允许的序列长度（考虑 token 限制）
        template_base = (
            "你是一个网络安全专家，你的任务是将缺失的命令全部正确地插入到原来的消息序列当中，同时保留原始序列的基础内容。你只做增量式的插入，同时插入命令的未知要满足协议的状态机。 \n\n"
            "{example}\n\n"
            "Original sequence:\n"
            "{sequence}\n\n"
            "Task: Add the following missing request types: {missing_types}\n\n"
            "STRICT REQUIREMENTS:\n"
            "1. Return ONLY the complete modified sequence, nothing else\n"
            "2. Use the EXACT same format as the original sequence\n"
            "3. Each line must be a valid protocol command (e.g., 'USER ubuntu', not 'COMMAND USER')\n"
            "4. Do NOT include any explanatory text, comments, or descriptions\n"
            "5. Do NOT include server responses or status codes\n"
            "6. Do NOT use placeholder keywords like 'COMMAND', 'RESPONSE', 'PARAMETER'\n"
            "7. Maintain the exact formatting style of the original sequence\n\n"
            "Return the modified sequence now:"
        )
        
        template_base_len = len(template_base.replace("{sequence}", "").replace("{missing_types}", "").replace("{example}", ""))
        missing_types_len = len(missing_types_str)
        example_len = len(example)
        estimated_template_tokens = (template_base_len + missing_types_len + example_len) // 4
        
        # 保留安全边距
        allowed_sequence_chars = (self.MAX_TOKENS - estimated_template_tokens - 150) * 4
        
        if len(sequence) > allowed_sequence_chars:
            sequence = sequence[:allowed_sequence_chars]
        
        user_message = template_base.format(
            example=example,
            sequence=sequence,
            missing_types=missing_types_str
        )
        
        messages = [
            {
                "role": "system", 
                "content": "You are a network protocol expert. 你需要在原来的消息序列的基础上正确地插入缺失的命令. You NEVER use placeholder keywords. You return ONLY the raw protocol commands in the exact format requested."
            },
            {"role": "user", "content": user_message}
        ]
        
        return json.dumps(messages)
    
    def extract_sequence_from_response(self, response: str, protocol_name: str) -> str:
        """
        从 LLM 响应中提取纯种子序列，去除解释性文字
        
        Args:
            response: LLM 的原始响应
            protocol_name: 协议名称（用于识别序列格式）
            
        Returns:
            提取出的纯种子序列
        """
        # 移除开头的空白字符
        response = response.lstrip('\n \t\r')
        
        # 尝试找到代码块（``` 包围的内容）
        code_block_pattern = r'```(?:\w+)?\n(.*?)```'
        match = re.search(code_block_pattern, response, re.DOTALL)
        if match:
            response = match.group(1).strip()
        
        # 定义协议命令模式
        protocol_patterns = {
            "FTP": r'^(USER|PASS|LIST|RETR|STOR|DELE|MKD|RMD|CWD|PWD|QUIT|PASV|PORT|TYPE|MODE|STRU|NLST|SIZE|MDTM|RNFR|RNTO|APPE|REST|ABOR|SYST|STAT|HELP|NOOP|SITE|STOU|ALLO|ACCT|SMNT|REIN|CDUP)\s',
            "RTSP": r'^(DESCRIBE|SETUP|PLAY|PAUSE|TEARDOWN|OPTIONS|ANNOUNCE|RECORD|REDIRECT|GET_PARAMETER|SET_PARAMETER)\s',
            "HTTP": r'^(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH|TRACE|CONNECT)\s',
            "SMTP": r'^(HELO|EHLO|MAIL|RCPT|DATA|RSET|VRFY|EXPN|HELP|NOOP|QUIT)\s',
            "SIP": r'^(INVITE|ACK|BYE|CANCEL|REGISTER|OPTIONS|INFO|PRACK|UPDATE|REFER|SUBSCRIBE|NOTIFY|PUBLISH|MESSAGE)\s',
        }
        
        protocol_pattern = protocol_patterns.get(protocol_name.upper(), r'^[A-Z]+\s')
        
        lines = response.split('\n')
        sequence_lines = []
        found_start = False
        skip_patterns = [
            r'^\d+\.?\s+',  # 编号列表 "1. ", "2. "
            r'^\*\s+',      # 无序列表 "* "
            r'^-\s+',       # 无序列表 "- "
            r'^\*\*',       # Markdown 粗体 "**"
            r'^#+\s+',      # Markdown 标题 "# "
        ]
        
        for line in lines:
            original_line = line
            line = line.strip()
            
            if not line:
                # 保留空行（可能是协议消息分隔符），但只在找到序列后保留
                if found_start:
                    sequence_lines.append('')
                continue
            
            # 跳过明显的解释性文字
            should_skip = False
            for pattern in skip_patterns:
                if re.match(pattern, line):
                    should_skip = True
                    break
            
            if should_skip:
                continue
            
            # 跳过包含常见解释性关键词的行
            explanation_keywords = [
                'here', 'the', 'so', 'in', 'this', 'note', 'important',
                'following', 'above', 'below', 'sequence', 'command',
                'response', 'status', 'code', 'ftp status', 'server'
            ]
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in explanation_keywords) and not re.match(protocol_pattern, line):
                # 但如果这行本身就是协议命令，不要跳过
                if not re.match(r'^[A-Z]+\s', line):
                    continue
            
            # 严格过滤：跳过包含占位符关键词的行
            placeholder_keywords = ['command', 'response', 'parameter', 'value', 'placeholder']
            if any(keyword in line_lower for keyword in placeholder_keywords):
                # 检查是否是纯占位符格式（如 "COMMAND USER" 或 "RESPONSE ubuntu"）
                if re.match(r'^(COMMAND|RESPONSE|PARAMETER|VALUE)\s', line, re.IGNORECASE):
                    continue
                # 如果整行只是占位符关键词，跳过
                if line_lower.strip() in placeholder_keywords:
                    continue
            
            # 检查是否是协议命令
            if re.match(protocol_pattern, line) or found_start:
                found_start = True
                
                # 对于 FTP，跳过服务器响应（以3位数字开头的行）
                if protocol_name.upper() == "FTP":
                    if re.match(r'^\d{3}\s', line):
                        continue
                    # 跳过包含状态码说明的行
                    if re.search(r'\d{3}\s+[A-Z]', line) and not re.match(r'^[A-Z]+\s', line):
                        continue
                
                # 移除行首可能的编号或标记
                line = re.sub(r'^\d+\.?\s*', '', line)
                line = re.sub(r'^[-*]\s*', '', line)
                
                sequence_lines.append(line)
        
        # 如果找到了序列，返回它
        if sequence_lines:
            result = '\n'.join(sequence_lines).strip()
            # 移除末尾可能的解释性文字（连续两个换行后的内容）
            result = re.sub(r'\n\n+.*$', '', result, flags=re.DOTALL)
            # 清理多余的空行
            result = re.sub(r'\n{3,}', '\n\n', result)
            return result
        
        # 如果没找到，返回清理后的原始响应（移除明显的解释性开头）
        cleaned = response.strip()
        # 移除常见的解释性开头
        cleaned = re.sub(r'^(Here|The|So|In|This|Note|Important|Following|Above|Below).*?\n+', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        
        # 最后验证：如果包含明显的占位符，尝试修复或返回空
        if re.search(r'\b(COMMAND|RESPONSE|PARAMETER|VALUE)\s+', cleaned, re.IGNORECASE):
            # 尝试修复：将 "COMMAND USER" 转换为 "USER"
            cleaned = re.sub(r'COMMAND\s+', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'RESPONSE\s+', '', cleaned, flags=re.IGNORECASE)
            # 如果修复后仍然有问题，返回空
            if re.search(r'\b(COMMAND|RESPONSE|PARAMETER|VALUE)\b', cleaned, re.IGNORECASE):
                return ""
        
        return cleaned
    
    def validate_enriched_sequence(self, sequence: str, protocol_name: str, original_sequence: str) -> bool:
        """
        验证丰富后的序列是否符合格式要求
        
        Args:
            sequence: 丰富后的序列
            protocol_name: 协议名称
            original_sequence: 原始序列（用于格式对比）
            
        Returns:
            如果序列有效返回 True，否则返回 False
        """
        if not sequence or not sequence.strip():
            return False
        
        # 检查是否包含占位符关键词
        placeholder_pattern = r'\b(COMMAND|RESPONSE|PARAMETER|VALUE|PLACEHOLDER)\s+'
        if re.search(placeholder_pattern, sequence, re.IGNORECASE):
            return False
        
        # 检查是否包含明显的解释性文字
        explanation_patterns = [
            r'^(Here|The|So|In|This|Note|Important|Following|Above|Below)',
            r'example',
            r'format:',
            r'sequence:',
        ]
        for pattern in explanation_patterns:
            if re.search(pattern, sequence, re.IGNORECASE | re.MULTILINE):
                return False
        
        # 对于 FTP，验证命令格式
        if protocol_name.upper() == "FTP":
            lines = sequence.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # FTP 命令应该是：COMMAND [parameter]
                # 不应该包含 "COMMAND" 或 "RESPONSE" 关键词
                if re.match(r'^(COMMAND|RESPONSE)\s+', line, re.IGNORECASE):
                    return False
                # 应该以 FTP 命令开头
                if not re.match(r'^[A-Z]+\s', line):
                    # 允许空行，但不允许其他格式
                    continue
        
        return True
    
    def normalize_line_endings(self, content: str) -> str:
        """
        规范化换行符格式，确保使用 \r\n（Windows 风格）
        并确保文件末尾有换行符
        
        Args:
            content: 原始内容
            
        Returns:
            规范化后的内容（使用 \r\n 换行，末尾有换行符）
        """
        if not content:
            return '\r\n'
        
        # 统一处理：先将所有可能的换行符组合标准化为 \n
        # 处理 \r\n (Windows)
        content = content.replace('\r\n', '\n')
        # 处理单独的 \r (Mac)
        content = content.replace('\r', '\n')
        
        # 移除末尾的空白字符（但保留换行符的逻辑）
        content = content.rstrip(' \t')
        
        # 现在所有换行都是 \n，统一转换为 \r\n
        content = content.replace('\n', '\r\n')
        
        # 确保文件末尾有换行符
        if not content.endswith('\r\n'):
            content += '\r\n'
        
        return content
    
    def generate_message_type_combinations(self, missing_types: List[str], 
                                           max_size: int = None) -> List[List[str]]:
        """
        生成缺失消息类型的所有组合
        
        例如：如果 max_size=3，缺失类型为 [GET, POST, PUT]，
        则生成所有长度为1、2、3的组合：
        - 长度1: [GET], [POST], [PUT]
        - 长度2: [GET, POST], [GET, PUT], [POST, PUT]
        - 长度3: [GET, POST, PUT]
        
        Args:
            missing_types: 缺失的消息类型列表
            max_size: 每个组合的最大大小（默认使用 MAX_ENRICHMENT_MESSAGE_TYPES）
            
        Returns:
            组合列表，每个组合是一个消息类型列表
        """
        from itertools import combinations
        
        if not missing_types:
            return []
        
        max_size = max_size if max_size is not None else self.MAX_ENRICHMENT_MESSAGE_TYPES
        combinations_list = []
        
        # 生成所有可能的组合（大小从1到max_size）
        for size in range(1, min(max_size + 1, len(missing_types) + 1)):
            for combo in combinations(missing_types, size):
                combinations_list.append(list(combo))
        
        return combinations_list
    
    def select_diverse_combinations(self, all_combinations: List[List[str]], 
                                    num_select: int) -> List[List[str]]:
        """
        从所有组合中随机选择不同的组合
        
        例如：如果 all_combinations 包含 [GET], [POST], [PUT], [GET, POST], [GET, PUT], [POST, PUT], [GET, POST, PUT]
        且 num_select=3，则随机选择3个不同的组合，如：[POST], [GET, PUT], [GET, POST, PUT]
        
        Args:
            all_combinations: 所有可能的组合列表（长度1到max_enrichment_message_types的所有组合）
            num_select: 需要选择的数量（对应 max_enriched_per_file）
            
        Returns:
            随机选中的组合列表，每个组合用于生成一个变体种子
        """
        if not all_combinations:
            return []
        
        # 如果组合数量少于需要的数量，直接返回所有组合（随机打乱）
        if len(all_combinations) <= num_select:
            selected = all_combinations.copy()
            random.shuffle(selected)
            return selected
        
        # 随机选择 num_select 个不同的组合
        selected = random.sample(all_combinations, num_select)
        
        return selected
    
    def enrich_sequence(self, sequence: str, 
                       missing_message_types: List[str],
                       protocol_name: str = "FTP") -> Optional[str]:
        """
        丰富种子序列：在合适位置添加缺失的消息类型
        
        Args:
            sequence: 原始种子序列
            missing_message_types: 缺失的消息类型列表
            protocol_name: 协议名称（用于后处理）
            
        Returns:
            丰富后的序列，失败返回 None
        """
        if not missing_message_types:
            return sequence
        
        prompt = self.construct_enrichment_prompt(sequence, missing_message_types, protocol_name)
        
        response = self.chat_with_llm(
            prompt,
            model_type="chat",
            temperature=self.TEMPERATURE,
            max_retries=self.ENRICHMENT_RETRIES
        )
        
        if response:
            # 从响应中提取纯种子序列
            cleaned_response = self.extract_sequence_from_response(response, protocol_name)
            
            # 验证序列质量
            if cleaned_response and self.validate_enriched_sequence(cleaned_response, protocol_name, sequence):
                return cleaned_response
            else:
                print(f"  警告: 生成的序列格式不符合要求，已拒绝")
                return None
        
        return None
    
    def enrich_seed_file(self, seed_file: Path, protocol_name: str,
                       all_message_types: Set[str],
                       used_message_types: Set[str]) -> Optional[str]:
        """
        丰富单个种子文件
        
        Args:
            seed_file: 种子文件路径
            protocol_name: 协议名称
            all_message_types: 协议的所有消息类型
            used_message_types: 已使用的消息类型
            
        Returns:
            丰富后的种子内容，失败返回 None
        """
        # 计算缺失的消息类型
        missing_types = list(all_message_types - used_message_types)
        
        if not missing_types:
            print(f"种子 {seed_file} 已包含所有消息类型，无需丰富")
            return None
        
        # 读取原始种子内容
        try:
            with open(seed_file, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
        except Exception as e:
            print(f"读取种子文件失败: {e}")
            return None
        
        # 丰富序列
        enriched_content = self.enrich_sequence(original_content, missing_types, protocol_name)
        
        return enriched_content
    
    def enrich_seeds(self, seed_dir: str, protocol_name: str,
                    output_dir: Optional[str] = None,
                    max_enriched_per_file: Optional[int] = None) -> Dict[str, str]:
        """
        丰富种子目录中的所有种子
        
        Args:
            seed_dir: 种子目录路径
            protocol_name: 协议名称
            output_dir: 输出目录，如果为 None 则在原目录创建 enriched 子目录
            max_enriched_per_file: 每个原始种子最多生成的丰富种子数量（默认使用 MAX_ENRICHED_SEEDS_PER_FILE）
            
        Returns:
            字典：{原始文件路径: 丰富后的内容列表}
        """
        seed_dir = Path(seed_dir)
        if not seed_dir.exists():
            raise ValueError(f"种子目录不存在: {seed_dir}")
        
        # 获取所有种子文件
        seed_files = list(seed_dir.glob("*"))
        seed_files = [f for f in seed_files if f.is_file()]
        
        if not seed_files:
            print(f"种子目录 {seed_dir} 中没有找到种子文件")
            return {}
        
        print(f"找到 {len(seed_files)} 个种子文件")
        
        # 步骤1: 获取协议的所有消息类型
        print("\n步骤1: 获取协议的所有消息类型...")
        all_message_types = self.get_protocol_message_types(protocol_name)
        
        if not all_message_types:
            print("无法获取协议消息类型，终止")
            return {}
        
        # 步骤2: 从现有种子中提取已使用的消息类型
        print("\n步骤2: 分析现有种子中的消息类型...")
        used_message_types = self.extract_message_types_from_seeds(
            seed_files, protocol_name
        )
        print(f"已使用的消息类型: {sorted(used_message_types)}")
        
        # 步骤3: 计算缺失的消息类型
        missing_types = all_message_types - used_message_types
        print(f"\n缺失的消息类型: {sorted(missing_types)}")
        
        if not missing_types:
            print("所有消息类型都已覆盖，无需丰富")
            return {}
        
        # 步骤4: 准备输出目录
        max_per_file = max_enriched_per_file if max_enriched_per_file is not None else self.MAX_ENRICHED_SEEDS_PER_FILE
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"输出目录: {output_dir}")
            print(f"每个种子最多生成: {max_per_file} 个变体")
        
        # 步骤5: 丰富种子（每丰富一个立即保存）
        max_per_file = max_enriched_per_file if max_enriched_per_file is not None else self.MAX_ENRICHED_SEEDS_PER_FILE
        print(f"\n步骤3: 开始丰富种子（每次最多添加 {self.MAX_ENRICHMENT_MESSAGE_TYPES} 个消息类型，每个种子最多生成 {max_per_file} 个变体）...")
        enriched_seeds = {}
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for idx, seed_file in enumerate(seed_files, 1):
            print(f"\n[{idx}/{len(seed_files)}] 处理种子: {seed_file.name}")
            
            # 从当前种子中提取消息类型
            try:
                with open(seed_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    seed_used_types = self.extract_message_types_from_seed(
                        content, protocol_name
                    )
            except Exception as e:
                print(f"  ✗ 读取种子文件失败: {e}")
                fail_count += 1
                continue
            
            # 计算当前种子缺失的类型
            seed_missing_types = list(missing_types - seed_used_types)
            
            if not seed_missing_types:
                print(f"  ⊘ 种子已包含所有缺失类型，跳过")
                skip_count += 1
                continue
            
            # 生成缺失消息类型的所有可能组合
            all_combinations = self.generate_message_type_combinations(seed_missing_types)
            
            if not all_combinations:
                print(f"  ⊘ 无法生成消息类型组合，跳过")
                skip_count += 1
                continue
            
            # 随机选择多样化的组合
            selected_combinations = self.select_diverse_combinations(all_combinations, max_per_file)
            
            print(f"  种子缺失的消息类型: {sorted(seed_missing_types)}")
            print(f"  将生成 {len(selected_combinations)} 个不同的消息类型组合变体")
            
            # 为每个种子生成多个变体（每个变体使用不同的消息类型组合）
            file_success_count = 0
            for variant_idx, combo in enumerate(selected_combinations):
                if variant_idx > 0:
                    print(f"  生成变体 {variant_idx + 1}/{len(selected_combinations)} (组合: {', '.join(combo)})...")
                else:
                    print(f"  生成变体 1/{len(selected_combinations)} (组合: {', '.join(combo)})...")
                
                # 使用当前组合丰富种子
                enriched_content = self.enrich_sequence(content, combo, protocol_name)
                
                if enriched_content:
                    # 立即保存到输出目录
                    if output_dir:
                        original_file = Path(seed_file)
                        if len(selected_combinations) > 1:
                            # 多个变体时，添加序号
                            base_name = original_file.stem
                            extension = original_file.suffix
                            output_file = output_dir / f"enriched_{base_name}_{variant_idx + 1}{extension}"
                        else:
                            # 单个变体时，使用原文件名
                            output_file = output_dir / f"enriched_{original_file.name}"
                        
                        try:
                            # 规范化换行符格式为 \r\n
                            normalized_content = self.normalize_line_endings(enriched_content)
                            
                            with open(output_file, 'wb') as f:
                                # 使用二进制模式写入，确保 \r\n 正确保存
                                f.write(normalized_content.encode('utf-8'))
                            
                            if len(selected_combinations) > 1:
                                print(f"  ✓ 成功生成变体 {variant_idx + 1} 并保存: {output_file.name}")
                            else:
                                print(f"  ✓ 成功丰富并保存: {output_file.name}")
                            
                            file_success_count += 1
                            success_count += 1
                            
                            # 保存到返回字典
                            key = f"{seed_file}_v{variant_idx + 1}" if len(selected_combinations) > 1 else str(seed_file)
                            enriched_seeds[key] = enriched_content
                            
                        except Exception as e:
                            print(f"  ✗ 保存失败: {e}")
                            fail_count += 1
                    else:
                        print(f"  ✓ 成功丰富种子（未指定输出目录，未保存）")
                        file_success_count += 1
                        success_count += 1
                        key = f"{seed_file}_v{variant_idx + 1}" if len(selected_combinations) > 1 else str(seed_file)
                        enriched_seeds[key] = enriched_content
                else:
                    if variant_idx == 0:
                        print(f"  ✗ 丰富种子失败 (组合: {', '.join(combo)})")
                    else:
                        print(f"  ✗ 生成变体 {variant_idx + 1} 失败 (组合: {', '.join(combo)})")
                    # 继续尝试下一个组合，而不是直接break
            
            if file_success_count == 0:
                fail_count += 1
        
        # 输出统计信息
        print("\n" + "=" * 60)
        print("处理完成统计:")
        print(f"  成功: {success_count} 个")
        print(f"  跳过: {skip_count} 个")
        print(f"  失败: {fail_count} 个")
        print(f"  总计: {len(seed_files)} 个")
        if output_dir and success_count > 0:
            print(f"  输出目录: {output_dir}")
        print("=" * 60)
        
        return enriched_seeds

