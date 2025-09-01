# Toolset

自用工具、脚本和一些收集的奇奇怪怪的东西！

## 📁 工具脚本说明

### 🐳 Docker-all-install.py
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

---

### 🎯 朱雀自动转盘抽奖及统计-1.4.js
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

---

### 🔐 LuckySSLtoSafeLine.py
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
```bash
# 设置环境变量配置
export API_TOKEN="your_leichi_api_token"
export WECOM_WEBHOOK="your_wecom_webhook_url"

# 运行脚本
python3 LuckySSLtoSafeLine.py
```

**配置说明**:
- 需要配置雷池管理端API Token
- 支持环境变量配置推送渠道
- 可自定义Lucky证书文件路径（默认：/data/lucky）
- 支持多种证书类型和域名模式

**适用场景**: Lucky证书自动化管理、SSL证书自动更新、雷池证书同步、运维自动化

**官方文档**: [Lucky SSL模块文档](https://lucky666.cn/docs/modules/ssl)

---

## 🚀 快速开始

1. **克隆仓库**
   ```bash
   git clone <repository_url>
   cd Toolset
   ```

2. **选择需要的工具**
   - Docker环境配置 → 使用 `Docker-all-install.py`
   - PT站点自动化 → 使用 `朱雀自动转盘抽奖及统计-1.4.js`
   - 证书管理迁移 → 使用 `LuckySSLtoSafeLine.py`

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
