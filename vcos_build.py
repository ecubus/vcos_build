# This Python file uses the following encoding: utf-8
import os
import subprocess
import sys
import argparse
import platform
import json
import time
import shutil

cur_platfm = platform.system().lower()
build_path = os.path.abspath(os.path.dirname(__file__))
VCOS_ROOT_PATH = os.path.abspath(os.path.join(build_path, ".."))
BOARDS_FUNC = lambda a: [b['board_name'] for b in a['boards']]


def error(log = "", exit_num = 127):
    print("[ERROR]: " + log)
    sys.exit(exit_num)

def write_json_data(data, jsonName):
    with open(jsonName, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def read_json_data(jsonName):
    if os.path.exists(jsonName):
        with open(jsonName, 'r', encoding='utf-8') as b:
            info = json.loads(b.read())
        return info


def new_command_parser():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    with open("./build_config.json", 'r', encoding='utf-8') as f:
        cfg = json.loads(f.read())
        parser = argparse.ArgumentParser(description="VCOS Build")
        parser.add_argument("-board_name", type=str, choices=BOARDS_FUNC(cfg), default=None, \
                            help=str(BOARDS_FUNC(cfg)))
        parser.add_argument("-app_name", type=str, default=None, help="application name, find from ./vcos/examples/")
        parser.add_argument("-sim", type=int, choices=[0, 1], default=0, help="is sim build")
        parser.add_argument("-compiler", type=str, choices=['gcc', 'ghs', 'tasking'], default=None, \
                            help="compiler type")
        parser.add_argument("-mode", type=str, choices=['release', 'debug'], default=None, \
                            help="build config mode, include testcases or not")
        parser.add_argument("-maketool", type=str, choices=['make', 'ninja'], default="make", \
                            help="select make tool, default is [make]")
        parser.add_argument("-update", action="store_true", default=False, help="update build config json file")
        parser.add_argument("-clean", action="store_true", default=False, help="clean output path")
        parser.add_argument("-codegen", action="store_true", default=False, help="dynamic code generation")
        parser.add_argument("-gcmake", action="store_true", default=False, help="gendate cmake config")
        parser.add_argument("-fc", action="store_true", default=False, help="full compilation")
        parser.add_argument("-ic", action="store_true", default=False, help="incremental compilation")
        parser.add_argument("-all", action="store_true", default=False,
                            help="all compilation steps, include '-codegen'、'-gcmake'、'-fc'")
    return parser


def choice_board(app_name, board_name, updateType=False):
    toolchain_path = ''
    compiler = ''
    apps_dir = ''
    output_path = ''
    board_config = ''
    board_build_path = ''
    codegen_boot = ''
    vcosproject_file_path = ''
    is_sim_build = 0
    if cur_platfm == 'windows':
        maketool = "MinGW Makefiles"
    elif cur_platfm == 'linux':
        maketool = "Unix Makefiles"
    else:
        maketool = ""

    with open('./build_config.json', 'r', encoding='utf-8') as f:
        cfg = json.loads(f.read())
        for b in cfg['boards']:
            if b['board_name'] == board_name and b['app_name'] == app_name:
                apps_dir = os.path.join("vcos_examples", app_name)
                board_config = os.path.abspath(os.path.join(build_path, b["board_config"]))
                board_build_path = os.path.abspath(os.path.join(build_path, b["board_build_path"]))
                codegen_boot = os.path.abspath(os.path.join(build_path, b["codegen_boot"]))
                vcosproject_file_path = os.path.abspath(os.path.join(build_path, b["vcosproject_file_path"]))
                break

        compiler = cfg['compiler']
        output_path = os.path.join(VCOS_ROOT_PATH, "..", "output", f"{app_name}_{board_name}_{compiler}")
        buildTmpJson = f'{app_name.replace("/", "_")}_{board_name}_{compiler}_build_temp.json'
        if os.path.exists('./tmp/' + buildTmpJson) and not updateType:
            return read_json_data(f'./tmp/{buildTmpJson}')
        elif updateType:
            if os.path.exists('./tmp/' + buildTmpJson):
                os.remove('./tmp/' + buildTmpJson)
        elif not app_name or not board_name:
            error(log='Please select board first, e.g.: python vcos_build.py -app_name xx -board_name xx -compiler xx')

        data = {
            "app_name": app_name,
            "board_name": board_name,
            "board_build_path": board_build_path,
            "compiler": compiler,
            "build_mode": cfg['build_mode'],
            "apps_dir": apps_dir,
            "codegen_boot": codegen_boot,
            "vcosproject_file_path": vcosproject_file_path,
            "toolchain_path": toolchain_path,
            "build_action": cfg["build_action"],
            "output_path": output_path,
            "board_config": board_config,
            "maketool": maketool,
            "is_sim_build": is_sim_build,
            "sim_board_cfg": cfg["sim_board_config"],
            "sim_defconfig_gen_path": os.path.abspath(os.path.join(build_path, cfg["sim_defconfig_gen_path"])),
            "sim_cfg": cfg["sim_config"],
            "extra_config": cfg["extra_config"]
        }

    if not os.path.exists('./tmp/'):
        try:
            os.makedirs('./tmp/')
        except Exception as e:
            print(f'[ERROR] Make ./tmp folder failed, but not return failure! log: {e}')

    write_json_data(data, f'./tmp/{buildTmpJson}')
    return read_json_data(f'./tmp/{buildTmpJson}')


def set_compiler_path_env(compiler):
    compiler_path = ''
    # 如果配置了环境变量则使用环境变量配置的编译器路径
    if compiler == 'gcc' and os.environ.get("GCC_LICENSE_PATH", None):
        compiler_path = os.environ['GCC_LICENSE_PATH']
    elif compiler == 'tasking' and os.environ.get("TSK_LICENSE_PATH", None):
        compiler_path = os.environ['TSK_LICENSE_PATH']
    elif compiler == 'ghs' and os.environ.get("GHS_LICENSE_PATH", None):
        compiler_path = os.environ['GHS_LICENSE_PATH']

    os.environ["PATH"] = compiler_path + os.pathsep + os.environ["PATH"]
    print(f'[Compiler] compiler [{compiler}] and path is [{compiler_path}].')
    return compiler_path


def set_compiler_process(board_info):
    compiler = board_info['compiler']
    app_name = board_info['app_name']
    board_name = board_info['board_name']
    board_config = board_info['board_config']
    if compiler == 'gcc':
        dst_path = board_config
    elif compiler == 'tasking':
        dst_path = f"{board_config}_{compiler}"
        if not os.path.exists(dst_path):
            os.makedirs(dst_path)
        else:
            shutil.rmtree(dst_path)
            os.makedirs(dst_path)
        shutil.copy2(os.path.join(board_config, 'defconfig'), dst_path)
    board_info['board_config'] = dst_path
    extra_config = board_info['extra_config']
    for extra_line in extra_config:
        with open(os.path.join(dst_path, 'defconfig'), 'r', encoding='utf-8') as fr:
            content = fr.readlines()
            if extra_line not in content:
                content += '\n' + extra_line + '\n'
        with open(os.path.join(dst_path, 'defconfig'), 'w', encoding='utf-8') as fw:
            fw.writelines(content)
    set_compiler_path_env(compiler)
    board_info["output_path"] = os.path.join(VCOS_ROOT_PATH, "..", "output", f'{app_name}_{board_name}_{compiler}')
    return board_info

def set_make_tool_path(maketool, board_info):
    board_info["toolchain_path"] = ""
    if maketool == 'make':
        if cur_platfm == 'windows':
            board_info["maketool"] = "MinGW Makefiles"
            board_info["toolchain_path"] = os.environ.get("MAKE_TOOL_PATH", None)
        elif cur_platfm == 'linux':
            board_info["maketool"] = "Unix Makefiles"
        else:
            board_info["maketool"] = ""
    elif maketool == 'ninja':
        board_info["maketool"] = "Ninja"
        if cur_platfm == 'windows':
            board_info["toolchain_path"] = os.environ.get("NINJA_TOOL_PATH", None)
    else:
        error(f'Not support make tool: {maketool}')
    return board_info


def symlink_dirs():
    with open(os.path.join(build_path, 'build_config.json'), 'r', encoding='utf-8') as f:
        cfg = json.loads(f.read())
        symlink_data = cfg["symlink_data"]
        for dir in symlink_data:
            src = os.path.abspath(os.path.join(VCOS_ROOT_PATH, dir["src"]))
            dst = os.path.abspath(os.path.join(VCOS_ROOT_PATH, dir["dst"]))
            symlink_dir(src, dst)


def symlink_dir(src_dir="", link_dir=""):
    if os.path.exists(src_dir):
        if os.path.lexists(link_dir):
            try:
                if os.path.islink(link_dir):
                    os.unlink(link_dir)
                elif os.path.isfile(link_dir):
                    os.remove(link_dir)
                elif os.path.isdir(link_dir):
                    shutil.rmtree(link_dir)
                else:
                    print(f"link_dir is not exists: {link_dir}")
            except Exception as e:
                print(f"delete {link_dir} failed: {e}")
        try:
            os.symlink(os.path.relpath(src_dir, os.path.dirname(link_dir)), \
                link_dir, target_is_directory=True)
        except OSError as e:
            error(f"[ERROR] create symlink link_dir: {link_dir} failed, {e}")


def run_clean(board_info):
    output_path = board_info['output_path']
    if os.path.exists(output_path):
        try:
            shutil.rmtree(output_path)
        except Exception as e:
            print(f'[ERROR] Clean output path failed, but not return failure! log: {e}')


def run_codegen(board_info):
    board_build_path = board_info["board_build_path"]
    app_name = board_info['app_name']
    board_name = board_info['board_name']
    os.chdir(board_build_path)

    codegen_boot = os.path.abspath(board_info['codegen_boot'])
    vcosproject_file_path = os.path.abspath(board_info['vcosproject_file_path'])
    change_vcosprojects_file(board_info)
    process = subprocess.Popen(
            [sys.executable, codegen_boot, "-p", vcosproject_file_path, "Generate", "--force"],
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            text = True
        )
    for line in iter(process.stdout.readline, ""):
        print(line.strip())
    process.wait()
    print(f'[{app_name}:{board_name}][codegen] End.')
    if process.returncode:
        sys.exit(1)


def change_vcosprojects_file(board_info):
    project_file = board_info['vcosproject_file_path']
    compiler = board_info['compiler']
    compiler_path = set_compiler_path_env(compiler)
    if os.path.exists(project_file):
        with open(project_file, 'r', encoding="utf-8") as f:
            projson = json.loads(f.read())
            projson["compiler"] = compiler
            projson['path']['compiler_path'] = compiler_path
        write_json_data(projson, project_file)
    else:
        print('[ERROR][run_codegen] Vcosproject file is not exists: ', project_file)
        sys.exit(1)


def sim_defconfig_gen(board_info):
    compiler = board_info['compiler']
    app_name = board_info['app_name']
    board_name = board_info['board_name']
    if compiler == 'gcc':
        dest_cfg = board_info["sim_cfg"]
    else:
        dest_cfg = board_info["sim_cfg"] + "_" + compiler
    sim_defconfig_gen_ret = subprocess.Popen(
            [sys.executable, board_info["sim_defconfig_gen_path"], "-s", board_info["sim_board_cfg"], "-d", dest_cfg],
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            text = True
        )
    for line in iter(sim_defconfig_gen_ret.stdout.readline, ""):
        print(line.strip())
    sim_defconfig_gen_ret.wait()
    if sim_defconfig_gen_ret.returncode:
        print(f'[{app_name}:{board_name}] ret.stdout: {sim_defconfig_gen_ret.stdout}')
        print(f'[{app_name}:{board_name}] ret.stderr: {sim_defconfig_gen_ret.stderr}')
        error(log = f'Step build_cmake failed, borard info: {board_info}')

def gendate_cmake(board_info):
    compiler = board_info['compiler']
    set_compiler_path_env(compiler)
    symlink_dirs()
    if board_info["is_sim_build"]:
        sim_defconfig_gen(board_info)
    os.chdir(board_info["board_build_path"])

    board_name = board_info['board_name']
    app_name = board_info['app_name']
    apps_dir = board_info['apps_dir']
    output_path = board_info['output_path']
    board_config = board_info['board_config']
    maketool = board_info['maketool']
    toolchain_path = board_info['toolchain_path']

    if os.path.exists(output_path):
        shutil.rmtree(output_path)

    if cur_platfm == 'windows':
        if maketool == "Ninja":
            gendate_cmake_cmd = f'cmake -B {output_path} -DBOARD_CONFIG={board_config} -DAPPS_DIR={apps_dir} \
                    -G \"{maketool}\" -DCMAKE_MAKE_PROGRAM={os.path.join(toolchain_path, "ninja.exe")} \
                    -DBOARD_NAME={board_name} -DWIN32=1'
        elif maketool == "MinGW Makefiles":
            gendate_cmake_cmd = f'cmake -B {output_path} -DBOARD_CONFIG={board_config} -DAPPS_DIR={apps_dir} \
                    -G \"{maketool}\" -DCMAKE_MAKE_PROGRAM={os.path.join(toolchain_path, "make.exe")} \
                    -DBOARD_NAME={board_name} -DWIN32=1'
        else:
            gendate_cmake_cmd = 'echo "[ERROR][gendate_cmake] Not support maketool type!"'
    elif cur_platfm == 'linux':
        if compiler == 'gcc':
            gendate_cmake_cmd = f'cmake -B {output_path} -DBOARD_CONFIG={board_config} -DAPPS_DIR={apps_dir} \
                -DBOARD_NAME={board_name} -G \"{maketool}\"'
        else:
            gendate_cmake_cmd = f'cmake -B {output_path} -DBOARD_CONFIG={board_config} -DAPPS_DIR={apps_dir} \
                -DBOARD_NAME={board_name}'
    else:
        gendate_cmake_cmd = 'echo "[ERROR][gendate_cmake] Not support platform!"'
    print(f'[{app_name}:{board_name}] gendate_cmake: {gendate_cmake_cmd}')
    gendate_cmake_ret = subprocess.Popen(
            args = gendate_cmake_cmd,
            shell = True,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            text = True
        )
    for line in iter(gendate_cmake_ret.stdout.readline, ""):
        print(line.strip())
    gendate_cmake_ret.wait()
    if gendate_cmake_ret.returncode:
        print(f'[{app_name}:{board_name}] ret.stdout: {gendate_cmake_ret.stdout}')
        print(f'[{app_name}:{board_name}] ret.stderr: {gendate_cmake_ret.stderr}')
        error(log = f'[gendate_cmake] Step gendate_cmake failed, borard info: {board_info}')
    os.chdir(build_path)


def cmake_build(board_info):
    compiler = board_info['compiler']
    set_compiler_path_env(compiler)
    os.chdir(board_info["board_build_path"])

    app_name = board_info['app_name']
    board_name = board_info['board_name']
    output_path = board_info['output_path']
    if board_info["build_action"] == "incre_compile":
        build_command = f"cmake --build {output_path} -j12"
    else:
        build_command = f"cmake --build {output_path} -j12 --clean-first"
    print('[cmake_build] command is: ', build_command)
    build_ret = subprocess.Popen(
            args = build_command,
            shell = True,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            text = True
        )
    for line in iter(build_ret.stdout.readline, ""):
        print(line.strip())
    build_ret.wait()
    if build_ret.returncode:
        print(f'[{app_name}:{board_name}] ret.stdout: {build_ret.stdout}')
        print(f'[{app_name}:{board_name}] ret.stderr: {build_ret.stderr}')
        error(f'[cmake_build] Cmake build failed, board info: {board_info}')
    check_output(board_info)
    os.chdir(build_path)


def check_output(board_info):
    if '/' in board_info['app_name']:
        app_name = board_info['app_name'].split('/')[1]
    else:
        app_name = board_info['app_name']
    output_path = board_info['output_path']
    elf_file = os.path.join(output_path, "nuttx.elf")
    nuttx_file = os.path.join(output_path, "nuttx")
    if os.path.exists(elf_file):
        print(f"# successful generate {app_name}.elf")
    elif os.path.exists(nuttx_file):
        print(f"# successful generate {app_name}")
    else:
        error(f"# failed to generate {app_name}.elf")
    for file in os.listdir(output_path):
        if "nuttx" in file:
            os.rename(os.path.join(output_path, file), os.path.join(output_path, app_name + file.split('nuttx')[1]))


def run_board_build(board_info):
    board_name = board_info['board_name']
    app_name = board_info['app_name']
    mode = board_info['build_mode']
    sim = board_info['is_sim_build']
    maketool = board_info['maketool']
    compiler = board_info['compiler']
    if 'clean' in board_info["build_action"]:
        run_clean(board_info)
    elif 'codegen' in board_info["build_action"]:
        run_codegen(board_info)
    elif 'compile' in board_info["build_action"]:
        cmake_build(board_info)
    elif 'gendate_cmake' == board_info["build_action"]:
        gendate_cmake(board_info)
    elif 'all' == board_info["build_action"]:
        run_codegen(board_info)
        gendate_cmake(board_info)
        cmake_build(board_info)
    elif 'select_board' == board_info["build_action"]:
        print(f"Build board [{board_name}] and app is [{app_name}]")
    elif 'mode' == board_info["build_action"]:
        print(f"Build board [{board_name}] and app is [{app_name}] and mode is [{mode}]")
    elif 'sim' == board_info["build_action"]:
        print(f"Build board [{board_name}] and app is [{app_name}] and sim is [{sim}]")
    elif 'maketool' == board_info["build_action"]:
        print(f"Build board [{board_name}] and app is [{app_name}] and maketool is [{maketool}]")
    elif 'compiler' == board_info["build_action"]:
        print(f"Build board [{board_name}] and app is [{app_name}] and compiler is [{compiler}]")
    else:
        error(f'Not support build action, borard info: {board_info}')


def run_main(args):
    board_info = choice_board(args.app_name, args.board_name, args.update)
    if args.board_name and args.app_name:
        board_info["build_action"] = 'select_board'
    if args.mode:
        board_info["build_mode"] = args.mode
        board_info["build_action"] = 'mode'
    if args.sim:
        board_info["is_sim_build"] = args.sim
        board_info["build_action"] = 'sim'
    if args.compiler:
        board_info["compiler"] = args.compiler
        board_info["build_action"] = 'compiler'
        board_info = set_compiler_process(board_info)
    if args.maketool:
        board_info["build_action"] = 'maketool'
        board_info = set_make_tool_path(args.maketool, board_info)

    if args.clean:
        board_info["build_action"] = 'clean'
    elif args.fc:
        board_info["build_action"] = 'full_compile'
    elif args.ic:
        board_info["build_action"] = 'incre_compile'
    elif args.gcmake:
        board_info["build_action"] = 'gendate_cmake'
    elif args.all:
        board_info["build_action"] = 'all'
    elif args.codegen:
        board_info["build_action"] = 'codegen'
    else:
        if len(sys.argv) < 5:
            error(log='Invalid input parameters, please reinput, \
                  e.g.: python vcos_build.py -app_name xx -board_name xx -compiler xx')

    app_name = board_info['app_name']
    board_name = board_info['board_name']
    compiler = board_info['compiler']
    file = f'{app_name.replace("/", "_")}_{board_name}_{compiler}_build_temp.json'
    write_json_data(board_info, f'./tmp/{file}')
    run_board_build(board_info)


if __name__ == "__main__":
    if os.environ.get("VIRTUAL_ENV"):
        start = time.time()
        parser = new_command_parser()
        args = parser.parse_args()
        run_main(args)
        end = time.time()
        eclipsed = end - start
        print("Elapsed %0.2f s" % eclipsed)
    else:
        if cur_platfm == "windows":
            python_path = os.path.join(VCOS_ROOT_PATH, ".venv/Scripts/python.exe")
        else:
            python_path = os.path.join(VCOS_ROOT_PATH, ".venv/bin/python")
        if not os.path.exists(python_path):
            python_path = sys.executable
        environ = os.environ.copy()
        environ["VIRTUAL_ENV"] = python_path
        process = subprocess.Popen(
            [python_path] + sys.argv,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            text = True,
            env=environ
        )
        for line in iter(process.stdout.readline, ""):
            print(line.strip())
        process.wait()