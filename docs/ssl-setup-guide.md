# SSL证书配置完整指南

## 概述

本指南详细说明如何为您的网站配置阿里云SSL证书，确保HTTPS访问的安全性。

## 前提条件

- 已从阿里云获取SSL证书文件
- 已安装Docker和Docker Compose
- 已配置好nginx服务

## 配置步骤

### 1. 证书文件放置

将下载的证书文件复制到项目的nginx/ssl/目录：

```bash
cp /path/to/downloaded/tuyun.website.pem ./nginx/ssl/tuyun.website.pem
cp /path/to/downloaded/tuyun.website.key ./nginx/ssl/tuyun.website.key
```

### 2. 设置文件权限

```bash
# 私钥文件权限（仅所有者可读写）
chmod 600 ./nginx/ssl/tuyun.website.key

# 证书文件权限（所有者可读写，其他用户只读）
chmod 644 ./nginx/ssl/tuyun.website.pem
```

### 3. 验证证书配置

使用提供的脚本验证SSL配置：

```bash
./scripts/check-ssl-config.sh
```

该脚本会检查：
- 证书文件是否存在
- 文件权限是否正确
- 证书有效期
- 证书和私钥是否匹配
- nginx配置是否正确
- docker-compose配置是否正确

### 4. 启动nginx服务

```bash
# 启动nginx服务
docker-compose up -d nginx

# 检查服务状态
docker-compose ps

# 查看nginx日志
docker-compose logs nginx
```

### 5. 测试HTTPS访问

使用提供的测试脚本：

```bash
./scripts/test-ssl.sh
```

或者手动测试：

```bash
# 使用curl测试
curl -I https://tuyun.website

# 检查证书详情
openssl s_client -connect tuyun.website:443 -servername tuyun.website < /dev/null
```

## 配置文件说明

### nginx.conf

SSL相关配置位于nginx.conf文件的HTTPS服务器块中：

```nginx
server {
    listen 443 ssl http2;
    server_name tuyun.website www.tuyun.website;

    # SSL证书配置
    ssl_certificate /etc/nginx/ssl/tuyun.website.pem;
    ssl_certificate_key /etc/nginx/ssl/tuyun.website.key;
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 其他安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # ... 其他配置
}
```

### docker-compose.yml

nginx服务的配置：

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx/ssl:/etc/nginx/ssl:ro
    - ./nginx/certbot:/var/www/certbot:ro
  depends_on:
    - backend
    - frontend
```

注意：我们使用官方nginx:alpine镜像，通过volume映射配置文件，而不是自定义构建镜像。这样做的好处是：
- 使用官方维护的镜像，更安全可靠
- 减少构建时间和镜像大小
- 配置文件可以直接在宿主机上修改，无需重新构建镜像

## 维护和监控

### 证书到期检查

定期检查证书到期情况：

```bash
./scripts/ssl-reminder.sh
```

建议设置cron任务定期执行：

```bash
# 每周一早上9点检查证书
0 9 * * 1 /path/to/your/project/scripts/ssl-reminder.sh
```

### 证书更新

当证书即将到期时，按以下步骤更新：

1. 从阿里云下载新证书
2. 替换证书文件：
   ```bash
   cp /path/to/new/tuyun.website.pem ./nginx/ssl/tuyun.website.pem
   cp /path/to/new/tuyun.website.key ./nginx/ssl/tuyun.website.key
   ```
3. 重载nginx配置：
   ```bash
   docker-compose exec nginx nginx -s reload
   ```
4. 验证新证书：
   ```bash
   ./scripts/check-ssl-config.sh
   ./scripts/test-ssl.sh
   ```

## 故障排除

### 常见问题

1. **证书文件路径错误**
   - 确保证书文件在正确的目录中
   - 检查docker-compose.yml中的卷挂载路径

2. **权限问题**
   - 确保私钥文件权限为600
   - 确保证书文件权限为644

3. **证书和私钥不匹配**
   - 使用openssl命令验证证书和私钥是否匹配
   - 重新下载正确的证书文件

4. **nginx配置错误**
   - 使用`docker-compose exec nginx nginx -t`检查配置语法
   - 查看nginx日志排查具体错误

5. **HTTPS访问失败**
   - 检查防火墙设置
   - 确认443端口已开放
   - 验证DNS解析是否正确

### 调试命令

```bash
# 检查nginx配置
docker-compose exec nginx nginx -t

# 查看nginx错误日志
docker-compose exec nginx tail -f /var/log/nginx/error.log

# 测试SSL连接
openssl s_client -connect tuyun.website:443 -servername tuyun.website

# 检查证书详情
openssl x509 -in ./nginx/ssl/tuyun.website.pem -text -noout
```

## 安全建议

1. **定期检查证书有效期**，至少每月检查一次
2. **设置证书到期提醒**，提前30天开始提醒
3. **备份证书文件**，防止意外丢失
4. **限制私钥文件访问权限**，确保只有必要用户可以访问
5. **监控SSL证书状态**，及时发现和解决问题
6. **使用强加密套件**，定期更新nginx配置以使用最新的安全标准

## 脚本说明

项目中提供了三个实用脚本：

1. **check-ssl-config.sh** - 全面检查SSL配置
2. **ssl-reminder.sh** - 检查证书到期情况
3. **test-ssl.sh** - 测试HTTPS连接和SSL配置

这些脚本可以帮助您快速验证和维护SSL配置。