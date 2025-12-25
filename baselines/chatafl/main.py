#!/usr/bin/env python3
"""
ChatAFL 种子丰富方法 - 主程序示例

使用方法:
    python main.py --protocol RTSP --seed_dir ../seeds/RTSP --output_dir ./enriched_seeds
"""

import argparse
import sys
from pathlib import Path
from chatafl_enricher import ChatAFLEnricher


def main():
    parser = argparse.ArgumentParser(
        description="ChatAFL 种子丰富方法复现",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 丰富 RTSP 协议的种子
  python main.py --protocol RTSP --seed_dir ../seeds/RTSP --output_dir ./enriched_seeds
  
  # 使用自定义 API key
  python main.py --protocol FTP --seed_dir ../seeds/FTP --api_key your_api_key
        """
    )
    
    parser.add_argument(
        "--protocol",
        type=str,
        required=True,
        help="协议名称 (如 RTSP, FTP, HTTP, SMTP, SIP)"
    )
    
    parser.add_argument(
        "--seed_dir",
        type=str,
        required=True,
        help="种子文件目录路径"
    )
    
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="输出目录路径（默认为 seed_dir/enriched）"
    )
    
    parser.add_argument(
        "--api_key",
        type=str,
        default=None,
        help="OpenAI API key（也可通过环境变量 OPENAI_API_KEY 设置）"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-3.5-turbo-instruct",
        help="使用的模型（默认: gpt-3.5-turbo-instruct）"
    )
    
    parser.add_argument(
        "--api_url",
        type=str,
        default=None,
        help="自定义 API URL（用于本地模型或其他兼容 API）"
    )
    
    parser.add_argument(
        "--use_local",
        action="store_true",
        help="使用本地模型（如 Ollama）"
    )
    
    args = parser.parse_args()
    
    # 设置输出目录
    if args.output_dir is None:
        seed_dir = Path(args.seed_dir)
        output_dir = seed_dir / "enriched"
    else:
        output_dir = Path(args.output_dir)
    
    # 创建丰富器
    try:
        enricher = ChatAFLEnricher(
            api_key=args.api_key, 
            model=args.model,
            api_url=args.api_url,
            use_local=args.use_local
        )
    except ValueError as e:
        print(f"错误: {e}")
        if not args.use_local:
            print("\n请设置 API key:")
            print("  1. 通过命令行参数: --api_key YOUR_KEY")
            print("  2. 通过环境变量: export OPENAI_API_KEY=YOUR_KEY")
        else:
            print("\n使用本地模型时，请确保:")
            print("  1. Ollama 服务正在运行: ollama serve")
            print("  2. 已下载模型: ollama pull <model_name>")
            print("  3. API URL 正确: --api_url http://localhost:11434/v1")
        sys.exit(1)
    
    # 执行种子丰富
    print(f"开始丰富 {args.protocol} 协议的种子...")
    print(f"种子目录: {args.seed_dir}")
    print(f"输出目录: {output_dir}")
    print("-" * 60)
    
    try:
        enriched_seeds = enricher.enrich_seeds(
            seed_dir=args.seed_dir,
            protocol_name=args.protocol,
            output_dir=str(output_dir)
        )
        
        print("\n" + "=" * 60)
        print(f"完成！成功丰富了 {len(enriched_seeds)} 个种子")
        print(f"输出目录: {output_dir}")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

