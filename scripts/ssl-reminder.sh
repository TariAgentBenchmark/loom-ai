#!/bin/bash

# SSL证书到期提醒脚本
# 可以设置为cron任务定期检查证书到期情况

CERT_DIR="./nginx/ssl"
DOMAIN="tuyun.website"
ALERT_DAYS=30  # 提前多少天提醒

echo "=========================================="
echo "SSL证书到期检查"
echo "=========================================="

# 检查证书文件是否存在
if [ ! -f "$CERT_DIR/$DOMAIN.pem" ]; then
    echo "错误: 证书文件不存在: $CERT_DIR/$DOMAIN.pem"
    exit 1
fi

# 获取证书过期时间
if command -v openssl &> /dev/null; then
    NOT_AFTER=$(openssl x509 -in "$CERT_DIR/$DOMAIN.pem" -noout -enddate | cut -d= -f2)
    
    # 转换为时间戳
    EXPIRE_TIMESTAMP=$(date -d "$NOT_AFTER" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$NOT_AFTER" +%s)
    CURRENT_TIMESTAMP=$(date +%s)
    
    # 计算剩余天数
    DAYS_LEFT=$(( ($EXPIRE_TIMESTAMP - $CURRENT_TIMESTAMP) / 86400 ))
    
    echo "域名: $DOMAIN"
    echo "过期时间: $NOT_AFTER"
    echo "剩余天数: $DAYS_LEFT 天"
    echo ""
    
    # 根据剩余天数显示不同级别的提醒
    if [ $DAYS_LEFT -lt 0 ]; then
        echo "🚨 严重: 证书已过期 $((0 - $DAYS_LEFT)) 天！"
        echo "请立即更新证书！"
    elif [ $DAYS_LEFT -lt 7 ]; then
        echo "🔴 紧急: 证书将在 $DAYS_LEFT 天后过期！"
        echo "请尽快更新证书！"
    elif [ $DAYS_LEFT -lt $ALERT_DAYS ]; then
        echo "🟡 警告: 证书将在 $DAYS_LEFT 天后过期"
        echo "请开始准备更新证书"
    else
        echo "✅ 证书有效期正常"
    fi
    
    echo ""
    echo "=========================================="
    echo "证书更新步骤："
    echo "1. 登录阿里云控制台"
    echo "2. 下载新的SSL证书"
    echo "3. 替换 $CERT_DIR/$DOMAIN.pem 和 $CERT_DIR/$DOMAIN.key"
    echo "4. 运行: docker-compose exec nginx nginx -s reload"
    echo "=========================================="
    
    # 如果需要，可以在这里添加邮件或通知逻辑
    # 例如: send_email_alert "$DOMAIN" "$DAYS_LEFT"
    
else
    echo "错误: openssl命令不可用"
    exit 1
fi