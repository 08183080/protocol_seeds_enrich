#!/usr/bin/env python3
"""
测试本地模型连接

用于验证本地模型（如 Ollama）配置是否正确
支持 WSL 环境自动检测宿主机 IP
"""

import sys
from chatafl_enricher import ChatAFLEnricher, get_wsl_host_ip


def test_local_model():
    """测试本地模型连接"""
    print("=" * 60)
    print("测试本地模型连接")
    print("=" * 60)
    
    # 在 WSL2 中，直接使用 localhost（会自动转发到 Windows）
    # 如果需要使用 Windows IP，可以取消下面的注释
    # host_ip = get_wsl_host_ip()
    # api_url = f"http://{host_ip}:11434/v1"
    api_url = "http://localhost:11434/v1"  # WSL2 自动转发到 Windows
    
    # 配置（可以从配置文件读取或手动设置）
    model = "qwen2.5:7b"  # 修改为你的模型名称
    
    print(f"\n配置:")
    print(f"  使用 localhost（WSL2 会自动转发到 Windows）")
    print(f"  API URL: {api_url}")
    print(f"  模型: {model}")
    print("-" * 60)
    
    try:
        # 创建丰富器（会自动处理 WSL 环境）
        enricher = ChatAFLEnricher(
            api_key="ollama",
            model=model,
            api_url=api_url,
            use_local=True
        )
        
        print(f"\n实际使用的 API URL: {enricher.api_url}")
        print("-" * 60)
        
        print("\n测试 1: 简单对话")
        print("-" * 60)
        response = enricher.chat_with_llm(
            "Hello, how are you? Please respond briefly.",
            model_type="instruct",
            temperature=0.5
        )
        
        if response:
            print(f"✓ 成功！响应: {response[:100]}...")
        else:
            print("✗ 失败：未收到响应")
            return False
        
        print("\n测试 2: 协议消息类型查询")
        print("-" * 60)
        prompt = enricher.construct_prompt_for_message_types("FTP")
        print(f"提示词: {prompt[:100]}...")
        response = enricher.chat_with_llm(
            prompt,
            model_type="instruct",
            temperature=0.5
        )
        
        if response:
            print(f"✓ 成功！响应: {response[:200]}...")
        else:
            print("✗ 失败：未收到响应")
            return False
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！本地模型配置正确。")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        print("\n请检查:")
        print("  1. Ollama 服务是否运行: ollama serve")
        print("  2. 模型是否已下载: ollama pull " + model)
        print("  3. API URL 是否正确: " + api_url)
        print("  4. WSL 宿主机 IP 是否正确（如果 Ollama 运行在 Windows 上）")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_local_model()
    sys.exit(0 if success else 1)
