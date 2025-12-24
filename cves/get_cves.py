import requests
import csv
import time
import sys

# --- 配置参数 ---
# 搜索关键词：替换为你想要查询的产品或协议名称，例如 'proftpd'
SEARCH_KEYWORD = "Exim"
# NVD API 基础 URL
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
# 输出文件名
OUTPUT_FILENAME = f"{SEARCH_KEYWORD}_cve.csv"
# NVD API 的每页最大限制
RESULTS_PER_PAGE = 500

def format_references(references):
    """
    将 References 列表格式化为易于 CSV 阅读的字符串
    """
    if not references:
        return "N/A"
    
    # 格式示例：[TAG: URL] | [TAG: URL]
    ref_list = []
    for ref in references:
        url = ref.get('url', 'N/A')
        tags = ", ".join(ref.get('tags', [])) if ref.get('tags') else "None"
        ref_list.append(f"[{tags}: {url}]")
    
    # 使用换行符或分号分隔，方便在一个单元格内查看
    return "\n".join(ref_list)


def format_cpes(configurations):
    """
    提取受影响产品的 CPE (Common Platform Enumeration) 列表
    """
    cpe_list = []
    if not configurations:
        return "N/A"

    for config in configurations:
        nodes = config.get('nodes', [])
        for node in nodes:
            cpe_matches = node.get('cpeMatch', [])
            for match in cpe_matches:
                if match.get('vulnerable') and 'criteria' in match:
                    cpe_list.append(match['criteria'])
    
    # 将所有受影响的 CPE 链接用换行符分隔
    return "\n".join(cpe_list)


def fetch_cves_from_nvd(keyword):
    """
    从 NVD API 批量获取 CVE 数据
    """
    all_cves = []
    start_index = 0
    total_results = None

    print(f"--- 🚀 正在查询 NVD API 中关于 '{keyword}' 的 CVE 记录... ---")

    while total_results is None or start_index < total_results:
        params = {
            'keywordSearch': keyword,
            'resultsPerPage': RESULTS_PER_PAGE,
            'startIndex': start_index
        }
        
        try:
            response = requests.get(NVD_API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"❌ API 请求失败，可能受到速率限制: {e}", file=sys.stderr)
            break
        
        vulnerabilities = data.get('vulnerabilities', [])
        total_results = data.get('totalResults', 0)

        if not vulnerabilities:
            print("--- ✅ 没有更多结果了。 ---")
            break

        for item in vulnerabilities:
            cve = item.get('cve', {})
            
            # --- 1. 基本信息 ---
            cve_id = cve.get('id', 'N/A')
            
            # 获取英文描述
            description = next(
                (desc['value'] for desc in cve.get('descriptions', []) if desc.get('lang') == 'en'), 
                'No English Description'
            )
            
            # --- 2. 严重性与评分 ---
            metrics = cve.get('metrics', {})
            base_score = 'N/A'
            severity = 'N/A'
            vector = 'N/A'
            
            # 优先 V3.1 评分
            if 'cvssMetricV31' in metrics and metrics['cvssMetricV31']:
                cvss_data = metrics['cvssMetricV31'][0]['cvssData']
                base_score = cvss_data.get('baseScore', 'N/A')
                severity = cvss_data.get('baseSeverity', 'N/A')
                vector = cvss_data.get('vectorString', 'N/A')

            # --- 3. 复杂字段提取 ---
            references_str = format_references(cve.get('references', []))
            cpes_str = format_cpes(cve.get('configurations', []))
            
            # 存储提取的 CVE 记录
            all_cves.append({
                'CVE_ID': cve_id,
                'Severity': severity,
                'Base_Score': base_score,
                'CVSS_Vector': vector,
                'Published_Date': cve.get('published', 'N/A').split('T')[0],
                'Last_Modified': cve.get('lastModified', 'N/A').split('T')[0],
                'Description': description,
                # 'References': references_str,
                # 'Vulnerable_CPEs': cpes_str
            })

        print(f"--- 📥 已下载 {len(all_cves)} / {total_results} 条记录... ---")

        # 准备下一页
        start_index += len(vulnerabilities)
        
        # 遵守 NVD 速率限制，等待 1 秒
        time.sleep(1) 

    return all_cves

def export_to_csv(data, filename):
    """
    将提取的 CVE 数据写入 CSV 文件
    """
    if not data:
        print("没有数据可导出。")
        return

    # CSV 文件的完整标题行/字段名
    fieldnames = [
        'CVE_ID', 'Severity', 'Base_Score', 'CVSS_Vector', 
        'Published_Date', 'Last_Modified', 'Description', 
        # 'References', 'Vulnerable_CPEs'
    ]

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            
            writer.writeheader()
            writer.writerows(data)
        
        print(f"\n--- 🎉 成功导出 {len(data)} 条完整的 CVE 记录到文件: {filename} ---")
        
    except IOError as e:
        print(f"❌ 导出文件失败: {e}", file=sys.stderr)


# --- 主执行逻辑 ---
if __name__ == "__main__":
    cve_data = fetch_cves_from_nvd(SEARCH_KEYWORD)
    export_to_csv(cve_data, OUTPUT_FILENAME)