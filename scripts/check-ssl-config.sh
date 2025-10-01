#!/bin/bash

# SSL证书配置检查脚本
# 用于验证nginx SSL配置是否正确

echo "=========================================="
echo "SSL证书配置检查"
echo "=========================================="

CERT_DIR="./nginx/ssl"
DOMAIN="tuyun.website"

# 检查证书文件是否存在
echo "1. 检查证书文件..."
if [ -f "$CERT_DIR/$DOMAIN.pem" ] && [ -f "$CERT_DIR/$DOMAIN.key" ]; then
    echo "✓ 证书文件存在"
else
    echo "✗ 证书文件不存在"
    exit 1
fi

# 检查文件权限
echo "2. 检查文件权限..."
CERT_PERM=$(stat -c "%a" "$CERT_DIR/$DOMAIN.pem" 2>/dev/null || stat -f "%A" "$CERT_DIR/$DOMAIN.pem")
KEY_PERM=$(stat -c "%a" "$CERT_DIR/$DOMAIN.key" 2>/dev/null || stat -f "%A" "$CERT_DIR/$DOMAIN.key")

if [ "$CERT_PERM" = "644" ]; then
    echo "✓ 证书文件权限正确 (644)"
else
    echo "⚠ 证书文件权限: $CERT_PERM (建议: 644)"
fi

if [ "$KEY_PERM" = "600" ]; then
    echo "✓ 私钥文件权限正确 (600)"
else
    echo "⚠ 私钥文件权限: $KEY_PERM (建议: 600)"
fi

# 检查证书有效期
echo "3. 检查证书有效期..."
if command -v openssl &> /dev/null; then
    NOT_BEFORE=$(openssl x509 -in "$CERT_DIR/$DOMAIN.pem" -noout -startdate | cut -d= -f2)
    NOT_AFTER=$(openssl x509 -in "$CERT_DIR/$DOMAIN.pem" -noout -enddate | cut -d= -f2)
    
    echo "  生效时间: $NOT_BEFORE"
    echo "  过期时间: $NOT_AFTER"
    
    # 计算剩余天数
    EXPIRE_TIMESTAMP=$(date -d "$NOT_AFTER" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$NOT_AFTER" +%s)
    CURRENT_TIMESTAMP=$(date +%s)
    DAYS_LEFT=$(( ($EXPIRE_TIMESTAMP - $CURRENT_TIMESTAMP) / 86400 ))
    
    if [ $DAYS_LEFT -lt 30 ]; then
        echo "⚠ 警告: 证书将在 $DAYS_LEFT 天后过期"
    else
        echo "✓ 证书有效期正常 (剩余 $DAYS_LEFT 天)"
    fi
else
    echo "⚠ openssl命令不可用，无法检查证书有效期"
fi

# 检查证书和私钥是否匹配
echo "4. 检查证书和私钥匹配..."
if command -v openssl &> /dev/null; then
    CERT_MD5=$(openssl x509 -noout -modulus -in "$CERT_DIR/$DOMAIN.pem" | openssl md5 | cut -d' ' -f2)
    KEY_MD5=$(openssl rsa -noout -modulus -in "$CERT_DIR/$DOMAIN.key" | openssl md5 | cut -d' ' -f2)
    
    if [ "$CERT_MD5" = "$KEY_MD5" ]; then
        echo "✓ 证书和私钥匹配"
    else
        echo "✗ 证书和私钥不匹配"
        exit 1
    fi
else
    echo "⚠ openssl命令不可用，无法验证证书和私钥匹配"
fi

# 检查nginx配置
echo "5. 检查nginx配置..."
if [ -f "nginx/nginx.conf" ]; then
    if grep -q "ssl_certificate /etc/nginx/ssl/$DOMAIN.pem" nginx/nginx.conf && \
       grep -q "ssl_certificate_key /etc/nginx/ssl/$DOMAIN.key" nginx/nginx.conf; then
        echo "✓ nginx配置中的SSL证书路径正确"
    else
        echo "✗ nginx配置中的SSL证书路径不正确"
        exit 1
    fi
else
    echo "⚠ nginx配置文件不存在"
fi

# 检查docker-compose配置
echo "6. 检查docker-compose配置..."
if [ -f "docker-compose.yml" ]; then
    if grep -q "./nginx/ssl:/etc/nginx/ssl" docker-compose.yml; then
        echo "✓ docker-compose中的SSL证书卷挂载正确"
    else
        echo "✗ docker-compose中的SSL证书卷挂载不正确"
        exit 1
    fi
else
    echo "⚠ docker-compose.yml文件不存在"
fi

echo ""
echo "=========================================="
echo "SSL证书配置检查完成"
echo "=========================================="
echo ""
echo "如果所有检查都通过，您可以运行以下命令启动nginx："
echo "docker-compose up -d nginx"
echo ""
echo "启动后，使用以下命令测试HTTPS访问："
echo "curl -I https://$DOMAIN"