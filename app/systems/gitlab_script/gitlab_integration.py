import sys
import requests

host = "10.0.3.170:8001"
headers = {
    "Authorization": "JWT mock_token_for_testing"
}


# SCA 扫描相关
base_url = ""
SCA_API_URL = f'http://{base_url}/api/v1/projects/cicd/scan/'


def trigger_sca_scan(file_path, project_name, version):
    scan_data = {
        'projectName': project_name,
        'version': version
    }
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f)}
        headers = {}
        response = requests.post(headers=headers, url=SCA_API_URL, data=scan_data, files=files)

    print(response.status_code)


def main():
    file_path, project_name, version = sys.argv[1], sys.argv[2], sys.argv[3]
    print(f"File path: {file_path}, Project name: {project_name}, Version: {version}")
    trigger_sca_scan(file_path, project_name, version)


if __name__ == "__main__":
    main()