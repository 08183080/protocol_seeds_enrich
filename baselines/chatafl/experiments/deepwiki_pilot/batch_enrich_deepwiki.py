import sys
import os
import json
import time
from pathlib import Path

# 确保可以导入基础类 chatafl_enricher.py (根据你的实际路径调整)
sys.path.append(os.path.abspath("../../")) 
from chatafl_enricher import ChatAFLEnricher

# --- 这里保留你定义的类 ---
class ProSeedsDeepEnricher(ChatAFLEnricher):
    def __init__(self, knowledge_path, **kwargs):
        super().__init__(**kwargs)
        with open(knowledge_path, 'r', encoding='utf-8') as f:
            self.kb = json.load(f)
        print(f"[+] 成功加载 {self.kb['target']} 的深度知识库")

    def _get_relevant_logic(self, missing_types):
        relevant_info = ""
        for cmd_entry in self.kb.get('custom_commands', []):
            cmd_name = cmd_entry['command_name']
            if any(m in cmd_name for m in missing_types) or cmd_name in missing_types:
                relevant_info += f"- 命令: {cmd_name}\n"
                relevant_info += f"  处理模块: {cmd_entry['handling_module']}\n"
                relevant_info += f"  关键逻辑: {cmd_entry['critical_logic']}\n\n"
        return relevant_info

    def construct_enrichment_prompt(self, sequence, missing_message_types, protocol_name="FTP"):
        base_prompt_json = super().construct_enrichment_prompt(sequence, missing_message_types, protocol_name)
        messages = json.loads(base_prompt_json)
        relevant_logic = self._get_relevant_logic(missing_message_types)
        impl_overview = self.kb.get('implementation_details', "")

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
        messages[-1]["content"] += "\n" + knowledge_injection
        return json.dumps(messages)

    def run_enrichment_task(self, seed_file, missing_cmds):
        with open(seed_file, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()
        prompt = self.construct_enrichment_prompt(original_content, missing_cmds, "FTP")
        response = self.chat_with_llm(prompt, model_type="chat", temperature=0.7) # 稍微提高随机性
        if response:
            result = self.extract_sequence_from_response(response, "FTP")
            if result and self.validate_enriched_sequence(result, "FTP", original_content):
                return result
        return None

# --- 批量处理主逻辑 ---
def main():
    # 1. 配置路径
    KNOWLEDGE_PATH = "mined_knowledge.json"
    INPUT_SEEDS_DIR = Path("/home/apple/ProSeedsBench/seeds/FTP/ProFTPD/in-proftpd")
    OUTPUT_DIR = Path("/home/apple/ProSeedsBench/enriched_seeds/FTP/ProFTPD/deepwiki_batch_v1")
    
    # 2. 如果输出目录不存在则创建
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 3. 初始化增强器
    enricher = ProSeedsDeepEnricher(
        knowledge_path=KNOWLEDGE_PATH,
        use_local=True,
        api_url="http://localhost:11434/v1",
        model="qwen2.5:7b" 
    )

    # 4. 决定要针对哪些挖掘出来的命令进行增强
    # 我们从 KB 中提取前 10 个自定义命令作为目标，或者你可以手动指定
    with open(KNOWLEDGE_PATH, 'r') as f:
        kb_data = json.load(f)
    all_custom_cmds = [c['command_name'] for c in kb_data.get('custom_commands', [])]
    
    # 将命令分成几组，以便生成不同侧重点的种子
    target_groups = [
        ["SITE COPY", "SITE CPTO", "SITE QUOTA"], # 侧重文件复制逻辑
        ["MLSD", "MLST", "MFF", "MFMT"],          # 侧重文件事实扩展
        ["MDTM", "SIZE", "HOST"]                 # 侧重核心功能扩展
    ]

    # 5. 遍历输入目录下的所有 .raw 文件
    seed_files = list(INPUT_SEEDS_DIR.glob("*.raw"))
    print(f"[*] 发现 {len(seed_files)} 个原始种子，准备开始批量处理...")

    stats = {"success": 0, "fail": 0}
    start_time = time.time()

    for seed_path in seed_files:
        print(f"\n[>] 处理种子: {seed_path.name}")
        
        # 每个种子尝试用不同的命令组生成变体
        for i, cmd_group in enumerate(target_groups):
            print(f"    - 尝试增强变体 {i+1} (目标: {cmd_group})")
            
            try:
                enriched_seq = enricher.run_enrichment_task(str(seed_path), cmd_group)
                
                if enriched_seq:
                    # 构造输出文件名: dw_原名_varX.raw
                    output_filename = f"dw_{seed_path.stem}_v{i+1}.raw"
                    save_path = OUTPUT_DIR / output_filename
                    
                    with open(save_path, "wb") as f:
                        f.write(enricher.normalize_line_endings(enriched_seq).encode('utf-8'))
                    
                    print(f"      [OK] 已保存至: {output_filename}")
                    stats["success"] += 1
                else:
                    print(f"      [!] 增强失败 (LLM 未返回有效序列)")
                    stats["fail"] += 1
            except Exception as e:
                print(f"      [ERROR] 处理时出错: {e}")
                stats["fail"] += 1

    # 6. 打印总结
    end_time = time.time()
    duration = end_time - start_time
    print("\n" + "="*50)
    print(f"批量增强任务完成！")
    print(f"总计耗时: {duration:.2f} 秒")
    print(f"成功生成: {stats['success']} 个种子")
    print(f"失败数量: {stats['fail']} 个")
    print(f"保存目录: {OUTPUT_DIR}")
    print("="*50)

if __name__ == "__main__":
    main()