# WSL 环境下使用 Ollama 配置指南

## 问题说明

在 WSL2 环境中，如果 Ollama 运行在 Windows 宿主机上，需要特殊配置才能从 WSL 访问。

## 解决方案

### 方案 1: 使用 localhost（推荐，WSL2 自动转发）

WSL2 会自动将 `localhost` 转发到 Windows 主机，所以最简单的方式是：

```yaml
use_local: true
api_url: http://localhost:11434/v1  # 或留空
model: qwen2.5:7b
```

**优点**：无需额外配置，WSL2 自动处理

### 方案 2: 配置 Ollama 监听所有接口

如果方案 1 不工作，需要配置 Ollama 在 Windows 上监听所有网络接口：

1. **停止 Ollama 服务**（如果正在运行）

2. **设置环境变量**（在 Windows PowerShell 中）：
   ```powershell
   $env:OLLAMA_HOST="0.0.0.0:11434"
   ollama serve
   ```

3. **或者创建启动脚本** `start_ollama.bat`：
   ```batch
   @echo off
   set OLLAMA_HOST=0.0.0.0:11434
   ollama serve
   ```

4. **配置 Windows 防火墙**：
   - 打开 Windows 防火墙设置
   - 允许端口 11434 的入站连接
   - 或者在首次运行时选择"允许访问"

5. **在 WSL 中使用 Windows IP**：
   ```yaml
   use_local: true
   api_url: http://192.168.31.1:11434/v1  # 替换为实际的 Windows IP
   model: qwen2.5:7b
   ```

### 方案 3: 使用 WSL hostname

在某些情况下，可以使用 Windows 主机名：

```yaml
use_local: true
api_url: http://$(hostname).local:11434/v1  # 需要替换为实际主机名
model: qwen2.5:7b
```

## 故障排除

### 问题 1: 502 Bad Gateway

**原因**：Ollama 只监听 localhost，WSL 无法访问

**解决**：
1. 确保使用 `localhost` 而不是 Windows IP（WSL2 会自动转发）
2. 或者配置 Ollama 监听 `0.0.0.0:11434`

### 问题 2: Connection Refused

**原因**：Windows 防火墙阻止了连接

**解决**：
1. 在 Windows 防火墙中允许端口 11434
2. 或者使用 `localhost`（通常不需要防火墙规则）

### 问题 3: 无法检测到 Windows IP

**原因**：WSL 网络配置问题

**解决**：
1. 检查 WSL 版本：`wsl --version`
2. 确保使用 WSL2：`wsl --set-version <distro> 2`
3. 使用 `localhost` 而不是 IP 地址

## 验证连接

运行测试脚本：

```bash
python test_local_model.py
```

如果成功，会看到：
```
✓ 所有测试通过！本地模型配置正确。
```

## 推荐配置

对于 WSL2 环境，推荐配置：

```yaml
use_local: true
api_url: http://localhost:11434/v1  # WSL2 自动转发
# 或者直接留空，程序会使用默认值
model: qwen2.5:7b
```

这样配置最简单，无需额外设置。

