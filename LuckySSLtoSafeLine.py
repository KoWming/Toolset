#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
import time
import hmac
import urllib.parse
import base64
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局配置
BASE_PATH = Path(r"/data/lucky")  # 使用Path对象处理路径
API_BASE_URL = "https://xxx.xxxxx.xxx/api/open/cert"  # 雷池证书管理API请求地址
API_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # 雷池管理端生成的APIToken

# 消息推送渠道配置
push_config = {
    # 自定义webhook消息推送API地址
    'HTTP_URL': "",
    
    # 企业微信机器人Webhook地址
    'WECOM_WEBHOOK': "",
    
    # Server酱的PUSH_KEY
    'SERVERJ_PUSH_KEY': "",
    
    # 钉钉机器人的DD_BOT_TOKEN
    # 钉钉机器人的DD_BOT_SECRET
    'DD_BOT_TOKEN': "",
    'DD_BOT_SECRET': "",
    
    # 飞书机器人的FSKEY
    'FSKEY': "",
    
    # 企业微信应用QYWX_AM
    # 企业微信应用代理QYWX_ORIGIN
    'QYWX_AM': "",
    'QYWX_ORIGIN': "",
}

# 从环境变量读取配置
for k in push_config:
    if os.getenv(k):
        push_config[k] = os.getenv(k)

# 请求配置
REQUEST_TIMEOUT = 30  # 请求超时时间（秒）
MAX_RETRIES = 3  # 最大重试次数

class CertManager:
    def __init__(self):
        self.headers = {
            'accept': 'application/json',
            'X-SLCE-API-TOKEN': API_TOKEN
        }
        self.msg_headers = {
            'accept': 'application/json',
        }
        # 确保基础路径存在
        if not BASE_PATH.exists():
            logger.error(f"基础路径不存在: {BASE_PATH}")
            raise FileNotFoundError(f"基础路径不存在: {BASE_PATH}")
        logger.info(f"使用基础路径: {BASE_PATH}")

    def get_cert_list(self) -> Optional[Dict]:
        """获取证书列表"""
        try:
            response = requests.get(
                API_BASE_URL,
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"获取证书列表失败: {str(e)}")
            return None

    def extract_domain_info(self, cert_data: Dict) -> List[Dict]:
        """提取域名信息，对相同domain_key的域名只保留一个记录"""
        result = []
        processed_domain_keys: Set[str] = set()  # 用于记录已处理的domain_key

        if not cert_data or 'data' not in cert_data or 'nodes' not in cert_data['data']:
            return result

        for node in cert_data['data']['nodes']:
            # 收集该节点下的所有域名
            domains = node.get('domains', [])
            domain_groups = {}  # 用于按domain_key分组域名

            for domain in domains:
                # 处理通配符域名和普通域名
                if domain.startswith('*.'):
                    domain_key = domain.split('.')[1]
                else:
                    domain_key = domain.split('.')[0]

                if domain_key not in domain_groups:
                    domain_groups[domain_key] = []
                domain_groups[domain_key].append(domain)

            # 对每个domain_key只处理一次
            for domain_key, domain_list in domain_groups.items():
                if domain_key in processed_domain_keys:
                    logger.info(f"跳过重复的domain_key: {domain_key} (域名: {', '.join(domain_list)})")
                    continue

                processed_domain_keys.add(domain_key)
                logger.info(f"处理域名组 - domain_key: {domain_key}, 包含域名: {', '.join(domain_list)}")
                
                result.append({
                    'domain_key': domain_key,
                    'id': node['id'],
                    'type': node['type'],
                    'domains': domain_list  # 保存该domain_key下的所有域名
                })

        return result

    def get_cert_info(self, cert_id: int) -> Optional[Dict]:
        """获取指定证书的详细信息"""
        try:
            response = requests.get(
                API_BASE_URL,
                headers=self.headers,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            cert_data = response.json()
            
            if not cert_data or 'data' not in cert_data or 'nodes' not in cert_data['data']:
                logger.error("获取证书列表失败：数据格式错误")
                return None
                
            # 查找指定ID的证书
            for node in cert_data['data']['nodes']:
                if node['id'] == cert_id:
                    # 提取域名信息
                    domains = node.get('domains', [])
                    domain_key = None
                    for domain in domains:
                        if domain.startswith('*.'):
                            domain_key = domain.split('.')[1]
                            break
                        else:
                            domain_key = domain.split('.')[0]
                            break
                    
                    if not domain_key:
                        logger.error(f"无法从域名列表 {domains} 中提取domain_key")
                        return None
                        
                    return {
                        'domain_key': domain_key,
                        'id': node['id'],
                        'type': node['type'],
                        'domains': domains,
                        'issuer': node.get('issuer', '未知'),
                        'valid_before': node.get('valid_before', ''),
                        'trusted': node.get('trusted', False),
                        'revoked': node.get('revoked', False),
                        'expired': node.get('expired', False),
                        'related_sites': node.get('related_sites', [])
                    }
            
            logger.error(f"未找到ID为 {cert_id} 的证书")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"获取证书信息失败: {str(e)}")
            return None

    def find_cert_files(self, domain_info: Dict) -> Optional[Tuple[str, str]]:
        """查找证书文件，使用域名组中的所有域名进行查找"""
        domain_key = domain_info['domain_key']
        domains = domain_info['domains']  # 获取域名组中的所有域名
        
        # 构建所有可能的文件名模式
        possible_names = []
        # 首先添加domain_key相关的模式
        possible_names.extend([
            f"{domain_key}.crt",
            f"{domain_key}.key",
            f"_.{domain_key}.crt",
            f"_.{domain_key}.key"
        ])
        
        # 然后为每个域名添加对应的模式
        for domain in domains:
            possible_names.extend([
                f"{domain}.crt",
                f"{domain}.key",
                f"_.{domain}.crt",
                f"_.{domain}.key"
            ])
        
        logger.debug(f"文件名模式列表: {possible_names}")

        # 在基础目录及其子目录中查找文件
        cert_content = None
        key_content = None

        # 首先在基础目录中查找
        for name in possible_names:
            cert_path = BASE_PATH / name.replace('.crt', '.crt')
            key_path = BASE_PATH / name.replace('.crt', '.key')
            
            if cert_path.exists() and key_path.exists():
                logger.info(f"在基础目录中找到证书文件: {cert_path} 和 {key_path}")
                try:
                    cert_content = cert_path.read_text(encoding='utf-8').strip()
                    key_content = key_path.read_text(encoding='utf-8').strip()
                    return cert_content, key_content
                except Exception as e:
                    logger.error(f"读取证书文件失败: {str(e)}")
                    continue

        # 在子目录中查找
        for root, _, _ in os.walk(BASE_PATH):
            for name in possible_names:
                cert_path = Path(root) / name.replace('.crt', '.crt')
                key_path = Path(root) / name.replace('.crt', '.key')
                
                if cert_path.exists() and key_path.exists():
                    logger.info(f"在子目录 {root} 中找到证书文件: {cert_path} 和 {key_path}")
                    try:
                        cert_content = cert_path.read_text(encoding='utf-8').strip()
                        key_content = key_path.read_text(encoding='utf-8').strip()
                        return cert_content, key_content
                    except Exception as e:
                        logger.error(f"读取证书文件失败: {str(e)}")
                        continue

        logger.warning(f"未找到域名组 {domain_key} (包含域名: {', '.join(domains)}) 的证书文件")
        return None

    def build_message(self, domain_info: Dict, success: bool, error_msg: str = None, format_type: str = 'HTTP') -> Dict:
        """构建消息内容
        
        Args:
            domain_info: 域名信息
            success: 是否成功
            error_msg: 错误信息
            format_type: 消息格式类型 ('HTTP', 'wecom', 'serverj', 'dingding', 'feishu', 'wecom_app')
        """
        # 获取当前时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建消息内容
        details = []
        
        # 添加标题（仅企业微信机器人格式需要）
        if format_type == 'wecom':
            details.append("【🔒雷池证书更新报告】")
        
        # 添加状态信息
        details.append("━━━━━━━━━━━━━━")
        details.append("📊 更新状态：")
        status_emoji = "✅" if success else "❌"
        details.append(f"{status_emoji} {'更新成功' if success else '更新失败'}")
        
        # 添加域名信息
        details.append("━━━━━━━━━━━━━━")
        details.append("🌐 域名信息：")
        details.append(f"📌 域名组：{domain_info['domain_key']}")
        details.append("🔗 包含域名：")
        for domain in domain_info['domains']:
            details.append(f"  • {domain}")
        
        # 检查是否有完整的证书信息
        has_full_info = all(key in domain_info for key in ['issuer', 'valid_before', 'trusted', 'revoked', 'expired'])
        
        if has_full_info:
            # 添加证书信息
            details.append("━━━━━━━━━━━━━━")
            details.append("📜 证书信息：")
            details.append(f"🆔 证书ID：{domain_info['id']}")
            details.append(f"📝 证书类型：{domain_info['type']}")
            details.append(f"🏢 颁发机构：{domain_info['issuer']}")
            
            # 添加证书有效期
            if domain_info['valid_before']:
                try:
                    # 处理日期字符串，移除时区信息
                    date_str = domain_info['valid_before']
                    # 移除时区信息（+08:00 或 Z）
                    if '+' in date_str:
                        date_str = date_str.split('+')[0]
                    elif 'Z' in date_str:
                        date_str = date_str.replace('Z', '')
                    
                    # 解析日期
                    valid_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
                    valid_date_str = valid_date.strftime("%Y-%m-%d %H:%M:%S")
                    days_remaining = (valid_date - datetime.now()).days
                    
                    if days_remaining > 0:
                        if days_remaining <= 30:
                            details.append(f"⚠️ 证书将在 {days_remaining} 天后过期")
                        else:
                            details.append(f"✅ 证书还有 {days_remaining} 天有效期")
                        details.append(f"📅 有效期至：{valid_date_str}")
                    else:
                        details.append("❌ 证书已过期")
                        details.append(f"📅 原有效期至：{valid_date_str}")
                except Exception as e:
                    logger.error(f"解析证书有效期失败: {str(e)}")
            
            # 添加证书状态
            details.append("━━━━━━━━━━━━━━")
            details.append("🔍 证书状态：")
            status_items = [
                ("✅" if domain_info['trusted'] else "❌", "受信任"),
                ("✅" if not domain_info['revoked'] else "❌", "未撤销"),
                ("✅" if not domain_info['expired'] else "❌", "未过期")
            ]
            for emoji, status in status_items:
                details.append(f"{emoji} {status}")
            
            # 添加相关站点信息
            if domain_info.get('related_sites'):
                details.append("━━━━━━━━━━━━━━")
                details.append("🖥️ 使用应用：")
                for site in domain_info['related_sites']:
                    details.append(f"  • {site}")
        
        # 如果有错误信息，添加错误详情
        if not success and error_msg:
            details.append("━━━━━━━━━━━━━━")
            details.append("⚠️ 错误信息：")
            details.append(error_msg)
        
        # 添加时间戳
        details.append("━━━━━━━━━━━━━━")
        details.append(f"⏱ 更新时间：{current_time}")
        
        # 组合所有信息
        content = "\n".join(details)
        
        # 根据格式类型返回不同的消息结构
        if format_type == 'wecom':
            return {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
        elif format_type == 'serverj':
            return {
                "title": "【🔒雷池证书更新报告】",
                "desp": content
            }
        elif format_type == 'dingding':
            return {
                "msgtype": "text",
                "text": {
                    "content": f"【🔒雷池证书更新报告】\n\n{content}"
                }
            }
        elif format_type == 'feishu':
            return {
                "msg_type": "text",
                "content": {
                    "text": f"【🔒雷池证书更新报告】\n\n{content}"
                }
            }
        elif format_type == 'wecom_app':
            return {
                "touser": "@all",
                "msgtype": "text",
                "agentid": "",  # 这个字段会在发送时被替换
                "text": {
                    "content": f"【🔒雷池证书更新报告】\n\n{content}"
                }
            }
        else:  # HTTP格式
            return {
                "title": "【🔒雷池证书更新报告】",
                "text": content
            }

    def send_http_notification(self, message: Dict) -> bool:
        """发送HTTP消息通知"""
        if not push_config.get('HTTP_URL'):
            logger.info("HTTP消息推送未配置，跳过")
            return True

        try:
            response = requests.post(
                push_config['HTTP_URL'],
                headers=self.msg_headers,
                json=message,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                logger.info("HTTP消息推送成功")
                return True
            else:
                logger.error(f"HTTP消息推送失败: {result.get('message', '未知错误')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP消息推送请求失败: {str(e)}")
            return False

    def send_wecom_notification(self, message: Dict) -> bool:
        """发送企业微信机器人消息通知"""
        if not push_config.get('WECOM_WEBHOOK'):
            logger.info("企业微信机器人消息推送未配置，跳过")
            return True

        try:
            response = requests.post(
                push_config['WECOM_WEBHOOK'],
                json=message,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info("企业微信机器人消息推送成功")
                return True
            else:
                logger.error(f"企业微信机器人消息推送失败: {result.get('errmsg', '未知错误')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"企业微信机器人消息推送请求失败: {str(e)}")
            return False

    def send_serverj_notification(self, message: Dict) -> bool:
        """发送Server酱消息通知"""
        if not push_config.get('SERVERJ_PUSH_KEY'):
            logger.info("Server酱消息推送未配置，跳过")
            return True

        try:
            url = f"https://sctapi.ftqq.com/{push_config['SERVERJ_PUSH_KEY']}.send"
            data = {
                "title": message['title'],
                "desp": message['text']
            }
            response = requests.post(url, data=data, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                logger.info("Server酱消息推送成功")
                return True
            else:
                logger.error(f"Server酱消息推送失败: {result.get('message', '未知错误')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Server酱消息推送请求失败: {str(e)}")
            return False

    def send_dingding_notification(self, message: Dict) -> bool:
        """发送钉钉机器人消息通知"""
        if not push_config.get('DD_BOT_TOKEN') or not push_config.get('DD_BOT_SECRET'):
            logger.info("钉钉机器人消息推送未配置，跳过")
            return True

        try:
            timestamp = str(round(time.time() * 1000))
            secret_enc = push_config['DD_BOT_SECRET'].encode('utf-8')
            string_to_sign = f"{timestamp}\n{push_config['DD_BOT_SECRET']}"
            string_to_sign_enc = string_to_sign.encode('utf-8')
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            
            url = f"https://oapi.dingtalk.com/robot/send?access_token={push_config['DD_BOT_TOKEN']}&timestamp={timestamp}&sign={sign}"
            data = {
                "msgtype": "text",
                "text": {
                    "content": f"{message['title']}\n\n{message['text']}"
                }
            }
            response = requests.post(url, json=data, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info("钉钉机器人消息推送成功")
                return True
            else:
                logger.error(f"钉钉机器人消息推送失败: {result.get('errmsg', '未知错误')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"钉钉机器人消息推送请求失败: {str(e)}")
            return False

    def send_feishu_notification(self, message: Dict) -> bool:
        """发送飞书机器人消息通知"""
        if not push_config.get('FSKEY'):
            logger.info("飞书机器人消息推送未配置，跳过")
            return True

        try:
            url = f"https://open.feishu.cn/open-apis/bot/v2/hook/{push_config['FSKEY']}"
            data = {
                "msg_type": "text",
                "content": {
                    "text": f"{message['title']}\n\n{message['text']}"
                }
            }
            response = requests.post(url, json=data, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            
            if result.get('StatusCode') == 0 or result.get('code') == 0:
                logger.info("飞书机器人消息推送成功")
                return True
            else:
                logger.error(f"飞书机器人消息推送失败: {result.get('msg', '未知错误')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"飞书机器人消息推送请求失败: {str(e)}")
            return False

    def send_wecom_app_notification(self, message: Dict) -> bool:
        """发送企业微信应用消息通知"""
        if not push_config.get('QYWX_AM'):
            logger.info("企业微信应用消息推送未配置，跳过")
            return True

        try:
            # 解析企业微信应用配置
            config = push_config['QYWX_AM'].split(',')
            if len(config) != 3:
                logger.error("企业微信应用配置格式错误")
                return False
                
            corpid, corpsecret, agentid = config
            
            # 获取访问令牌
            base_url = push_config.get('QYWX_ORIGIN', 'https://qyapi.weixin.qq.com')
            token_url = f"{base_url}/cgi-bin/gettoken?corpid={corpid}&corpsecret={corpsecret}"
            token_response = requests.get(token_url, timeout=REQUEST_TIMEOUT)
            token_response.raise_for_status()
            token_result = token_response.json()
            
            if token_result.get('errcode') != 0:
                logger.error(f"获取企业微信访问令牌失败: {token_result.get('errmsg', '未知错误')}")
                return False
                
            access_token = token_result.get('access_token')
            
            # 发送消息
            send_url = f"{base_url}/cgi-bin/message/send?access_token={access_token}"
            data = {
                "touser": "@all",
                "msgtype": "text",
                "agentid": agentid,
                "text": {
                    "content": f"{message['title']}\n\n{message['text']}"
                }
            }
            response = requests.post(send_url, json=data, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info("企业微信应用消息推送成功")
                return True
            else:
                logger.error(f"企业微信应用消息推送失败: {result.get('errmsg', '未知错误')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"企业微信应用消息推送请求失败: {str(e)}")
            return False

    def update_cert(self, cert_content: str, key_content: str, cert_id: int, cert_type: int, domain_info: Dict) -> bool:
        """更新证书并发送通知"""
        payload = {
            "manual": {
                "crt": cert_content,
                "key": key_content
            },
            "type": cert_type,
            "id": cert_id
        }

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    API_BASE_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()
                
                success = result.get('err') is None
                error_msg = result.get('msg') if not success else None
                
                if success:
                    # 证书更新成功，获取最新的证书信息
                    updated_cert_info = self.get_cert_info(cert_id)
                    if updated_cert_info:
                        # 使用最新的证书信息构建通知
                        message = self.build_message(updated_cert_info, True)
                        wecom_message = self.build_message(updated_cert_info, True, format_type='wecom')
                        serverj_message = self.build_message(updated_cert_info, True, format_type='serverj')
                        dingding_message = self.build_message(updated_cert_info, True, format_type='dingding')
                        feishu_message = self.build_message(updated_cert_info, True, format_type='feishu')
                        wecom_app_message = self.build_message(updated_cert_info, True, format_type='wecom_app')
                    else:
                        # 如果获取最新信息失败，使用原始信息
                        logger.warning("获取更新后的证书信息失败，使用原始信息发送通知")
                        message = self.build_message(domain_info, True)
                        wecom_message = self.build_message(domain_info, True, format_type='wecom')
                        serverj_message = self.build_message(domain_info, True, format_type='serverj')
                        dingding_message = self.build_message(domain_info, True, format_type='dingding')
                        feishu_message = self.build_message(domain_info, True, format_type='feishu')
                        wecom_app_message = self.build_message(domain_info, True, format_type='wecom_app')
                else:
                    # 更新失败，使用原始信息发送通知
                    message = self.build_message(domain_info, False, error_msg)
                    wecom_message = self.build_message(domain_info, False, error_msg, format_type='wecom')
                    serverj_message = self.build_message(domain_info, False, error_msg, format_type='serverj')
                    dingding_message = self.build_message(domain_info, False, error_msg, format_type='dingding')
                    feishu_message = self.build_message(domain_info, False, error_msg, format_type='feishu')
                    wecom_app_message = self.build_message(domain_info, False, error_msg, format_type='wecom_app')
                
                # 发送通知
                self.send_http_notification(message)
                self.send_wecom_notification(wecom_message)
                self.send_serverj_notification(serverj_message)
                self.send_dingding_notification(dingding_message)
                self.send_feishu_notification(feishu_message)
                self.send_wecom_app_notification(wecom_app_message)
                
                if success:
                    logger.info(f"证书更新成功: id = {cert_id}")
                    return True
                else:
                    logger.error(f"证书更新失败: {error_msg}")
                    return False
                    
            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"更新证书请求失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {str(e)}")
                    continue
                else:
                    error_msg = f"更新证书请求失败 (已重试 {MAX_RETRIES} 次): {str(e)}"
                    # 构建并发送失败通知
                    message = self.build_message(domain_info, False, error_msg)
                    wecom_message = self.build_message(domain_info, False, error_msg, format_type='wecom')
                    serverj_message = self.build_message(domain_info, False, error_msg, format_type='serverj')
                    dingding_message = self.build_message(domain_info, False, error_msg, format_type='dingding')
                    feishu_message = self.build_message(domain_info, False, error_msg, format_type='feishu')
                    wecom_app_message = self.build_message(domain_info, False, error_msg, format_type='wecom_app')
                    self.send_http_notification(message)
                    self.send_wecom_notification(wecom_message)
                    self.send_serverj_notification(serverj_message)
                    self.send_dingding_notification(dingding_message)
                    self.send_feishu_notification(feishu_message)
                    self.send_wecom_app_notification(wecom_app_message)
                    
                    logger.error(error_msg)
                    return False

def main():
    try:
        cert_manager = CertManager()
        
        # 获取证书列表
        cert_data = cert_manager.get_cert_list()
        if not cert_data:
            logger.error("无法获取证书列表，程序退出")
            return

        # 提取域名信息
        domain_info_list = cert_manager.extract_domain_info(cert_data)
        if not domain_info_list:
            logger.warning("未找到有效的域名信息")
            return

        # 处理每个域名
        for domain_info in domain_info_list:
            # 查找证书文件
            cert_files = cert_manager.find_cert_files(domain_info)
            if not cert_files:
                continue

            cert_content, key_content = cert_files
            # 更新证书并发送通知
            cert_manager.update_cert(
                cert_content,
                key_content,
                domain_info['id'],
                domain_info['type'],
                domain_info  # 传递完整的domain_info用于消息构建
            )

    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        raise

if __name__ == "__main__":
    main()
