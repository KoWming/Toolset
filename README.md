# Toolset

自用工具、脚本和一些收集的奇奇怪怪的东西！

## 📁 工具脚本说明

<details>
<summary><strong>🐳 Docker-all-install.py</strong> - 跨平台Docker和Docker Compose自动安装脚本</summary>

**功能描述**: 跨平台Docker和Docker Compose自动安装脚本

**主要特性**:
- 支持Linux、Windows、macOS系统
- 自动检测Docker和Docker Compose版本
- 智能安装缺失的组件
- 多语言支持（中文/英文）
- 自动权限检测和配置
- 安装完成后自动启动服务

**使用方法**:
```bash
# 检查并安装Docker
python3 Docker-all-install.py

# 仅检查状态
python3 Docker-all-install.py --status

# 指定语言
python3 Docker-all-install.py --lang en
```

**适用场景**: 新服务器环境配置、Docker环境快速部署、开发环境搭建

</details>

<details>
<summary><strong>🎯 朱雀自动转盘抽奖及统计-1.4.js</strong> - 朱雀PT站点自动转盘抽奖脚本</summary>

**功能描述**: 朱雀PT站点自动转盘抽奖脚本（Tampermonkey用户脚本）

**主要特性**:
- 自动获取CSRF Token和Cookie
- 智能抽奖策略和进度显示
- 抽奖结果统计和分析
- 一键出售道具功能
- 自动回收和上传量管理
- 可配置的出售预设

**使用方法**:
1. 安装Tampermonkey浏览器扩展
2. 导入此脚本到Tampermonkey
3. 访问朱雀PT站点即可使用

**功能模块**:
- 自动抽奖控制
- 奖品价值统计
- 一键出售设置
- 上传量管理
- 收益分析报告

**适用场景**: 朱雀PT站点用户、自动化抽奖、道具管理

</details>

<details>
<summary><strong>🔐 LuckySSLtoSafeLine.py</strong> - Lucky证书自动更新同步工具</summary>

**功能描述**: Lucky证书自动更新同步工具，将Lucky申请的SSL证书自动同步到雷池中进行更新

**主要特性**:
- 监控Lucky证书更新状态，证书变化后触发脚本
- 自动读取Lucky生成的证书文件（.crt和.key）
- 通过雷池API自动更新证书
- 智能域名匹配和证书文件查找
- 多平台消息推送通知
- 完整的操作日志记录
- 支持重试机制和错误处理

**支持的消息推送渠道**:
- 企业微信机器人
- Server酱
- 钉钉机器人
- 飞书机器人
- 企业微信应用
- 自定义Webhook

**使用方法**:

1. **配置Lucky证书映射**
   - 在Lucky SSL/TLS证书中打开编辑证书
   - 启用证书映射功能
   - 自定义映射路径：`/data/lucky/*证书名*`
   - 证书变化后触发脚本：`python3 /data/lucky/*证书名*/LuckySSLtoSafeLine.py`

2. **配置脚本参数**
   - 在脚本内设置雷池API地址：`API_BASE_URL`
   - 配置雷池API Token：`API_TOKEN`
   - 设置消息推送渠道配置（WebHook、企业微信、钉钉等）

3. **上传脚本文件**
   - 使用Lucky的FileBrowser或其他工具
   - 将脚本上传到自定义映射路径：`/data/lucky/*证书名*/`

4. **自动触发执行**
   - 配置完成后，证书有变化会自动触发脚本执行
   - 脚本自动读取证书文件并同步到雷池

**配置示例**:
```bash
# 脚本路径示例
/data/lucky/example.com/LuckySSLtoSafeLine.py

# 测试触发命令示例
python3 /data/lucky/example.com/LuckySSLtoSafeLine.py
```

**配置说明**:
- 需要在脚本内配置雷池管理端API地址和Token
- 支持多种消息推送渠道配置（企业微信、钉钉、飞书等）
- 证书映射路径格式：`/data/lucky/*证书名*`
- 支持多种证书类型和域名模式
- 脚本会自动在映射路径中查找证书文件（.crt和.key）

**适用场景**: Lucky证书自动化管理、SSL证书自动更新、雷池证书同步、运维自动化

**工作流程**:
1. Lucky申请/更新SSL证书
2. 证书文件保存到映射路径
3. Lucky自动触发脚本执行
4. 脚本读取证书文件并上传到雷池
5. 发送操作结果通知

**官方文档**: [Lucky SSL模块文档](https://lucky666.cn/docs/modules/ssl)

</details>

<details>
<summary><strong>📡 webhook_notify_docker.sh</strong> - subs-check项目执行结果统计通知脚本</summary>

**功能描述**: subs-check项目执行结果统计通知脚本，用于Docker环境下的节点测速完成后的WebHook通知推送

**主要特性**:
- 自动解析subs-check执行日志和统计信息
- 智能提取节点数量、去重数量、成功节点数等关键数据
- 自动计算订阅链接数量（本地+远程）
- 支持流量消耗统计（GB单位）
- 兼容Alpine Linux环境，使用wget发送请求
- 卡片风格的通知内容，信息清晰易读

**统计信息包含**:
- 订阅链接数量统计
- 获取节点数量（去重前）
- 去重后节点数量
- 成功节点数量
- 测试总消耗流量
- 测速完成时间

**使用方法**:

1. **配置WebHook地址**
   - 在脚本中修改 `NOTIFY_HOST` 变量
   - 设置为您的自定义WebHook通知地址

2. **部署到subs-check项目**
   - 将脚本放到Docker项目的config目录下
   - 路径：`./config/webhook_notify_docker.sh`

3. **配置回调脚本**
   - 打开项目配置文件界面
   - 修改 `callback-script: "/app/config/webhook_notify_docker.sh"`

4. **自动执行**
   - 项目运行完成后自动触发脚本
   - 推送统计详细信息到自定义WebHook

**配置示例**:
```bash
# 脚本中的WebHook配置
NOTIFY_HOST="http://your-server:port/api/webhook?key=your_key"

# 配置文件中的回调设置
callback-script: "/app/config/webhook_notify_docker.sh"
```

**环境变量支持**:
- `SUCCESS_COUNT`: 成功节点数量
- `NODES_TOTAL`: 获取节点数量
- `NODES_DEDUP`: 去重后节点数量
- `TOTAL_TRAFFIC_GB`: 测试总消耗流量
- `SUBS_COUNT_OVERRIDE`: 订阅链接数量覆盖值

**适用场景**: subs-check项目Docker部署、节点测速结果通知

**相关项目**: [subs-check](https://github.com/beck-8/subs-check)

</details>

## 🚀 快速开始

1. **克隆仓库**
   ```bash
   git clone https://github.com/KoWming/Toolset.git
   cd Toolset
   ```

2. **选择需要的工具**
   - Docker环境配置 → 使用 `Docker-all-install.py`
   - PT站点自动化 → 使用 `朱雀自动转盘抽奖及统计-1.4.js`
   - 证书管理迁移 → 使用 `LuckySSLtoSafeLine.py`
   - 节点测速通知 → 使用 `webhook_notify_docker.sh`

3. **查看具体使用说明**
   每个工具都有详细的注释和配置说明，请根据实际需求调整配置参数。

## 📋 系统要求

- **Python脚本**: Python 3.6+
- **JavaScript脚本**: 支持Tampermonkey的现代浏览器
- **操作系统**: 跨平台支持（Linux/Windows/macOS）

## 🔧 依赖安装

```bash
# Python依赖
pip install requests

# 浏览器扩展
# 安装Tampermonkey扩展
```

## 📝 注意事项

- 使用前请仔细阅读各工具的配置说明
- 部分工具需要管理员权限或特定环境配置
- 建议在测试环境中先验证功能
- 定期备份重要配置和数据

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这些工具！

## 📄 许可证

本项目采用GPL-3.0许可证，详见 [LICENSE](LICENSE) 文件。
