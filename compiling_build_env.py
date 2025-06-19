import os
import sys
import urllib.request
import zipfile
import shutil
import subprocess
import stat
import ctypes
import time
from ctypes.wintypes import HWND, UINT
import platform
from typing import List
from pathlib import Path

LINUX_TOOLS = [{
    "name": "Build Essentials",
    "type": "apt-group",
    "packages": [
        "build-essential", "cmake", "ninja-build", "bison", "flex", "gettext", "texinfo", "libncurses5-dev",
        "libncursesw5-dev", "gperf", "automake", "libtool", "pkg-config", "genromfs", "libgmp-dev", "libmpc-dev",
        "libmpfr-dev", "libisl-dev", "binutils-dev", "libelf-dev", "libexpat-dev", "gcc-multilib", "g++-multilib",
        "picocom", "u-boot-tools", "util-linux", "p7zip-full", "apt-transport-https", "ca-certificates", "curl",
        "software-properties-common"
    ],
    "verify_cmd": "cmake --version"
}, {
    "name": "Tricore GCC",
    "type": "tricore",
    "repo": "https://gitee.com/yanxiaoyong_1/tricore-gcc-ubuntu",
    "clone_dir": "./tricore-gcc-ubuntu",
    "source_dir": "./tricore-gcc-ubuntu",
    "extract_to": "~/compiler-toolchain/tricore",
    "bin_subpath": "tricore-gcc-ubuntu/bin",
    "verify_cmd": "tricore-elf-gcc --version",
}, {
    "name": "ARM GCC",
    "type": "arm",
    "repo": "https://gitee.com/yanxiaoyong_1/arm-gcc-ubuntu",
    "clone_dir": "./arm-gcc-ubuntu",
    "source_dir": "./arm-gcc-ubuntu",
    "extract_to": "~/compiler-toolchain/arm",
    "bin_subpath": "arm-gcc-ubuntu/bin",
    "verify_cmd": "arm-none-eabi-gcc --version",
}]

if platform.system().lower() == "windows":
    import winreg
    WINDOWS_TOOLS = [{
        "name": "7z",
        "url": "https://www.7-zip.org/a/7z2409-x64.exe",
        "filename": "7z2409-x64.exe",
        "type": "7z",
        "install_args": ["/i", "7z2409-x64.exe"],
        "verify_cmd": "7z --version",
    }, {
        "name": "CMake",
        "url": "https://github.com/Kitware/CMake/releases/download/v4.0.0/cmake-4.0.0-windows-x86_64.msi",
        "filename": "cmake-4.0.0-windows-x86_64.msi",
        "type": "CMake",
        "install_args": ["/i", "cmake-4.0.0-windows-x86_64.msi"],
        "verify_cmd": "cmake --version",
    }, {
        "name": "Ninja",
        "url": "https://github.com/ninja-build/ninja/releases/download/v1.12.1/ninja-win.zip",
        "filename": "ninja-win.zip",
        "type": "ninja",
        "extract_to": "./ninja_temp",
        "copy_to": os.path.join(os.environ["USERPROFILE"], "bin"),
        "verify_cmd": "ninja --version",
    }, {
        "name": "Make",
        "type": "make",
        "downloads": [
            {
                "url": "https://sourceforge.net/projects/gnuwin32/files/make/3.81/make-3.81-bin.zip/download",
                "filename": "make-3.81-bin.zip",
                "extract_to": "./make_bin_temp",
            },
            {
                "url": "https://sourceforge.net/projects/gnuwin32/files/make/3.81/make-3.81-dep.zip/download",
                "filename": "make-3.81-dep.zip",
                "extract_to": "./make_dep_temp",
            },
        ],
        "copy_to": os.path.join(os.environ["USERPROFILE"], "bin"),
        "verify_cmd": "make --version",
    }, {
        "name": "Tricore GCC",
        "type": "tricore",
        "repo": "https://gitee.com/yanxiaoyong_1/tricore-gcc-win32",
        "clone_dir": "./tricore-gcc-win32",
        "source_dir": "./tricore-gcc-win32",
        "extract_to": "C:\\Users\\{}\\compiler".format(os.getenv("USERNAME")),
        "bin_subpath": "tricore-gcc-win32/bin",
        "verify_cmd": "tricore-elf-gcc --version",
    }, {
        "name": "ARM GCC",
        "type": "arm",
        "repo": "https://gitee.com/yanxiaoyong_1/arm-gcc-win32",
        "clone_dir": "./arm-gcc-win32",
        "source_dir": "./arm-gcc-win32",
        "extract_to": "C:\\Users\\{}\\compiler".format(os.getenv("USERNAME")),
        "bin_subpath": "arm-gcc-win32/bin",
        "verify_cmd": "arm-none-eabi-gcc --version",
    }]

PYTHON_PACKAGES = ["kconfiglib"]
HWND_BROADCAST = HWND(0xFFFF)
WM_SETTINGCHANGE = UINT(0x001A)
SMTO_ABORTIFHUNG = 0x0002
ENV_REG_PATH = {"user": r"Environment", "system": r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"}


def run_cmd(commands: List[str], sudo: bool = False) -> None:
    for raw_cmd in commands:
        try:
            if sudo and not raw_cmd.startswith("sudo") and os.path.exists("/usr/bin/sudo"):
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


def install_linux_packages_tools(tools):
    base_commands = ["apt-get update"]
    run_cmd(base_commands, sudo=True)

    for pkg in tools.get('packages', []):
        print(f"\n{'='*30}\n安装 {pkg}\n{'='*30}")
        try:
            run_cmd([f"apt-get install -y {pkg}"], sudo=True)
        except Exception as e:
            print(f"{pkg} 安装失败: {str(e)}")
            continue

def force_remove(func, path, excinfo, max_retries=3, wait_seconds=1):
    for _ in range(max_retries):
        try:
            os.chmod(path, stat.S_IWRITE)
            if os.path.isdir(path):
                shutil.rmtree(path, onerror=force_remove)
            else:
                func(path)
            break
        except Exception:
            time.sleep(wait_seconds)
    else:
        print(f"[警告] 无法删除: {path}")


def download_file(url, save_path):
    try:
        save_path = Path(save_path).resolve()
        parent_dir = save_path.parent

        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            file_name = os.path.basename(save_path)

            print(f"开始下载: {file_name}")

            with open(save_path, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        progress = downloaded / total_size * 100
                        sys.stdout.write(f"\r下载进度: {progress:.1f}% ({downloaded}/{total_size} bytes)")
                        sys.stdout.flush()
            print(f"\n[OK] 下载完成: {os.path.abspath(save_path)}")
            return True

    except urllib.error.HTTPError as e:
        print(f"\n[ERR] HTTP 错误: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        print(f"\n[ERR] URL 错误: {e.reason}")
    except Exception as e:
        print(f"\n[ERR] 下载失败: {str(e)}")

    return False


def run_cmd_safe(cmd):
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, shell=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e.cmd}\n输出: {e.stdout}\n错误: {e.stderr}")
        raise


def install_7z(z_path, args):
    try:
        run_cmd_safe(["7z2409-x64.exe", "/S"])
    except Exception as e:
        print(f"7-Zip安装失败: {str(e)}")
        print("请手动执行以下操作:")
        print("1. 访问 https://www.7-zip.org/download.html")
        print("2. 下载并运行安装程序")
        print("3. 勾选 'Add 7-Zip to PATH' 选项")
        return False
    return True


def install_cmake(cmake_path, args):
    try:
        subprocess.run(["msiexec"] + args, check=True, capture_output=True, text=True, shell=True)
        print(f"[OK] 安装成功: {cmake_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERR] 安装失败: {e.stderr.strip()}")
        return False


def install_ninja(zip_path, config):
    """安装 Ninja 工具"""
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(config["extract_to"])
        print(f"[OK] 解压完成: {config['extract_to']}")
        exe_src = os.path.join(config["extract_to"], "ninja.exe")
        if not os.path.exists(exe_src):
            raise FileNotFoundError("未找到 ninja.exe")

        os.makedirs(config["copy_to"], exist_ok=True)
        exe_dst = os.path.join(config["copy_to"], "ninja.exe")
        shutil.copy(exe_src, exe_dst)
        print(f"[OK] 已复制到系统目录: {exe_dst}")

        ninja_tool_path = config["copy_to"]
        if not set_environment_variable(name="NINJA_TOOL_PATH",
                                        value=ninja_tool_path,
                                        scope="system" if is_system_path(ninja_tool_path) else "user"):
            print(f"[重要] 请手动设置环境变量 NINJA_TOOL_PATH = {ninja_tool_path}")

        shutil.rmtree(config["extract_to"])
        return True
    except Exception as e:
        print(f"[ERR] Ninja 安装失败: {str(e)}")
        return False


def install_make(downloads, config):
    """安装 GNU Make 工具"""
    try:
        target_dir = config["copy_to"]
        os.makedirs(target_dir, exist_ok=True)

        for entry in downloads:
            with zipfile.ZipFile(entry["filename"], "r") as zip_ref:
                zip_ref.extractall(entry["extract_to"])
            print(f"[OK] 解压完成: {entry['extract_to']}")

            src_dir = os.path.join(entry["extract_to"], "bin")
            if "bin" in entry["filename"]:
                exe_src = os.path.join(src_dir, "make.exe")
                shutil.copy(exe_src, target_dir)
                print(f"[OK] 已复制 make.exe 到 {target_dir}")
            else:
                for dll in ["libiconv2.dll", "libintl3.dll"]:
                    dll_src = os.path.join(src_dir, dll)
                    if os.path.exists(dll_src):
                        shutil.copy(dll_src, target_dir)
                        print(f"[OK] 已复制 {dll} 到 {target_dir}")

        if not set_environment_variable(
                name="MAKE_TOOL_PATH", value=target_dir, scope="system" if is_system_path(target_dir) else "user"):
            print(f"[重要] 请手动设置环境变量 MAKE_TOOL_PATH = {target_dir}")
        return True
    except Exception as e:
        print(f"[ERR] Make 安装失败: {str(e)}")
        return False


def find_7z_windows():
    if shutil.which("7z.exe"):
        return "7z.exe"

    default_paths = [r"C:\Program Files\7-Zip\7z.exe", r"C:\Program Files (x86)\7-Zip\7z.exe"]
    for path in default_paths:
        if os.path.exists(path):
            return path
    return None


def add_env_to_bashrc(target_path):

    export_line = f'export PATH="{target_path}:$PATH"\n'

    bashrc_path = Path.home() / ".bashrc"

    try:
        with open(bashrc_path, 'r+') as f:
            content = f.read()
            if str(target_path) in content:
                print("环境变量已存在，无需重复添加")
                return True

            f.write(f"\n{export_line}")
            print(f"成功添加环境变量到 {bashrc_path}")
        run_cmd([("source ~/.bashrc")])
        return True

    except PermissionError:
        print(f"错误：没有权限写入 {bashrc_path}")
        return False
    except Exception as e:
        print(f"写入配置文件失败: {str(e)}")
        return False


def install_windows_toolchain(tool_config):
    """安装 Tricore 编译器工具链"""
    clone_dir = tool_config["clone_dir"]
    try:
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir, onerror=force_remove)

        print(f"正在克隆仓库: {tool_config['repo']}")
        subprocess.run(["git", "clone", tool_config["repo"], clone_dir], check=True, timeout=300)
        print(f"[OK] 仓库克隆完成: {clone_dir}")

        source_dir = tool_config["source_dir"]
        split_files = [f for f in os.listdir(source_dir) if f.endswith(".7z.001")]
        if not split_files:
            raise FileNotFoundError("未找到 .7z.001 分卷文件")

        main_split = os.path.join(source_dir, split_files[0])
        extract_to = tool_config["extract_to"].format(os.getenv("USERNAME"))
        z_path = find_7z_windows()
        if z_path is None:
            z_path = "C:/Program Files/7-Zip/7z.exe"
        if subprocess.run([z_path], capture_output=True).returncode != 0:
            raise EnvironmentError("请先安装 7-Zip 并添加到 PATH 环境变量")

        print(f"正在解压: {main_split} -> {extract_to}")
        os.makedirs(extract_to, exist_ok=True)

        subprocess.run([z_path, "x", main_split, f"-o{extract_to}", "-y"], check=True)
        print(f"[OK] 解压完成: {extract_to}")

        bin_path = os.path.join(extract_to, tool_config["bin_subpath"])
        if not os.path.exists(bin_path):
            raise FileNotFoundError(f"编译器路径不存在: {bin_path}")

        scope = "system" if is_system_path(extract_to) else "user"
        print(f"正在配置{scope}级环境变量...")
        if not add_to_path(bin_path, scope=scope):
            print(f"请手动添加: {bin_path}")

        return True
    except Exception as e:
        print(f"[ERR] Tricore 安装失败: {str(e)}")
        print("tricore-gcc-toolchain是Tricore架构的编译器工具链")
        print("1. 下载[tricore-gcc-win32工具链](yanxiaoyong/compiler-toolchain)")
        print("2. 解压后，进入到tricore-gcc-win32下能看到多个7z压缩包。找到编号为001的压缩包，用7zip解压")
        print("3. 将编译器路径`<your_compiler_path>/tricore-gcc-win32/bin`添加到`PATH`环境变量中")
        print("    1. 按 Win + S 搜索 '环境变量' → 选择 '编辑系统环境变量'")
        print("    2. 在 '用户变量' 中找到 Path → 点击 '编辑' → '新建' → 添加上述bin路径 → 保存")
        print("4. 用管理员权限重启powershell，执行`tricore-elf-gcc --version`，如果显示版本号即安装成功")
        return False
    finally:
        if os.path.exists(clone_dir):
            print("正在清理临时文件...")
            shutil.rmtree(clone_dir, onerror=force_remove)


def install_linux_tricore_toolchain(tool_config, z_path, target_path):
    """安装 Tricore 编译器工具链"""
    clone_dir = tool_config["clone_dir"]
    try:
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir, onerror=force_remove)

        print(f"正在克隆仓库: {tool_config['repo']}")
        subprocess.run(["git", "clone", "--depth=1", tool_config["repo"], clone_dir], check=True, timeout=300)
        print(f"[OK] 仓库克隆完成: {clone_dir}")

        source_dir = tool_config["source_dir"]
        split_files = [f for f in os.listdir(source_dir) if f.endswith(".7z.001")]
        if not split_files:
            raise FileNotFoundError("未找到 .7z.001 分卷文件")

        main_split = os.path.join(source_dir, split_files[0])
        extract_to = Path(f"{tool_config['extract_to']}").expanduser()
        if subprocess.run([z_path], capture_output=True).returncode != 0:
            raise EnvironmentError("请先安装 7-Zip 并添加到 PATH 环境变量")

        print(f"正在解压: {main_split} -> {extract_to}")
        os.makedirs(extract_to, exist_ok=True)

        subprocess.run([z_path, "x", main_split, f"-o{extract_to}", "-y"], check=True)
        print(f"[OK] 解压完成: {extract_to}")

        bin_path = os.path.join(extract_to, tool_config["bin_subpath"])
        if not os.path.exists(bin_path):
            raise FileNotFoundError(f"编译器路径不存在: {bin_path}")

        add_env_to_bashrc(target_path)

        return True
    except Exception as e:
        print(f"[ERR] Tricore 安装失败: {str(e)}")

        return False
    finally:
        if os.path.exists(clone_dir):
            print("正在清理临时文件...")


def is_system_path(path):
    system_paths = [os.environ.get("SystemRoot", "C:\\Windows"), os.environ.get("ProgramFiles", "C:\\Program Files")]
    return any(path.lower().startswith(p.lower()) for p in system_paths)


def set_environment_variable(name, value, scope="user"):
    try:
        key = winreg.HKEY_CURRENT_USER if scope == "user" else winreg.HKEY_LOCAL_MACHINE
        with winreg.OpenKey(key, ENV_REG_PATH[scope], 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, name, 0, winreg.REG_EXPAND_SZ, value)

        ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", SMTO_ABORTIFHUNG,
                                                 5000, None)
        print(f"[OK] 已设置环境变量 {name}={value} ({scope}级)")
        return True
    except PermissionError:
        print("[ERR] 权限不足，请以管理员身份运行")
        return False
    except Exception as e:
        print(f"[ERR] 设置环境变量失败: {str(e)}")
        return False


def add_to_path(path_to_add, scope="user"):
    try:
        normalized_path = os.path.abspath(path_to_add).rstrip("\\")
        if not os.path.isdir(normalized_path):
            raise ValueError(f"无效的目录路径: {normalized_path}")

        key = winreg.HKEY_CURRENT_USER if scope == "user" else winreg.HKEY_LOCAL_MACHINE
        with winreg.OpenKey(key, ENV_REG_PATH[scope], 0, winreg.KEY_READ | winreg.KEY_WRITE) as reg_key:

            try:
                current_path, reg_type = winreg.QueryValueEx(reg_key, "Path")
            except FileNotFoundError:
                current_path, reg_type = "", winreg.REG_EXPAND_SZ

            path_list = [p.rstrip("\\") for p in current_path.split(";") if p.strip()]
            if normalized_path in path_list:
                return True

            new_path = f"{normalized_path};{';'.join(path_list)}"
            winreg.SetValueEx(reg_key, "Path", 0, reg_type, new_path)

        ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", SMTO_ABORTIFHUNG,
                                                 5000, None)
        return True
    except Exception as e:
        print(f"[ERROR] 环境变量操作失败: {str(e)}")
        return False


def verify_installation(tool):
    print(f"\n验证 {tool['name']}...")
    try:
        result = subprocess.run(tool["verify_cmd"].split(), check=True, capture_output=True, text=True, shell=True)
        version = result.stdout.splitlines()[0]
        print(f"[成功] {version}")
        return True
    except Exception as e:
        print(f"[失败] {str(e)}")
        if hasattr(e, "output"):
            print(f"错误输出: {e.output.strip()}")
        return False


def main():
    os.makedirs(".temp", exist_ok=True)
    os.chdir(".temp")
    try:
        current_os = platform.system().lower()
        if current_os == "windows":
            for tool in WINDOWS_TOOLS:
                print(f"\n{'='*30}\n处理: {tool['name']}\n{'='*30}")
                if tool["type"] == "7z":
                    if download_file(tool["url"], tool["filename"]):
                        install_7z(tool["filename"], tool["install_args"])
                        os.remove(tool["filename"])
                elif tool["type"] == "CMake":
                    if not download_file(tool["url"], tool["filename"]) or not install_cmake(
                            tool["filename"], tool["install_args"]):
                        print(
                            "1. 在CMake 4.0.0 官网安装包(https://github.com/Kitware/CMake/releases/download/v4.0.0/cmake-4.0.0-windows-x86_64.msi) 下载对应Windows版本的CMake工具"
                        )
                        print("2. 双击安装，安装的时候请注意勾选'Add to Path'，以添加到环境变量中")
                        print("3. 用管理员权限重启powershell，执行`cmake --version`，输出版本号即表示安装成功")
                    if os.path.exists(tool["filename"]):
                        os.remove(tool["filename"])
                elif tool["type"] == "ninja":
                    if not download_file(tool["url"], tool["filename"]) or not install_ninja(tool["filename"], tool):
                        print(
                            "1. 如果需要使用ninja进行编译，下载 [ninja 官方Zip压缩包](https://github.com/ninja-build/ninja/releases/download/v1.12.1/ninja-win.zip)"
                        )
                        print("2. 解压并将ninja.exe文件复制到系统用户的bin路径下(如C:/Users/<YourName>/bin，注意该路径需要添加进环境变量)")
                        print("3. 用管理员权限重启powershell，执行`ninja --version`，输出版本号即表示安装成功")
                    if os.path.exists(tool["filename"]):
                        os.remove(tool["filename"])
                elif tool["type"] == "make":
                    downloads = []
                    for entry in tool["downloads"]:
                        if not download_file(entry["url"], entry["filename"]):
                            print(
                                "1. 下载 [Make 官方Zip压缩包](https://gnuwin32.sourceforge.net/downlinks/make-bin-zip.php)和[Make依赖包](https://sourceforge.net/projects/gnuwin32/files/make/3.81/make-3.81-dep.zip/download?use_mirror=onboardcloud&download=)"
                            )
                            print(
                                "2. (以3.81版本的make为例)解压并将`make-3.81-bin/bin`文件夹下的make.exe文件和`make-3.81-dep/bin`文件夹下的libiconv2.dll、libintl3.dll文件复制到系统用户的bin路径下(如C:/Users/<YourName>/bin，注意该路径需要添加进环境变量)"
                            )
                            print("3. 用管理员权限重启powershell，执行`make --version`，输出版本号即表示安装成功")
                            break

                        downloads.append(entry)
                    if len(downloads) == len(tool["downloads"]):
                        if not install_make(downloads, tool):
                            print(
                                "1. 下载 [Make 官方Zip压缩包](https://gnuwin32.sourceforge.net/downlinks/make-bin-zip.php)和[Make依赖包](https://sourceforge.net/projects/gnuwin32/files/make/3.81/make-3.81-dep.zip/download?use_mirror=onboardcloud&download=)"
                            )
                            print(
                                "2. (以3.81版本的make为例)解压并将`make-3.81-bin/bin`文件夹下的make.exe文件和`make-3.81-dep/bin`文件夹下的libiconv2.dll、libintl3.dll文件复制到系统用户的bin路径下(如C:/Users/<YourName>/bin，注意该路径需要添加进环境变量)"
                            )
                            print("3. 用管理员权限重启powershell，执行`make --version`，输出版本号即表示安装成功")
                    for entry in downloads:
                        if os.path.exists(entry["filename"]):
                            os.remove(entry["filename"])
                elif tool["type"] == "tricore":
                    z_path = find_7z_windows()
                    if z_path is None:
                        z_path = "C:/Program Files/7-Zip/7z.exe"
                    result = install_windows_toolchain(tool)
                    if result is False:
                        print("tricore-gcc-toolchain是Tricore架构的编译器工具链")
                        print("1. 下载[tricore-gcc-win32工具链](https://gitee.com/yanxiaoyong_1/tricore-gcc-win32)")
                        print("2. 解压后，进入到tricore-gcc-win32下能看到多个7z压缩包。找到编号为001的压缩包，用7zip解压")
                        print("3. 将编译器路径`<your_compiler_path>/tricore-gcc-win32/bin`添加到`PATH`环境变量中")
                        print("    1. 按 Win + S 搜索 '环境变量' → 选择 '编辑系统环境变量'")
                        print("    2. 在 '用户变量' 中找到 Path → 点击 '编辑' → '新建' → 添加上述bin路径 → 保存")
                        print("4. 用管理员权限重启powershell，执行`tricore-elf-gcc --version`，如果显示版本号即安装成功")
                elif tool["type"] == "arm":
                    z_path = find_7z_windows()
                    if z_path is None:
                        z_path = "C:/Program Files/7-Zip/7z.exe"
                    result = install_windows_toolchain(tool)
                    if result is False:
                        print("arm-gcc-toolchain是arm架构的编译器工具链")
                        print("1. 下载[arm-gcc-win32工具链](https://gitee.com/yanxiaoyong_1/arm-gcc-win32)")
                        print("2. arm-gcc-win32下能看到多个7z压缩包。找到编号为001的压缩包，用7zip解压")
                        print("3. 将编译器路径`<your_compiler_path>/arm-gcc-win32/bin`添加到`PATH`环境变量中")
                        print("    1. 按 Win + S 搜索 '环境变量' → 选择 '编辑系统环境变量'")
                        print("    2. 在 '用户变量' 中找到 Path → 点击 '编辑' → '新建' → 添加上述bin路径 → 保存")
                        print("4. 用管理员权限重启powershell，执行`arm-none-eabi-gcc --version`，如果显示版本号即安装成功")
        else:
            for tool in LINUX_TOOLS:
                print(f"\n{'='*30}\n处理: {tool['name']}\n{'='*30}")
                if tool["name"] == "Build Essentials":
                    install_linux_packages_tools(tool)
                elif tool["type"] == "tricore":
                    target_path = Path(f"~/compiler-toolchain/{tool['type']}/tricore-gcc-ubuntu/bin").expanduser()
                    result = install_linux_tricore_toolchain(tool, "7z", target_path)
                    if result is False:
                        print("tricore-gcc-toolchain是Tricore架构的编译器工具链")
                        print("1. 下载[tricore-gcc-ubuntu工具链](https://gitee.com/yanxiaoyong_1/tricore-gcc-ubuntu)")
                        print("2. 解压后，进入到tricore-gcc-ubuntu下能看到多个7z压缩包。找到编号为001的压缩包，用7zip解压")
                        print("3. 将编译器路径`<your_compiler_path>/tricore-gcc-ubuntu/bin`添加到`PATH`环境变量中")
                        print("    1. 按 Win + S 搜索 '环境变量' → 选择 '编辑系统环境变量'")
                        print("    2. 在 '用户变量' 中找到 Path → 点击 '编辑' → '新建' → 添加上述bin路径 → 保存")
                        print("4. 用管理员权限重启powershell，执行`tricore-elf-gcc --version`，如果显示版本号即安装成功")
                elif tool["type"] == "arm":
                    target_path = Path(f"~/compiler-toolchain/{tool['type']}/arm-gcc-ubuntu/bin").expanduser()
                    result = install_linux_tricore_toolchain(tool, "7z", target_path)
                    if result is False:
                        print("arm-gcc-toolchain是arm架构的编译器工具链")
                        print("1. 下载[arm-gcc-ubuntu工具链](https://gitee.com/yanxiaoyong_1/arm-gcc-ubuntu)")
                        print("2. 解压后，进入到arm-gcc-ubuntu下能看到多个7z压缩包。找到编号为001的压缩包，用7zip解压")
                        print("3. 将编译器路径`<your_compiler_path>/arm-gcc-ubuntu/bin`添加到`PATH`环境变量中")
                        print("    1. 按 Win + S 搜索 '环境变量' → 选择 '编辑系统环境变量'")
                        print("    2. 在 '用户变量' 中找到 Path → 点击 '编辑' → '新建' → 添加上述bin路径 → 保存")
                        print("4. 用管理员权限重启powershell，执行`arm-none-eabi-gcc --version`，如果显示版本号即安装成功")
        print("\n=== 安装Python依赖 ===")
        subprocess.run([
            "pip", "install", "kconfiglib", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple", "--trusted-host",
            "pypi.tuna.tsinghua.edu.cn"
        ],
                       check=True)

    finally:
        print("\n安装完成")


if __name__ == "__main__":
    main()
