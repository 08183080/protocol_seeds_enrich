#!/usr/bin/env python3
"""
ChatAFL 使用示例

演示如何使用 ChatAFLEnricher 进行种子丰富
"""

import os
from pathlib import Path
from chatafl_enricher import ChatAFLEnricher


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("示例 1: 基本使用")
    print("=" * 60)
    
    # 检查 API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("错误: 请设置环境变量 OPENAI_API_KEY")
        return
    
    # 创建丰富器
    enricher = ChatAFLEnricher(api_key=api_key)
    
    # 获取协议消息类型
    print("\n获取 RTSP 协议的消息类型...")
    message_types = enricher.get_protocol_message_types("RTSP")
    print(f"消息类型: {sorted(message_types)}")
    
    # 从种子中提取消息类型
    print("\n从种子中提取消息类型...")
    seed_file = Path("../seeds/RTSP/seed1.txt")  # 示例路径
    if seed_file.exists():
        with open(seed_file, 'r') as f:
            content = f.read()
        used_types = enricher.extract_message_types_from_seed(content, "RTSP")
        print(f"已使用的消息类型: {sorted(used_types)}")
    else:
        print(f"种子文件不存在: {seed_file}")


def example_enrich_single_seed():
    """丰富单个种子示例"""
    print("\n" + "=" * 60)
    print("示例 2: 丰富单个种子")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("错误: 请设置环境变量 OPENAI_API_KEY")
        return
    
    enricher = ChatAFLEnricher(api_key=api_key)
    
    # 示例种子内容
    original_sequence = """DESCRIBE rtsp://example.com/test RTSP/1.0
CSeq: 1
User-Agent: TestClient

SETUP rtsp://example.com/test/track1 RTSP/1.0
CSeq: 2
Transport: RTP/AVP;unicast;client_port=5000-5001
"""
    
    # 缺失的消息类型
    missing_types = ["PLAY", "TEARDOWN"]
    
    print(f"\n原始序列:\n{original_sequence}")
    print(f"\n缺失的消息类型: {missing_types}")
    
    # 丰富序列
    enriched = enricher.enrich_sequence(original_sequence, missing_types)
    
    if enriched:
        print(f"\n丰富后的序列:\n{enriched}")
    else:
        print("\n丰富失败")


def example_batch_enrichment():
    """批量丰富示例"""
    print("\n" + "=" * 60)
    print("示例 3: 批量丰富种子")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("错误: 请设置环境变量 OPENAI_API_KEY")
        return
    
    enricher = ChatAFLEnricher(api_key=api_key)
    
    # 假设种子目录存在
    seed_dir = "../seeds/RTSP"
    output_dir = "./enriched_seeds"
    
    if not Path(seed_dir).exists():
        print(f"种子目录不存在: {seed_dir}")
        print("请使用实际的种子目录路径")
        return
    
    print(f"\n种子目录: {seed_dir}")
    print(f"输出目录: {output_dir}")
    
    # 执行批量丰富
    enriched_seeds = enricher.enrich_seeds(
        seed_dir=seed_dir,
        protocol_name="RTSP",
        output_dir=output_dir
    )
    
    print(f"\n成功丰富了 {len(enriched_seeds)} 个种子")


if __name__ == "__main__":
    print("ChatAFL 使用示例\n")
    
    # 运行示例
    example_basic_usage()
    # example_enrich_single_seed()  # 取消注释以运行
    # example_batch_enrichment()    # 取消注释以运行
    
    print("\n" + "=" * 60)
    print("提示: 取消注释其他示例函数以查看完整功能")
    print("=" * 60)

