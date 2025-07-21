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
build_path = os.path.abspath(os.path.dirname(__file__)).replace('\\', '/')
VCOS_ROOT_PATH = os.path.abspath(os.path.join(build_path, "..")).replace('\\', '/')

APPS_FUNC = lambda a: list(set(b['app_name'] for b in a['apps']))
BOARDS_FUNC = lambda a: list(set(b['board_name'] for b in a['apps']))
BOARDS_DICT_FUNC = lambda a: str([str(b['app_name']) + ':' + b['board_name'] for b in a['apps']])


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
        parser = argparse.ArgumentParser(description="VCOS Build", formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument("-app_name", type=str, required=True, choices=APPS_FUNC(cfg), default=None, \
                            help="application name, find from ./vcos/examples/")
        parser.add_argument("-board_name", type=str, required=True, choices=BOARDS_FUNC(cfg), default=None, \
                            help=f"support board list, with app: {BOARDS_DICT_FUNC(cfg)}")
        parser.add_argument("-compiler", type=str, choices=['gcc', 'ghs', 'tasking', 'arm'], default=None, \
                            help="Compiler type")
        parser.add_argument("-mode", type=str, choices=['release', 'debug'], default=None, \
                            help="build config mode, include testcases or not")
        parser.add_argument("-sim", type=int, choices=[0, 1], default=None, help="is sim build")
        parser.add_argument("-update", action="store_true", default=False, help="update build config json file")
        parser.add_argument("-clean", action="store_true", default=False, help="clean output path")
        parser.add_argument("-maketool", type=str, choices=['make', 'ninja'], default=None, \
                            help="select make tool, default is [make]")
        parser.add_argument("-codegen", action="store_true", default=False, help="dynamic code generation")
        parser.add_argument("-gcmake", action="store_true", default=False, help="gendate cmake config")
        parser.add_argument("-fc", action="store_true", default=False, help="full compilation")
        parser.add_argument("-ic", action="store_true", default=False, help="incremental compilation")
        parser.add_argument("-all", action="store_true", default=False,
                            help="all compilation steps, include '-codegen'、'-gcmake'、'-fc'")
    return parser


def choice_board(app_name, board_name, compiler, updateType=False):
    toolchain_path = ''
    compiler_tmp = ''
    apps_dir = ''
    output_path = ''
    board_config = ''
    board_build_path = ''
    codegen_boot = ''
    vcosproject_file_path = ''
    is_sim_build = 0
    sim_datas = []
    sim_arxml_path = ''
    sim_board_config = ''
    sim_defconfig_gen_path = ''
    sim_config = ''
    extra_config = []
    extra_configs = ''
    if cur_platfm == 'windows':
        maketool = "MinGW Makefiles"
    elif cur_platfm == 'linux':
        maketool = "Unix Makefiles"
    else:
        maketool = ""

    buildTmpJson = f'{app_name.replace("/", "_")}_{board_name}_build_temp.json'
    if os.path.exists('./tmp/' + buildTmpJson) and not updateType:
        return read_json_data(f'./tmp/{buildTmpJson}')
    elif updateType:
        if os.path.exists('./tmp/' + buildTmpJson):
            os.remove('./tmp/' + buildTmpJson)
    elif not app_name or not board_name:
        error(log='Please select board first, e.g.: python vcos_build.py -app_name xx -board_name xx')

    with open("./build_config.json", 'r', encoding='utf-8') as f:
        cfg = json.loads(f.read())
        if compiler:
            compiler_tmp = compiler
        else:
            compiler_tmp = cfg['compiler']
        extra_configs = cfg["extra_configs"]
        x = False
        for b in cfg['apps']:
            if b['board_name'] == board_name and b['app_name'] == app_name:
                apps_dir = f"vcos_examples/{app_name}"
                board_config = os.path.abspath(os.path.join(build_path, \
                            f'{b["board_config"]}_{compiler_tmp}')).replace('\\', '/')
                if not os.path.exists(board_config):
                    os.makedirs(board_config)
                else:
                    shutil.rmtree(board_config)
                    os.makedirs(board_config)
                shutil.copy2(os.path.join(b["board_config"], 'defconfig').replace('\\', '/'), board_config)
                board_build_path = os.path.abspath(os.path.join(build_path, b["board_build_path"])).replace('\\', '/')
                codegen_boot = os.path.abspath(os.path.join(build_path, b["codegen_boot"])).replace('\\', '/')
                vcosproject_file_path = os.path.abspath(os.path.join(build_path, \
                                        b["vcosproject_file_path"])).replace('\\', '/')
                x = True
                break
        if not x:
            error(log='Please choose the correct app_name and board_name.')

        # default sim data is semidrive
        sim_datas = cfg["sim_datas"]
        for sim_data in sim_datas:
            if board_name in sim_data['sim_board_config']:
                sim_arxml_path = sim_data["sim_arxml_path"]
                sim_board_config = sim_data["sim_board_config"]
                sim_defconfig_gen_path = os.path.abspath(os.path.join(build_path, \
                                        sim_data["sim_defconfig_gen_path"])).replace('\\', '/')
                sim_config = sim_data["sim_config"]

        output_path = os.path.join(VCOS_ROOT_PATH, "..", "output", \
                                   f"{app_name}_{board_name}_{compiler_tmp}").replace('\\', '/')

        data = {
            "app_name": app_name,
            "board_name": board_name,
            "board_build_path": board_build_path,
            "compiler": compiler_tmp,
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
            "sim_arxml_path": sim_arxml_path,
            "sim_board_cfg": sim_board_config,
            "sim_defconfig_gen_path": sim_defconfig_gen_path,
            "sim_cfg": sim_config,
            "sim_datas": sim_datas,
            "extra_config": extra_config,
            "extra_configs": extra_configs
        }

    if not os.path.exists('./tmp/'):
        try:
            os.makedirs('./tmp/')
        except Exception as e:
            print(f'[ERROR] Make ./tmp folder failed, but not return failure! log: {e}')

    write_json_data(data, f'./tmp/{buildTmpJson}')
    return read_json_data(f'./tmp/{buildTmpJson}')


def set_output_path(board_info):
    compiler = board_info['compiler']
    app_name = board_info['app_name']
    board_name = board_info['board_name']
    if board_info['is_sim_build']:
        sim = '_sim'
    else:
        sim = ''

    board_info["output_path"] = os.path.join(VCOS_ROOT_PATH, "..", "output", \
                                             f'{app_name}_{board_name}_{compiler}{sim}').replace('\\', '/')
    return board_info


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
    board_config = board_info['board_config']
    if board_config.endswith(compiler):
        dst_path = board_config
    else:
        dst_path = f"{board_config}_{compiler}"
        if not os.path.exists(dst_path):
            os.makedirs(dst_path)
        else:
            shutil.rmtree(dst_path)
            os.makedirs(dst_path)
        shutil.copy2(os.path.join(board_config, 'defconfig').replace('\\', '/'), dst_path)
    board_info['board_config'] = dst_path
    extra_config = board_info['extra_configs'].get(compiler, None)
    if extra_config:
        board_info['extra_config'] = extra_config
        for extra_line in extra_config:
            with open(os.path.join(dst_path, 'defconfig').replace('\\', '/'), 'r', encoding='utf-8') as fr:
                content = fr.readlines()
                if extra_line not in content:
                    content += '\n' + extra_line + '\n'
            with open(os.path.join(dst_path, 'defconfig').replace('\\', '/'), 'w', encoding='utf-8') as fw:
                fw.writelines(content)

    set_compiler_path_env(compiler)
    return set_output_path(board_info)


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
            src = os.path.abspath(os.path.join(VCOS_ROOT_PATH, '..', dir["src"])).replace('\\', '/')
            dst = os.path.abspath(os.path.join(VCOS_ROOT_PATH, '..', dir["dst"])).replace('\\', '/')
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
    codegen_boot = os.path.abspath(board_info['codegen_boot'])
    vcosproject_file_path = os.path.abspath(board_info['vcosproject_file_path'])
    os.chdir(board_build_path)

    change_vcosprojects_file(board_info)

    process = subprocess.Popen(
            [sys.executable, "-u", codegen_boot, "-p", vcosproject_file_path, "Generate", "--force"],
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT
        )
    for line in process.stdout:
        try:
            decoded_line = line.decode("utf-8")
        except UnicodeDecodeError:
            decoded_line = line.decode("gbk", errors="replace")
        print(decoded_line, end="")
    process.wait()
    print(f'[{app_name}:{board_name}][codegen] End.')
    if board_info['is_sim_build']:
        sim_defconfig_gen(board_info)
        sim_arxml_adapt(board_info, revert=True)
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


def set_sim_config(board_info):
    board_name = board_info['board_name']
    for sim_data in board_info['sim_datas']:
        if board_name in sim_data['sim_board_config']:
            board_info["sim_arxml_path"] = os.path.abspath(os.path.join(build_path, \
                                        sim_data["sim_arxml_path"])).replace('\\', '/')
            board_info["sim_board_cfg"] = sim_data['sim_board_config']
            board_info["sim_defconfig_gen_path"] = os.path.abspath(os.path.join(build_path, \
                                        sim_data["sim_defconfig_gen_path"])).replace('\\', '/')
            board_info["sim_cfg"] = sim_data["sim_config"]
            board_info['board_config'] = os.path.abspath(os.path.join(VCOS_ROOT_PATH, \
                                        sim_data["sim_config"])).replace('\\', '/')
            break
    sim_defconfig_copy(board_info)
    sim_arxml_adapt(board_info)
    return set_output_path(board_info)


def sim_defconfig_copy(board_info):
    compiler = board_info['compiler']
    if compiler == 'gcc':
        dest_cfg = board_info["board_config"]
    else:
        dest_cfg = board_info["board_config"] + "_" + compiler
    shutil.copy2(
        os.path.join(VCOS_ROOT_PATH, board_info["sim_board_cfg"], 'defconfig'),
        os.path.join(dest_cfg, 'defconfig'))

def sim_defconfig_gen(board_info):
    app_name = board_info['app_name']
    board_name = board_info['board_name']

    sim_defconfig_gen_ret = subprocess.Popen(
            [sys.executable, board_info["sim_defconfig_gen_path"],
             "-s", board_info["board_config"], "-d", board_info["board_config"], "-i", board_info['vcosproject_file_path']],
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT
        )
    for line in sim_defconfig_gen_ret.stdout:
        try:
            decoded_line = line.decode("utf-8")
        except UnicodeDecodeError:
            decoded_line = line.decode("gbk", errors="replace")
        print(decoded_line, end="")
    sim_defconfig_gen_ret.wait()
    if sim_defconfig_gen_ret.returncode:
        print(f'[{app_name}:{board_name}] ret.stdout: {sim_defconfig_gen_ret.stdout}')
        print(f'[{app_name}:{board_name}] ret.stderr: {sim_defconfig_gen_ret.stderr}')
        error(log = f'Step sim_defconfig_gen failed, borard info: {board_info}')

def sim_arxml_adapt(board_info, revert=False):
    app_name = board_info['app_name']
    board_name = board_info['board_name']
    vcosproject_file_path = board_info['vcosproject_file_path']
    if revert:
        sim_arxml_path_ret = subprocess.Popen(
                [sys.executable, board_info["sim_arxml_path"], "-m", vcosproject_file_path, "-r"],
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT
            )
    else:
        sim_arxml_path_ret = subprocess.Popen(
                [sys.executable, board_info["sim_arxml_path"], "-m", vcosproject_file_path],
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT
            )
    for line in sim_arxml_path_ret.stdout:
        try:
            decoded_line = line.decode("utf-8")
        except UnicodeDecodeError:
            decoded_line = line.decode("gbk", errors="replace")
        print(decoded_line, end="")
    sim_arxml_path_ret.wait()
    if sim_arxml_path_ret.returncode:
        print(f'[{app_name}:{board_name}] ret.stdout: {sim_arxml_path_ret.stdout}')
        print(f'[{app_name}:{board_name}] ret.stderr: {sim_arxml_path_ret.stderr}')
        error(log = f'Step sim_arxml_adapt failed, borard info: {board_info}')


def gendate_cmake(board_info):
    compiler = board_info['compiler']
    set_compiler_path_env(compiler)
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
            toolchain = os.path.join(toolchain_path, "ninja.exe").replace('\\', '/')
            gendate_cmake_cmd = f'cmake -B {output_path} -DBOARD_CONFIG={board_config} -DAPPS_DIR={apps_dir} \
                    -G \"{maketool}\" -DWIN32=1 -DCMAKE_MAKE_PROGRAM=\"{toolchain}\"'
        elif maketool == "MinGW Makefiles":
            toolchain = os.path.join(toolchain_path, "make.exe").replace('\\', '/')
            gendate_cmake_cmd = f'cmake -B {output_path} -DBOARD_CONFIG={board_config} -DAPPS_DIR={apps_dir} \
                    -G \"{maketool}\" -DWIN32=1 -DCMAKE_MAKE_PROGRAM=\"{toolchain}\"'
        else:
            gendate_cmake_cmd = 'echo "[ERROR][gendate_cmake] Not support maketool type!"'
    elif cur_platfm == 'linux':
        if compiler == 'gcc':
            gendate_cmake_cmd = f'cmake -B {output_path} -DBOARD_CONFIG={board_config} -DAPPS_DIR={apps_dir} \
                -G \"{maketool}\"'
        else:
            gendate_cmake_cmd = f'cmake -B {output_path} -DBOARD_CONFIG={board_config} -DAPPS_DIR={apps_dir}'
    else:
        gendate_cmake_cmd = 'echo "[ERROR][gendate_cmake] Not support platform!"'
    if "tests/examples" not in apps_dir:
        gendate_cmake_cmd += f' -DBOARD_NAME={board_name}'
    print(f'[{app_name}:{board_name}] gendate_cmake: {gendate_cmake_cmd}')
    gendate_cmake_ret = subprocess.Popen(
            args = gendate_cmake_cmd,
            shell = True,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT
        )
    for line in gendate_cmake_ret.stdout:
        try:
            decoded_line = line.decode("utf-8")
        except UnicodeDecodeError:
            decoded_line = line.decode("gbk", errors="replace")
        print(decoded_line, end="")
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
            stderr = subprocess.STDOUT
        )
    for line in build_ret.stdout:
        try:
            decoded_line = line.decode("utf-8")
        except UnicodeDecodeError:
            decoded_line = line.decode("gbk", errors="replace")
        print(decoded_line, end="")
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
    elf_file = os.path.join(output_path, "nuttx.elf").replace('\\', '/')
    nuttx_file = os.path.join(output_path, "nuttx").replace('\\', '/')
    if os.path.exists(elf_file):
        print(f"# successful generate {app_name}.elf")
    elif os.path.exists(nuttx_file):
        print(f"# successful generate {app_name}")
    else:
        error(f"# failed to generate {app_name}.elf")
    for file in os.listdir(output_path):
        if "nuttx" in file:
            os.rename(os.path.join(output_path, file).replace('\\', '/'), \
                      os.path.join(output_path, app_name + file.split('nuttx')[1]).replace('\\', '/'))


def pre_process(apps_dir):
    symlink_dirs()


def run_board_build(board_info):
    board_name = board_info['board_name']
    app_name = board_info['app_name']
    apps_dir = board_info['apps_dir']
    mode = board_info['build_mode']
    sim = board_info['is_sim_build']
    maketool = board_info['maketool']
    compiler = board_info['compiler']
    pre_process(apps_dir)

    if 'clean' in board_info["build_action"]:
        run_clean(board_info)
    elif 'codegen' in board_info["build_action"]:
        run_codegen(board_info)
    elif '_compile' in board_info["build_action"]:
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
    board_info = choice_board(args.app_name, args.board_name, args.compiler, args.update)
    if args.board_name and args.app_name:
        board_info["build_action"] = 'select_board'
    if args.mode:
        board_info["build_mode"] = args.mode
        board_info["build_action"] = 'mode'
    if args.sim:
        board_info["is_sim_build"] = args.sim
        board_info["build_action"] = 'sim'
        board_info = set_sim_config(board_info)
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
    file = f'{app_name.replace("/", "_")}_{board_name}_build_temp.json'
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
            [python_path, "-u"] + sys.argv,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            env=environ
        )
        for line in process.stdout:
            try:
                decoded_line = line.decode("utf-8")
            except UnicodeDecodeError:
                decoded_line = line.decode("gbk", errors="replace")
            print(decoded_line, end="")
        process.wait()
