#!/usr/bin/env python3
"""
ChatAFL 种子丰富方法 - 基于 YAML 配置的运行脚本

使用方法:
    python run.py config.yaml
    或
    python run.py  # 使用默认配置文件 config.yaml
"""

import argparse
import sys
import os
from pathlib import Path
import yaml
from chatafl_enricher import ChatAFLEnricher


def load_config(config_path: str) -> dict:
    """
    加载 YAML 配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def validate_config(config: dict) -> None:
    """
    验证配置文件的必需字段
    
    Args:
        config: 配置字典
        
    Raises:
        ValueError: 如果配置无效
    """
    required_fields = ['protocol', 'seed_dir']
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"配置文件缺少必需字段: {field}")
    
    # 验证路径
    seed_dir = Path(config['seed_dir'])
    if not seed_dir.exists():
        raise ValueError(f"种子目录不存在: {seed_dir}")


def run_from_config(config_path: str = "config.yaml") -> None:
    """
    从配置文件运行种子丰富流程
    
    Args:
        config_path: 配置文件路径
    """
    print("=" * 60)
    print("ChatAFL 种子丰富方法")
    print("=" * 60)
    
    # 加载配置
    print(f"\n加载配置文件: {config_path}")
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"错误: 无法加载配置文件: {e}")
        sys.exit(1)
    
    # 验证配置
    try:
        validate_config(config)
    except ValueError as e:
        print(f"错误: 配置验证失败: {e}")
        sys.exit(1)
    
    # 提取配置项
    protocol = config['protocol']
    seed_dir = config['seed_dir']
    output_dir = config.get('output_dir', None)
    model = config.get('model', 'gpt-3.5-turbo-instruct')
    
    # API 配置
    use_local = config.get('use_local', False)
    api_url = config.get('api_url', None)
    api_key = config.get('api_key', None)
    
    # 如果使用本地模型，api_key 可以为空
    if not use_local:
        api_key = api_key or os.getenv('OPENAI_API_KEY')
    else:
        # 对于本地模型，如果 api_url 包含 localhost，会在 ChatAFLEnricher 中自动检测 WSL 宿主机 IP
        pass
    
    # 高级配置（可选）
    advanced_config = config.get('advanced', {})
    
    # 设置输出目录
    if output_dir is None:
        seed_dir_path = Path(seed_dir)
        output_dir = str(seed_dir_path / "enriched")
    
    # 显示配置信息
    print(f"\n配置信息:")
    print(f"  协议: {protocol}")
    print(f"  种子目录: {seed_dir}")
    print(f"  输出目录: {output_dir}")
    print(f"  模型: {model}")
    print(f"  使用本地模型: {use_local}")
    if api_url:
        print(f"  API URL: {api_url}")
    if advanced_config:
        print(f"  高级配置: {advanced_config}")
    print("-" * 60)
    
    # 创建丰富器
    try:
        enricher = ChatAFLEnricher(
            api_key=api_key, 
            model=model,
            api_url=api_url,
            use_local=use_local
        )
        
        # 应用高级配置（如果提供）
        max_enriched_per_file = None
        if advanced_config:
            if 'confident_times' in advanced_config:
                enricher.CONFIDENT_TIMES = advanced_config['confident_times']
            if 'max_enrichment_message_types' in advanced_config:
                enricher.MAX_ENRICHMENT_MESSAGE_TYPES = advanced_config['max_enrichment_message_types']
            if 'max_enrichment_corpus_size' in advanced_config:
                enricher.MAX_ENRICHMENT_CORPUS_SIZE = advanced_config['max_enrichment_corpus_size']
            if 'enrichment_retries' in advanced_config:
                enricher.ENRICHMENT_RETRIES = advanced_config['enrichment_retries']
            if 'message_type_retries' in advanced_config:
                enricher.MESSAGE_TYPE_RETRIES = advanced_config['message_type_retries']
            if 'max_enriched_per_file' in advanced_config:
                max_enriched_per_file = advanced_config['max_enriched_per_file']
                enricher.MAX_ENRICHED_SEEDS_PER_FILE = max_enriched_per_file
            
            print(f"已应用高级配置")
            print(f"  CONFIDENT_TIMES: {enricher.CONFIDENT_TIMES}")
            print(f"  MAX_ENRICHMENT_MESSAGE_TYPES: {enricher.MAX_ENRICHMENT_MESSAGE_TYPES}")
            print(f"  MAX_ENRICHMENT_CORPUS_SIZE: {enricher.MAX_ENRICHMENT_CORPUS_SIZE}")
            if max_enriched_per_file is not None:
                print(f"  MAX_ENRICHED_SEEDS_PER_FILE: {max_enriched_per_file}")
            print("-" * 60)
        
    except ValueError as e:
        print(f"错误: {e}")
        print("\n请设置 OpenAI API key:")
        print("  1. 在配置文件中设置: api_key: your-key")
        print("  2. 通过环境变量: export OPENAI_API_KEY=your-key")
        sys.exit(1)
    
    # 执行种子丰富
    print(f"\n开始丰富 {protocol} 协议的种子...\n")
    
    try:
        enriched_seeds = enricher.enrich_seeds(
            seed_dir=seed_dir,
            protocol_name=protocol,
            output_dir=output_dir,
            max_enriched_per_file=max_enriched_per_file
        )
        
        print("\n" + "=" * 60)
        print(f"完成！成功丰富了 {len(enriched_seeds)} 个种子")
        print(f"输出目录: {output_dir}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ChatAFL 种子丰富方法 - 基于 YAML 配置",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认配置文件 config.yaml
  python run.py
  
  # 使用自定义配置文件
  python run.py my_config.yaml
  
  # 查看示例配置文件
  cat config.yaml.example
        """
    )
    
    parser.add_argument(
        "config",
        type=str,
        nargs='?',
        default="config.yaml",
        help="YAML 配置文件路径（默认: config.yaml）"
    )
    
    args = parser.parse_args()
    
    run_from_config(args.config)


if __name__ == "__main__":
    main()

