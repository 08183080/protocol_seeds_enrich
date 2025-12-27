import asyncio
import traceback
from mcp import ClientSession
from mcp.client.sse import sse_client

# DeepWiki 官方 MCP 服务器地址 (SSE 协议)
DEEPWIKI_SERVER_URL = "https://mcp.deepwiki.com/sse"

async def call_deepwiki(repo_url, question):
    """
    通过 MCP 协议调用 DeepWiki 的 ask_question 工具
    """
    try:
        print(f"正在连接到 DeepWiki MCP 服务器: {DEEPWIKI_SERVER_URL}")
        async with sse_client(DEEPWIKI_SERVER_URL) as (read_stream, write_stream):
            print("SSE 连接已建立")
            async with ClientSession(read_stream, write_stream) as session:
                print("ClientSession 已创建")
                # 1. 初始化会话
                print("正在初始化会话...")
                await session.initialize()
                print("会话初始化完成")
                
                # 2. 调用 ask_question 工具
                # DeepWiki 官方提供的工具包括: ask_question, read_wiki_contents, read_wiki_structure
                # 注意：API 期望的参数名是 repoName，不是 repo_url
                arguments = {
                    "repoName": repo_url,
                    "question": question
                }
                
                print(f"正在向 DeepWiki 提问关于 {repo_url} 的问题...")
                result = await session.call_tool("ask_question", arguments)
                print("工具调用完成")
                
                # 3. 输出结果
                return result.content
    except Exception as e:
        print(f"在 call_deepwiki 中捕获到异常: {type(e).__name__}: {e}")
        print(f"详细错误信息:\n{traceback.format_exc()}")
        raise

async def main():
    # 示例：提问关于开源 AI 项目的问题
    # 注意：目标仓库需要在 deepwiki.com 上已被索引（公开仓库通常会自动索引或手动访问一次 deepwiki.com/user/repo）
    repo = "proftpd/proftpd"
    q0 = "该协议实现支持的所有命令，请以JSON形式返回。"
    q = "该协议实现所有的硬编码常量。"

    try:
        response = await call_deepwiki(repo, q)
        for item in response:
            if item.type == 'text':
                print("\n=== AI 回答内容 ===\n")
                print(item.text)
    except Exception as e:
        print(f"\n调用失败: {type(e).__name__}: {e}")
        print(f"\n完整错误堆栈:\n{traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())