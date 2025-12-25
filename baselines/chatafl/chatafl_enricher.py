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
    
    def __init__(self, api_key: Optional[str] = None, 
                 model: str = "gpt-3.5-turbo-instruct",
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
        
    def chat_with_llm(self, prompt: str, model_type: str = "instruct", 
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
        构建获取协议消息类型的提示词
        
        Args:
            protocol_name: 协议名称（如 "RTSP", "FTP"）
            
        Returns:
            提示词字符串
        """
        prompt = (
            f"In the {protocol_name} protocol, the message types are: \n\n"
            f"Desired format:\n"
            f"<comma_separated_list_of_states_in_uppercase_and_without_whitespaces>"
        )
        return prompt
    
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
        获取协议的所有消息类型（使用一致性检查）
        
        Args:
            protocol_name: 协议名称
            
        Returns:
            消息类型集合
        """
        prompt = self.construct_prompt_for_message_types(protocol_name)
        message_type_counter = Counter()
        
        print(f"提示词: {prompt}")
        print(f"开始查询协议消息类型（将查询 {self.CONFIDENT_TIMES} 次以确保一致性）...")
        
        # 多次查询以确保一致性
        successful_queries = 0
        for i in range(self.CONFIDENT_TIMES):
            print(f"  查询 {i+1}/{self.CONFIDENT_TIMES}...", end=" ")
            answer = self.chat_with_llm(
                prompt, 
                model_type="instruct", 
                temperature=0.5,
                max_retries=self.MESSAGE_TYPE_RETRIES
            )
            
            if answer is None:
                print("失败（未收到响应）")
                continue
            
            print(f"成功")
            successful_queries += 1
            
            # 显示原始响应（用于调试）
            if i == 0:  # 只显示第一次的完整响应
                print(f"  原始响应: {answer[:200]}..." if len(answer) > 200 else f"  原始响应: {answer}")
            
            # 格式化答案
            answer = self.format_string(answer)
            
            # 解析逗号分隔的消息类型
            message_types = [self.format_string(mt.strip()) 
                           for mt in answer.split(',')]
            
            # 过滤空字符串并转换为大写
            parsed_types = [mt.upper() for mt in message_types if mt]
            
            if parsed_types:
                print(f"  解析到的消息类型: {parsed_types}")
                for mt in parsed_types:
                    message_type_counter[mt] += 1
            else:
                print(f"  警告: 无法从响应中解析消息类型")
                print(f"  响应内容: {answer[:100]}...")
        
        print(f"\n成功查询次数: {successful_queries}/{self.CONFIDENT_TIMES}")
        print(f"消息类型统计: {dict(message_type_counter)}")
        
        # 只保留出现次数 >= 0.5 * CONFIDENT_TIMES 的消息类型
        threshold = 0.5 * self.CONFIDENT_TIMES
        result = {mt for mt, count in message_type_counter.items() 
                 if count >= threshold}
        
        print(f"协议 {protocol_name} 的消息类型（出现次数 >= {threshold}）: {sorted(result)}")
        
        if not result:
            print("\n警告: 未能获取到协议消息类型！")
            print("可能的原因:")
            print("  1. LLM 调用失败或超时")
            print("  2. LLM 返回的格式不符合预期")
            print("  3. 本地模型未正确响应")
            print("\n建议:")
            print("  1. 检查本地模型服务是否正常运行")
            print("  2. 尝试手动测试模型连接: python test_local_model.py")
            print("  3. 检查模型是否能正确理解提示词")
        
        return result
    
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
                                   missing_message_types: List[str]) -> str:
        """
        构建种子丰富化的提示词
        
        Args:
            sequence: 原始种子序列
            missing_message_types: 缺失的消息类型列表
            
        Returns:
            提示词字符串
        """
        # 限制缺失消息类型的数量
        missing_types = missing_message_types[:self.MAX_ENRICHMENT_MESSAGE_TYPES]
        missing_types_str = ", ".join(missing_types)
        
        # 转义序列内容（使用 JSON 转义，然后移除外层引号）
        # 这与原始 C 代码中的 json_object_to_json_string 行为一致
        sequence_escaped = json.dumps(sequence)
        sequence_escaped = sequence_escaped[1:-1]  # 移除外层引号
        
        # 计算允许的序列长度（考虑 token 限制）
        # 原始代码: allowed_tokens = (MAX_TOKENS - strlen(prompt_template) - missing_fields_len)
        prompt_template_base = (
            "The following is one sequence of client requests:\n"
            "{sequence}\n\n"
            "Please add the {missing_types} client requests in the proper locations.\n"
            "IMPORTANT: Return ONLY the modified sequence of client requests, without any explanations, comments, or additional text.\n"
            "Do not include status codes, server responses, or any descriptive text.\n"
            "Return only the raw client request sequence:\n"
        )
        
        # 估算 token 长度（简单估算：1 token ≈ 4 字符）
        template_base_len = len(prompt_template_base.replace("{sequence}", "").replace("{missing_types}", ""))
        missing_types_len = len(missing_types_str)
        estimated_template_tokens = (template_base_len + missing_types_len) // 4
        
        # 保留安全边距
        allowed_sequence_chars = (self.MAX_TOKENS - estimated_template_tokens - 50) * 4
        
        if len(sequence_escaped) > allowed_sequence_chars:
            sequence_escaped = sequence_escaped[:allowed_sequence_chars]
        
        prompt = prompt_template_base.format(
            sequence=sequence_escaped,
            missing_types=missing_types_str
        )
        
        return prompt
    
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
        return cleaned
    
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
        
        prompt = self.construct_enrichment_prompt(sequence, missing_message_types)
        
        response = self.chat_with_llm(
            prompt,
            model_type="instruct",
            temperature=0.5,
            max_retries=self.ENRICHMENT_RETRIES
        )
        
        if response:
            # 从响应中提取纯种子序列
            cleaned_response = self.extract_sequence_from_response(response, protocol_name)
            return cleaned_response
        
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
                    output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        丰富种子目录中的所有种子
        
        Args:
            seed_dir: 种子目录路径
            protocol_name: 协议名称
            output_dir: 输出目录，如果为 None 则在原目录创建 enriched 子目录
            
        Returns:
            字典：{原始文件路径: 丰富后的内容}
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
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"输出目录: {output_dir}")
        
        # 步骤5: 丰富种子（每丰富一个立即保存）
        print(f"\n步骤3: 开始丰富种子（每次最多添加 {self.MAX_ENRICHMENT_MESSAGE_TYPES} 个消息类型）...")
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
            
            # 丰富种子
            enriched_content = self.enrich_sequence(content, seed_missing_types, protocol_name)
            
            if enriched_content:
                enriched_seeds[str(seed_file)] = enriched_content
                
                # 立即保存到输出目录
                if output_dir:
                    original_file = Path(seed_file)
                    output_file = output_dir / f"enriched_{original_file.name}"
                    
                    try:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(enriched_content)
                        print(f"  ✓ 成功丰富并保存: {output_file.name}")
                        success_count += 1
                    except Exception as e:
                        print(f"  ✗ 保存失败: {e}")
                        fail_count += 1
                else:
                    print(f"  ✓ 成功丰富种子（未指定输出目录，未保存）")
                    success_count += 1
            else:
                print(f"  ✗ 丰富种子失败")
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

