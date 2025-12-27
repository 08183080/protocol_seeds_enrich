import sys
import os
import json
from pathlib import Path

# 确保可以导入基础类 chatafl_enricher.py
sys.path.append(os.path.abspath("../../")) 
from chatafl_enricher import ChatAFLEnricher

class ProSeedsDeepEnricher(ChatAFLEnricher):
    def __init__(self, knowledge_path, **kwargs):
        super().__init__(**kwargs)
        with open(knowledge_path, 'r', encoding='utf-8') as f:
            self.kb = json.load(f)
        print(f"[+] 成功加载 {self.kb['target']} 的深度知识库")

    def _get_relevant_logic(self, missing_types):
        """根据缺失命令筛选对应的深度逻辑"""
        relevant_info = ""
        for cmd_entry in self.kb.get('custom_commands', []):
            cmd_name = cmd_entry['command_name']
            # 匹配命令（考虑 SITE XXX 这种子命令）
            if any(m in cmd_name for m in missing_types) or cmd_name in missing_types:
                relevant_info += f"- 命令: {cmd_name}\n"
                relevant_info += f"  处理模块: {cmd_entry['handling_module']}\n"
                relevant_info += f"  关键逻辑: {cmd_entry['critical_logic']}\n\n"
        return relevant_info

    def construct_enrichment_prompt(self, sequence, missing_message_types, protocol_name="FTP"):
        """覆盖基类方法，注入 DeepWiki 深度知识"""
        # 1. 获取基础消息结构
        base_prompt_json = super().construct_enrichment_prompt(sequence, missing_message_types, protocol_name)
        messages = json.loads(base_prompt_json)
        
        # 2. 提取当前任务相关的深度逻辑
        relevant_logic = self._get_relevant_logic(missing_message_types)
        impl_overview = self.kb.get('implementation_details', "")

        # 3. 构造增强指令
        knowledge_injection = f"""
### 内部实现深度知识 (DeepWiki Insight) ###
【架构总览】: {impl_overview}

【当前命令的实现细节】:
{relevant_logic if relevant_logic else "遵循标准 RFC 规范，但注意 ProFTPD 的模块化处理特性。"}

### 增强生成要求 (Advanced Requirements) ###
1. 针对上述“关键逻辑”中提到的路径校验、缓冲区处理或函数调用，构造具有“压力”的参数。
2. 如果涉及 'mod_quotatab' 或 'mod_site'，尝试生成包含特殊字符、超长路径或逻辑边界值的序列。
3. 确保生成的命令参数能够触发该模块的深层分支。
"""
        # 将知识注入到用户最后一条消息中
        messages[-1]["content"] += "\n" + knowledge_injection
        
        return json.dumps(messages)

    def run_enrichment_task(self, seed_file, missing_cmds):
        """执行丰富化任务"""
        print(f"[*] 正在深度增强种子: {seed_file}")
        with open(seed_file, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()
            
        prompt = self.construct_enrichment_prompt(original_content, missing_cmds, "FTP")
        
        # 调用 LLM
        response = self.chat_with_llm(prompt, model_type="chat", temperature=0.6)
        
        if response:
            result = self.extract_sequence_from_response(response, "FTP")
            if result and self.validate_enriched_sequence(result, "FTP", original_content):
                return result
        return None

if __name__ == "__main__":
    # 配置你的模型环境
    enricher = ProSeedsDeepEnricher(
        knowledge_path="mined_knowledge.json", # 你刚才跑出来的结果
        use_local=True,
        api_url="http://localhost:11434/v1", # 修改为你的实际 API
        model="qwen2.5:7b" 
    )

    # 示例测试：针对 mod_quotatab 模块的 SITE COPY 命令进行针对性丰富
    test_seed = "/home/apple/ProSeedsBench/seeds/FTP/ProFTPD/in-proftpd/seed_1.raw"
    target_missing = ["SITE COPY", "SITE CPTO", "MDTM"]
    
    enriched_seq = enricher.run_enrichment_task(test_seed, target_missing)
    
    if enriched_seq:
        output_file = "enriched_with_logic.raw"
        with open(output_file, "wb") as f:
            f.write(enricher.normalize_line_endings(enriched_seq).encode('utf-8'))
        print(f"\n[+] 增强成功！种子已保存至: {output_file}")
        print("--- 生成的序列片段 ---")
        print("\n".join(enriched_seq.splitlines()[-5:])) # 显示末尾几行
    else:
        print("[-] 丰富化失败，请检查 LLM 输出或 Prompt 配置。")