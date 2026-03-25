#!/usr/bin/env bash

workdir="$(pwd)"
export workdir=$workdir
echo "workdir: $workdir"
basedir=$(dirname $(pwd))
export basedir=$basedir
echo "basedir: $basedir"
env=$workdir/venv
export env=$env
echo "env: $env"
user=$(whoami)
group=$(id -gn)

echo -e "\033[34m 开始部署 FastAPI 应用... \033[0m"

create_log_dir() {
  echo -e "\033[34m 创建日志目录... \033[0m"
  mkdir -p $workdir/logs
  sudo chown -R $user:$group $workdir/logs
}

install_pkg() {
  echo -e "\033[34m 安装依赖包... \033[0m"
  apt --help > /dev/null 2>&1
  if [ $? -ne 127 ]
  then
    sudo apt update
    sudo apt install -y supervisor python3 python3-pip python3-venv
  fi
  yum --help > /dev/null 2>&1
  if [ $? -ne 127 ]
  then
    yum install -y epel-release
    yum update -y
    yum install -y supervisor python3 python3-pip python3-venv
  fi
  echo -e "\033[34m 依赖包安装完成！ \033[0m"
}

install_depend() {
  echo -e "\033[34m 安装项目依赖... \033[0m"
  if [ ! -d "$env" ]; then
    echo -e "\033[34m 创建 Python 虚拟环境... \033[0m"
    python3 -m venv $env
  fi
  echo -e "\033[34m 安装项目依赖包... \033[0m"
  $env/bin/pip install -r $workdir/requirements.txt
  echo -e "\033[34m 项目依赖安装完成！ \033[0m"
}

install_supervisor() {
  echo -e "\033[34m 配置 Supervisor... \033[0m"
  conf_path=/etc/supervisor/conf.d
  yum --help > /dev/null 2>&1
  if [ $? -ne 127 ]
  then
    conf_path=/etc/supervisord.d
  fi
  
  echo -e "\033[34m 添加 FastAPI 应用启动守护文件... \033[0m"
  sudo cat <<EOF >$conf_path/fastapi-app.conf
[program:fastapi-app]
directory=$workdir
command=$env/bin/uvicorn main:app --host 0.0.0.0 --port 8001
autostart=true
autorestart=true
startsecs=5
startretries=3
user=$user
group=$group
stdout_logfile=$workdir/logs/fastapi-app.log
stderr_logfile=$workdir/logs/fastapi-app-error.log
EOF

  echo -e "\033[34m 设置 Supervisor 开机启动... \033[0m"
  sudo systemctl enable supervisor
  echo -e "\033[34m 重启 Supervisor... \033[0m"
  sudo systemctl restart supervisor
  echo -e "\033[34m Supervisor 配置完成！ \033[0m"
}

start_app() {
  echo -e "\033[34m 启动应用... \033[0m"
  sudo supervisorctl reread
  sudo supervisorctl update
  sudo supervisorctl start fastapi-app
  echo -e "\033[34m 查看应用状态... \033[0m"
  sudo supervisorctl status fastapi-app
}

show_result() {
  echo -e "\033[32m 部署完成！ \033[0m"
  echo -e "\033[32m 应用访问地址: http://localhost:8001 \033[0m"
  echo -e "\033[32m API 文档地址: http://localhost:8001/docs \033[0m"
}

case "$1" in
    "install_pkg")
        install_pkg
        ;;
    "install_depend")
        install_depend
        ;;
    "install_supervisor")
        install_supervisor
        ;;
    "start_app")
        start_app
        ;;
    *)
        create_log_dir
        install_pkg
        install_depend
        install_supervisor
        start_app
        show_result
        ;;
esac
