#!/bin/sh

# subs-check webhook通知脚本 (Docker Alpine版本)
# 在节点测速结束后自动调用WebHook发送通知
# 专门为Docker Alpine环境优化，使用wget发送请求。

# 配置通知服务api地址 - 请根据实际情况修改
NOTIFY_HOST="http://192.168.1.1:3000/api/v1/plugin/MsgNotify/send_json?apikey=XXXXXXX" #自定义WebHook通知地址

# 获取成功节点数量（从环境变量获取）
SUCCESS_COUNT=${SUCCESS_COUNT:-0}

# 可选：从环境变量读取统计（若未提供，将尝试自动计算或从日志解析）
# NODES_TOTAL: 获取节点数量（去重前）
# NODES_DEDUP: 去重后节点数量
# TOTAL_TRAFFIC_GB: 测试总消耗流量（单位GB，小数）
NODES_TOTAL=${NODES_TOTAL:-}
NODES_DEDUP=${NODES_DEDUP:-}
TOTAL_GB=${TOTAL_TRAFFIC_GB:-}

# 日志文件路径（程序默认写到临时目录）
LOG_FILE=${LOG_FILE:-/tmp/subs-check.log}

# 若环境变量缺失，从日志文件解析最近一次统计（使用更通用的awk替换，兼容busybox awk）
if [ -z "$NODES_TOTAL" ] && [ -f "$LOG_FILE" ]; then
  NODES_TOTAL=$(awk '/获取节点数量:/{val=$0} END{if(val){ gsub(/^.*获取节点数量:[ \t]*/,"",val); gsub(/[^0-9].*$/,"",val); if(val!="") print val }}' "$LOG_FILE")
fi
if [ -z "$NODES_DEDUP" ] && [ -f "$LOG_FILE" ]; then
  NODES_DEDUP=$(awk '/去重后节点数量:/{val=$0} END{if(val){ gsub(/^.*去重后节点数量:[ \t]*/,"",val); gsub(/[^0-9].*$/,"",val); if(val!="") print val }}' "$LOG_FILE")
fi
if [ -z "$TOTAL_GB" ] && [ -f "$LOG_FILE" ]; then
  TOTAL_GB=$(awk '/测试总消耗流量:/{val=$0} END{if(val){ gsub(/^.*测试总消耗流量:[ \t]*/,"",val); gsub(/GB.*$/,"",val); if(val!="") print val }}' "$LOG_FILE")
fi

# 自动计算订阅链接数量（sub-urls + sub-urls-remote）
CONFIG_FILE="/app/config/config.yaml"
calc_list_count() {
    # $1: key name
    # 统计YAML中顶层key为$1的列表项数量（忽略注释与空行）
    awk -v key="$1:" '
        $0 ~ "^"key"[ \t]*$" {inlist=1; next}
        inlist==1 {
            if ($0 ~ "^[ \t]*#") next
            if ($0 ~ "^[ \t]*-") { count++; next }
            if ($0 ~ "^[^ \t]") { inlist=0 }
        }
        END { print count+0 }
    ' "$CONFIG_FILE" 2>/dev/null
}

SUBS_COUNT=""
if [ -f "$CONFIG_FILE" ]; then
    local_count=$(calc_list_count "sub-urls")
    remote_count=$(calc_list_count "sub-urls-remote")
    # 避免空值
    [ -z "$local_count" ] && local_count=0
    [ -z "$remote_count" ] && remote_count=0
    SUBS_COUNT=$((local_count + remote_count))
fi
# 允许通过环境变量覆盖（例如在外部已统计好）
SUBS_COUNT=${SUBS_COUNT_OVERRIDE:-$SUBS_COUNT}
[ -z "$SUBS_COUNT" ] && SUBS_COUNT="0"

# 获取当前时间
CURRENT_TIME=$(date '+%Y-%m-%d %H:%M:%S')

# 显示用变量（缺失时显示“未知”）
DISP_SUBS=${SUBS_COUNT}
DISP_TOTAL=${NODES_TOTAL:-未知}
DISP_DEDUP=${NODES_DEDUP:-未知}
DISP_TRAFFIC=${TOTAL_GB:-未知}

# 分隔线
SEP="━━━━━━━━━━━━━━"

# 构建通知内容（卡片风格）
TITLE="【📡 节点测速】任务完成"
TEXT="${SEP}\n🧾 检测摘要:\n🔗 当前设置订阅链接数量: ${DISP_SUBS}\n📥 获取节点数量: ${DISP_TOTAL}\n🧹 去重后节点数量: ${DISP_DEDUP}\n✅ 成功节点数量: ${SUCCESS_COUNT}个\n📊 测试总消耗流量: ${DISP_TRAFFIC}GB\n${SEP}\n🕒 测速时间: ${CURRENT_TIME}\n📌 节点测速已完成，请查看最新结果。"

# 构建webhook URL
WEBHOOK_URL="${NOTIFY_HOST}"

# 构建请求体（转义换行）
REQUEST_BODY="{\"title\":\"${TITLE}\",\"text\":\"${TEXT}\"}"

# 发送POST请求
echo "正在发送webhook通知..."
echo "URL: ${WEBHOOK_URL}"
echo "内容: ${REQUEST_BODY}"

# 使用wget发送POST请求（Alpine Linux默认包含wget）
RESPONSE=$(wget -qO- --post-data="${REQUEST_BODY}" \
    --header="Content-Type: application/json" \
    "${WEBHOOK_URL}" 2>&1)

# 检查wget退出状态
if [ $? -eq 0 ]; then
    echo "✅ webhook通知发送成功"
    echo "响应: ${RESPONSE}"
else
    echo "❌ webhook通知发送失败"
    echo "错误: ${RESPONSE}"
    exit 1
fi

echo "脚本执行完成"
