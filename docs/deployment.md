# 项目部署指南

## 1. 环境要求

- Docker
- Docker Compose（或使用 Docker 内置的 compose 命令）

### 1.1 安装 Docker Compose

#### 使用 apt 包管理器安装（推荐）

```bash
# 更新包列表
sudo apt update

# 安装 Docker Compose
sudo apt install -y docker-compose

# 验证安装
docker-compose --version
```

#### 使用 curl 下载安装（备选方法）

如果 apt 安装失败或需要特定版本，可以使用以下方法：

```bash
# 下载最新版本的 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 赋予执行权限
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

## 2. 部署步骤

### 2.1 克隆项目

```bash
git clone <项目仓库地址>
cd fastapi
```

### 2.2 构建并启动服务

在项目根目录下执行以下命令：

```bash
# 较新的 Docker 版本（推荐）
docker compose up -d

# 旧版本 Docker
docker-compose up -d
```

这个命令会：
- 构建 FastAPI 应用的 Docker 镜像
- 拉取 MySQL 8.0 镜像（如果本地没有）
- 创建并启动所有定义的服务容器
- 将服务设置为后台运行

### 2.3 查看服务状态

启动后，您可以使用以下命令查看服务的运行状态：

```bash
# 较新的 Docker 版本
docker compose ps

# 旧版本 Docker
docker-compose ps
```

### 2.4 查看服务日志

如果需要查看服务的运行日志，可以使用：

```bash
# 较新的 Docker 版本
# 查看所有服务的日志
docker compose logs

# 查看特定服务的日志（例如 fastapi-app）
docker compose logs fastapi-app

# 实时查看日志
docker compose logs -f

# 旧版本 Docker
# 查看所有服务的日志
docker-compose logs

# 查看特定服务的日志（例如 fastapi-app）
docker-compose logs fastapi-app

# 实时查看日志
docker-compose logs -f
```

## 3. 服务管理

### 3.1 停止服务

如果需要停止服务，可以使用：

```bash
# 较新的 Docker 版本
docker compose down

# 旧版本 Docker
docker-compose down
```

这个命令会停止并移除所有容器，但会保留数据卷（如 MySQL 数据）。

### 3.2 重启服务

如果需要重启服务，可以使用：

```bash
# 较新的 Docker 版本
docker compose restart

# 旧版本 Docker
docker-compose restart
```

### 3.3 重新构建镜像

如果您修改了代码或配置，需要重新构建镜像：

```bash
# 较新的 Docker 版本
docker compose build

# 旧版本 Docker
docker-compose build
```

然后再次启动服务：

```bash
# 较新的 Docker 版本
docker compose up -d

# 旧版本 Docker
docker-compose up -d
```

### 3.4 强制重新构建并启动

如果您想强制重新构建镜像并启动服务，可以使用：

```bash
# 较新的 Docker 版本
docker compose up -d --build

# 旧版本 Docker
docker-compose up -d --build
```

## 4. 访问方式

部署完成后，您可以通过以下方式访问服务：

- **FastAPI 应用**：`http://localhost:8001`
- **API 文档**：`http://localhost:8001/docs`
- **MySQL 数据库**：通过 `localhost:3307` 端口访问
  - 用户名：`dev`
  - 密码：`Dev@1234`
  - 数据库名：`blogdb`

## 5. 环境变量配置

项目的环境变量配置在 `docker-compose.yml` 文件中定义，主要包括：

- `API_KEY`：API 密钥
- `MODEL`：使用的模型
- `DB_HOST`：数据库主机
- `DB_PORT`：数据库端口
- `DB_USER`：数据库用户名
- `DB_PASSWORD`：数据库密码
- `DB_NAME`：数据库名称

## 6. 目录结构说明

```
fastapi/
├── app/              # 应用代码
│   ├── config/       # 配置文件
│   ├── database/     # 数据库相关
│   ├── systems/      # 系统相关功能
│   ├── public/       # 公共接口
│   └── users/        # 用户相关功能
├── docs/             # 文档目录
├── mysql-init/       # MySQL 初始化脚本
├── docker-compose.yml # Docker Compose 配置
├── Dockerfile        # Docker 构建文件
├── main.py           # 应用入口
└── requirements.txt  # 依赖包
```

## 7. 故障排查

### 7.1 服务启动失败

如果服务启动失败，可以查看日志以获取详细信息：

```bash
# 较新的 Docker 版本
docker compose logs

# 旧版本 Docker
docker-compose logs
```

### 7.2 数据库连接问题

如果遇到数据库连接问题，请检查：
- MySQL 服务是否正常运行
- 环境变量中的数据库配置是否正确
- 网络连接是否正常

## 8. 最佳实践

1. **定期备份数据**：定期备份 MySQL 数据卷
2. **更新镜像**：定期更新 Docker 镜像以获取安全补丁
3. **监控服务**：设置监控以确保服务正常运行
4. **使用环境变量**：敏感信息通过环境变量传递，避免硬编码
5. **版本控制**：使用版本控制管理配置文件和代码
6. **端口管理**：确保部署环境中所需端口未被占用
7. **网络配置**：确保容器间网络连接正常