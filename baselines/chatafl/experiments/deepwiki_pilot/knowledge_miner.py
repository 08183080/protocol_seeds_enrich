import asyncio
import json
import os
from mcp import ClientSession
from mcp.client.sse import sse_client

DEEPWIKI_SERVER_URL = "https://mcp.deepwiki.com/sse"

class KnowledgeMiner:
    def __init__(self, repo_name):
        self.repo_name = repo_name # 例如 "proftpd/proftpd"

    async def mine(self):
        print(f"[*] 正在为仓库 {self.repo_name} 启动自动化知识挖掘...")
        
        async with sse_client(DEEPWIKI_SERVER_URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                # 构造一个高度结构化的 Prompt，强制要求 JSON 输出
                mining_query = f"""
                Analyze the protocol implementation in {self.repo_name}.
                Identify all custom or implementation-specific commands (e.g., SITE extensions for FTP).
                For each command, identify:
                1. The command name.
                2. The internal module handling it.
                3. A brief description of critical logic (e.g., buffer handling, path validation).
                
                Return the results strictly in the following JSON format:
                {{
                    "target": "Project Name",
                    "custom_commands": ["CMD1", "CMD2"],
                    "implementation_details": "Consolidated summary of critical logic paths"
                }}
                """
                
                arguments = {"repoName": self.repo_name, "question": mining_query}
                result = await session.call_tool("ask_question", arguments)
                
                # 提取并解析 JSON
                for item in result.content:
                    if item.type == 'text':
                        return self._parse_json_from_text(item.text)
        return None

    def _parse_json_from_text(self, text):
        try:
            # 找到文本中的第一个 { 和最后一个 }
            start = text.find('{')
            end = text.rfind('}') + 1
            return json.loads(text[start:end])
        except:
            print("[-] JSON 解析失败，响应内容不符合格式。")
            return None

# 测试运行
if __name__ == "__main__":
    miner = KnowledgeMiner("proftpd/proftpd")
    kb = asyncio.run(miner.mine())
    if kb:
        with open("mined_knowledge.json", "w") as f:
            json.dump(kb, f, indent=2)
            print("[+] 挖掘完成，知识库已保存至 mined_knowledge.json")