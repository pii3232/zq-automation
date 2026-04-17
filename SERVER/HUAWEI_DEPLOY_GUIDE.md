# 华为云部署指南

本指南帮助您将激活服务端从腾讯CloudBase迁移到华为云。

## 部署方式选择

### 方式一：华为云函数计算（推荐）
- 适合无服务器架构
- 按调用次数计费
- 自动弹性伸缩

### 方式二：华为云ECS云服务器
- 适合需要持续运行的场景
- 更高的控制权
- 固定月租

---

## 方式一：函数计算部署

### 1. 准备华为云账号
- 登录 [华为云控制台](https://console.huaweicloud.com)
- 开通 FunctionGraph 函数计算服务
- 开通 RDS for MySQL 数据库

### 2. 创建RDS MySQL数据库
```
登录华为云控制台 -> 云数据库 RDS -> 实例管理
创建MySQL实例，配置：
- 实例规格：通用型（最小规格即可）
- 存储空间：20GB
- 用户名：admin
- 密码：your-password
```

### 3. 初始化数据库
```bash
# 连接到RDS数据库并执行初始化脚本
mysql -h your-rds-host.rds.huaweicloud.com -u admin -p your-database < init_db.py
```

### 4. 打包函数代码
```bash
cd SERVER
pip install -r requirements.txt -t build/
cp -r app.py models.py routes.py config.py utils.py crypto_utils.py build/
cd build
zip -r ../function.zip ./
cd ..
```

### 5. 创建并部署函数
在华为云控制台：
1. 进入 FunctionGraph -> 函数管理
2. 创建函数，选择 Python 3.9 运行时
3. 上传 function.zip
4. 配置函数入口：`app.app`
5. 配置环境变量：
   - RDS_HOST: RDS实例连接地址
   - RDS_PORT: 3306
   - RDS_USER: admin
   - RDS_PASSWORD: your-password
   - RDS_DATABASE: activation_db
   - JWT_SECRET_KEY: 您的密钥

### 6. 创建HTTP触发器
1. 在函数详情页选择"触发器"
2. 创建HTTP触发器
3. 获取公网访问地址

### 7. 配置客户端
在客户端创建配置文件 `data/server_url_config.json`：
```json
{
    "server_url": "https://your-function-trigger-url"
}
```

---

## 方式二：ECS部署

### 1. 购买ECS云服务器
- 登录 [华为云控制台](https://console.huaweicloud.com)
- 购买弹性云服务器 ECS
- 配置：
  - 操作系统：Ubuntu 22.04 或 CentOS 8
  - 规格：2核4G
  - 带宽：5Mbps

### 2. 安装依赖
```bash
# Ubuntu
apt update
apt install -y python3 python3-pip nginx

# CentOS
yum update
yum install -y python3 python3-pip nginx
```

### 3. 部署应用
```bash
cd SERVER
pip3 install -r requirements.txt

# 使用Systemd管理
sudo cp activation.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start activation
sudo systemctl enable activation
```

### 4. 配置Nginx反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. 配置SSL证书（可选）
使用Let's Encrypt免费证书或购买商业证书

---

## 环境变量说明

### 服务端环境变量
| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| RDS_HOST | 华为云RDS连接地址 | example.rds.huaweicloud.com |
| RDS_PORT | 数据库端口 | 3306 |
| RDS_USER | 数据库用户名 | admin |
| RDS_PASSWORD | 数据库密码 | ******** |
| RDS_DATABASE | 数据库名称 | activation_db |
| JWT_SECRET_KEY | JWT密钥 | your-secret-key |
| MAIL_SERVER | 邮件服务器 | smtp.qq.com |
| MAIL_PORT | 邮件端口 | 587 |
| MAIL_USERNAME | 邮件账号 | example@qq.com |
| MAIL_PASSWORD | 邮件密码 | ******** |

---

## 更新客户端服务器地址

部署完成后，需要更新客户端连接的服务器地址：

### 方案一：创建配置文件
在程序目录 `data/` 下创建 `server_url_config.json` 文件：
```json
{
    "server_url": "https://your-huawei-cloud-url"
}
```

### 方案二：修改代码（不推荐）
直接修改以下文件中的服务器地址：
- `tabs.py` 第2450行
- `CLIENT/main.py` 第26行

---

## 常见问题

### Q: 函数部署后无法访问？
A: 检查触发器是否创建正确，确认安全组已开放80/443端口

### Q: 数据库连接失败？
A: 确认RDS安全组已允许函数所在VPC访问3306端口

### Q: 返回"安全中间页"拦截？
A: 华为云函数默认需要配置域名绑定，或在浏览器先访问一次触发URL
