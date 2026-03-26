# FastAPI 基础项目框架

## 项目简介

本项目是一个基于 FastAPI 框架搭建的基础项目结构，提供了完整的目录组织和基本功能，支持 Docker 容器化部署。

## 项目结构

```
├── app/
│   ├── users/             # 用户模块
│   ├── systems/           # 系统模块
│   │   ├── gitlab_script/  # CICD GitLab 脚本
│   │   └── apis.py         # 系统接口
│   ├── public/            # 公共模块
│   ├── database/          # 数据库模块
│   └── config/            # 配置模块
├── docs/                  # 文档目录
├── logs/                  # 日志目录
├── mysql-init/            # MySQL 初始化脚本
├── main.py                # 主应用入口
├── requirements.txt       # 项目依赖
├── .env                   # 环境变量
├── Dockerfile             # Docker 构建文件
├── docker-compose.yml     # Docker Compose 配置
├── supervisor.conf        # Supervisor 配置文件
├── install.sh             # 一键部署脚本
└── README.md              # 项目说明
```

## 功能特性

- **用户模块**：提供用户相关的接口
- **系统模块**：
  - **CICD GitLab 功能**：提供 GitLab CI/CD 相关的脚本和工具
  - **下载接口**：生成并下载包含 GitLab CI 配置和集成脚本的 zip 包
- **公共模块**：提供公共的接口，如健康检查
- **数据库模块**：提供数据库连接和模型定义
- **配置模块**：提供项目配置管理

## 启动方法

### 方法一：使用 Docker Compose 部署（推荐）

1. 确保已安装 Docker 和 Docker Compose

2. 在项目根目录下执行：
   ```bash
   docker compose up -d
   ```

3. 查看服务状态：
   ```bash
   docker compose ps
   ```

### 方法二：使用 Supervisor 部署

1. 在项目根目录下执行一键部署脚本：
   ```bash
   sudo ./install.sh
   ```

2. 查看服务状态：
   ```bash
   sudo supervisorctl status fastapi-app
   ```

3. 管理服务：
   ```bash
   # 启动服务
   sudo supervisorctl start fastapi-app
   
   # 停止服务
   sudo supervisorctl stop fastapi-app
   
   # 重启服务
   sudo supervisorctl restart fastapi-app
   ```

### 方法三：本地运行

1. 激活虚拟环境：
   ```bash
   source venv/bin/activate
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 启动服务：
   ```bash
   python -m uvicorn main:app --reload --port 8001 --host 0.0.0.0
   ```

## 访问地址

- **FastAPI 应用**：http://localhost:8001
- **Swagger UI 文档**：http://localhost:8001/docs
- **ReDoc 文档**：http://localhost:8001/redoc
- **MySQL 数据库**：通过 localhost:3307 端口访问
  - 用户名：dev
  - 密码：Dev@1234
  - 数据库名：blogdb

## 技术栈

- FastAPI
- Uvicorn
- SQLAlchemy (数据库 ORM)
- PyMySQL (数据库驱动)
- python-dotenv (环境变量管理)
- Docker (容器化部署)
- Docker Compose (多容器编排)

## 注意事项

- 服务默认运行在 8001 端口
- MySQL 数据库默认映射到 3307 端口
- 包含基础的数据库连接配置
- 提供了用户、系统和公共模块的路由结构
- 支持 Docker 容器化部署

## 部署文档

详细的部署步骤和故障排查请参考 [部署指南](docs/deployment.md)。

## 后续扩展

- 可在此基础上添加智能体接口
- 可扩展其他功能模块
- 可根据需要配置环境变量
- 可添加更多 Docker 相关配置
