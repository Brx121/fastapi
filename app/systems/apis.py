from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import FileResponse
import zipfile
from pathlib import Path
import os
import tempfile

router = APIRouter(prefix="/systems")

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent

@router.get("/download")
async def download_files(request: Request, background_tasks: BackgroundTasks):
    # 模拟用户和token（实际项目中应该从认证系统获取）
    user = {"id": 1, "username": "admin"}
    token = "mock_token_for_testing"
    # 获取客户端IP地址
    host = request.client.host
    port = request.base_url.port
    if port:
        host = f"{host}:{port}"
    
    file_name_1 = ".gitlab-ci.yml"
    file_name_2 = "gitlab_integration.py"
    
    # 确保gitlab_script目录存在
    gitlab_script_dir = BASE_DIR / "app" / "systems" / "gitlab_script"
    gitlab_script_dir.mkdir(exist_ok=True)
    
    file_path_yml = gitlab_script_dir / file_name_1
    file_path_py = gitlab_script_dir / file_name_2
    
    # 生成gitlab_integration.py文件
    fetch_host(host, file_path_py, token)
    
    # 创建zip文件
    tmp = tempfile.NamedTemporaryFile(prefix="cicd-", suffix=".zip", delete=False)
    zip_file_path = Path(tmp.name)
    tmp.close()

    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        if file_path_yml.exists():
            zipf.write(file_path_yml, file_name_1)
        if file_path_py.exists():
            zipf.write(file_path_py, file_name_2)

    background_tasks.add_task(lambda p: os.path.exists(p) and os.remove(p), str(zip_file_path))
    
    # 返回文件响应
    return FileResponse(
        path=zip_file_path,
        media_type="application/zip",
        filename="gitlab-cicd-scripts.zip",
        headers={"Access-Control-Expose-Headers": "Content-Disposition"}
    )

def fetch_host(host, file_path_py, token):
    # 创建base_gitlab_integration.py文件（如果不存在）
    base_file_path = BASE_DIR / "app" / "systems" / "gitlab_script" / "base_gitlab_integration.py"
    
    # 读取base文件内容
    with open(base_file_path, "r", encoding="utf-8") as file:
        content = file.readlines()
    
    # 插入host和token
    new_line = (
        f'host = "{host}"\n'
        f'headers = {{\n'
        f'    "Authorization": "JWT {token}"\n'
        f'}}\n'
    )
    content.insert(3, new_line)
    
    # 写入新文件
    with open(file_path_py, "w", encoding="utf-8") as file:
        file.writelines(content)
