# ChatAFL 配置文件使用指南

## 快速开始

### 1. 创建配置文件

```bash
cp config.yaml.example config.yaml
```

### 2. 编辑配置文件

使用任何文本编辑器打开 `config.yaml`，修改以下必需字段：

```yaml
protocol: RTSP          # 改为你的协议名称
seed_dir: ../seeds/RTSP # 改为你的种子目录路径
```

### 3. 运行

```bash
python run.py
```

就这么简单！

## 配置文件详解

### 基本配置

```yaml
# 必需配置
protocol: RTSP                    # 协议名称
seed_dir: ../seeds/RTSP          # 种子目录路径

# 可选配置
output_dir: ./enriched_seeds      # 输出目录（默认: seed_dir/enriched）
api_key: sk-xxx                   # API key（建议用环境变量）
model: gpt-3.5-turbo-instruct    # 使用的模型
```

### 高级配置

如果需要调整算法参数，可以使用 `advanced` 部分：

```yaml
advanced:
  confident_times: 3                    # 一致性检查次数（默认: 3）
  max_enrichment_message_types: 2       # 每次最多添加的类型数（默认: 2）
  max_enrichment_corpus_size: 10        # 最多检查的种子数（默认: 10）
  enrichment_retries: 5                 # 丰富操作重试次数（默认: 5）
  message_type_retries: 5               # 消息类型获取重试次数（默认: 5）
```

## 配置示例

### 示例 1: RTSP 协议

```yaml
protocol: RTSP
seed_dir: ../seeds/RTSP
output_dir: ./enriched_seeds/RTSP
```

### 示例 2: FTP 协议（带高级配置）

```yaml
protocol: FTP
seed_dir: ../seeds/FTP
output_dir: ./enriched_seeds/FTP

advanced:
  max_enrichment_message_types: 3  # 每次添加 3 个类型
  max_enrichment_corpus_size: 20   # 检查更多种子
```

### 示例 3: 多个协议配置

为不同协议创建不同的配置文件：

```bash
# RTSP 配置
cp config.yaml.example config_rtsp.yaml
# 编辑 config_rtsp.yaml

# FTP 配置
cp config.yaml.example config_ftp.yaml
# 编辑 config_ftp.yaml

# 运行
python run.py config_rtsp.yaml
python run.py config_ftp.yaml
```

## 环境变量配置

建议使用环境变量设置 API key，而不是直接写在配置文件中：

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

然后在配置文件中不设置 `api_key` 字段，或设置为空：

```yaml
# api_key:  # 留空，从环境变量读取
```

## 常见问题

### Q: 配置文件路径错误

**A**: 使用绝对路径：

```yaml
seed_dir: /home/user/project/seeds/RTSP
```

### Q: 如何查看当前使用的配置？

**A**: 运行时会显示配置信息：

```bash
python run.py
# 会显示：
# 配置信息:
#   协议: RTSP
#   种子目录: ../seeds/RTSP
#   输出目录: ./enriched_seeds/RTSP
#   模型: gpt-3.5-turbo-instruct
```

### Q: 配置文件格式错误

**A**: 确保 YAML 格式正确：
- 使用空格缩进（不要用 Tab）
- 冒号后要有空格
- 字符串不需要引号（除非包含特殊字符）

### Q: 如何验证配置文件？

**A**: 运行脚本会自动验证，如果有错误会显示具体信息。

## 最佳实践

1. **使用环境变量存储 API key**：更安全
2. **为不同协议创建不同配置文件**：便于管理
3. **使用相对路径**：便于在不同机器上运行
4. **保存配置文件到版本控制**：但不要包含 API key

## 配置文件模板

完整模板请参考 `config.yaml.example`。

