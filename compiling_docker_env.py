import os
import subprocess
from ctypes.wintypes import HWND, UINT
from typing import List
from pathlib import Path

LINUX_TOOLS = [{
    "name": "Build Essentials",
    "type": "apt-group",
    "packages": ["software-properties-common", "docker-ce", "docker-ce-cli", "containerd.io"]
}]


def run_cmd(commands: List[str], sudo: bool = False) -> None:
    for raw_cmd in commands:
        try:
            if sudo and not raw_cmd.startswith("sudo"):
                full_cmd = f"sudo {raw_cmd}"
            else:
                full_cmd = raw_cmd

            proc = subprocess.run(full_cmd,
                                  shell=True,
                                  check=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  text=True,
                                  executable="/bin/bash")
            if proc.stdout.strip():
                print(f"[CMD] {full_cmd}\n[OUT] {proc.stdout.strip()}\n")

        except subprocess.CalledProcessError as e:
            error_msg = f"""
            命令执行失败: {full_cmd}
            退出码: {e.returncode}
            错误输出: {e.stderr.strip()}
            """
            raise RuntimeError(error_msg) from e


def add_user_to_docker_group():
    username = os.getenv("USER")
    if not username:
        raise ValueError("无法获取当前用户名")

    commands = [f"usermod -aG docker {username}", "echo '请注销后重新登录使组生效'"]
    run_cmd(commands, sudo=True)


def install_linux_packages_tools(tools):
    docker_repo_cmd = ('echo "deb [arch=$(dpkg --print-architecture) '
                       'signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] '
                       'https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" '
                       '| sudo tee /etc/apt/sources.list.d/docker.list > /dev/null')
    run_cmd([docker_repo_cmd], sudo=True)

    gpg_key_cmd = ('curl -fsSL https://download.docker.com/linux/ubuntu/gpg | '
                   'sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg')
    run_cmd([gpg_key_cmd], sudo=True)

    base_commands = ["apt-get update"]
    run_cmd(base_commands, sudo=True)

    for pkg in tools.get('packages', []):
        print(f"\n{'='*30}\n安装 {pkg}\n{'='*30}")
        try:
            run_cmd([f"apt-get install -y {pkg}"], sudo=True)
        except Exception as e:
            print(f"{pkg} 安装失败: {str(e)}")
            continue

    run_cmd(["usermod -aG docker $USER"], sudo=True)
    add_user_to_docker_group()


def main():
    os.makedirs(".temp", exist_ok=True)
    os.chdir(".temp")
    try:
        for tool in LINUX_TOOLS:
            print(f"\n{'='*30}\n处理: {tool['name']}\n{'='*30}")
            if tool["name"] == "Build Essentials":
                install_linux_packages_tools(tool)

    finally:
        print("\n安装完成")


if __name__ == "__main__":
    main()
