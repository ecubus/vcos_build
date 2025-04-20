# vcos_build代码仓库说明

## 1. 代码仓库简介
智能车控OS（VCOS）编译框架支持多种芯片平台、多种编译器以及跨系统环境，为做到更好的兼容性，我们选择了python + json的方式

多芯片demo编译统一编译入口到python脚本，python中主要实现了编译框架适配，逻辑清晰，简约明了，且编译命令一致无需区分Windows和Linux。而json文件中则存放不同芯片demo的差异信息，用以给python编译框架提供编译流程中的差异信息

编译器选择上，我们根据不同的芯片demo，支持不同的编译器种类，例如tricore相关芯片支持GCC和tasking、芯驰E3650支持GCC和GHS（Green Hills）等，鉴于开源后方便大家集成调试，我们默认使用免费的GCC编译器

## 2. 代码目录
vcos_build 源代码在 haloosspace/vcos/build 目录下，目录结构如下图所示
```
haloosspace
└── vcos                     # 智能车控OS
    └── build                # 智能车控OS编译入口目录
        ├── build_conf.json  # 各芯片demo信息
        └── vcos_build.py    # 编译脚本
```

## 3. 仓库使用入门

**编译脚本：**
```bash
cd ./vcos/build
python3 vcos_build.py -h
```
**编译参数：**
```bash
lixiang:~/vcos/buid$ python3 vcos_build.py -h
usage: vcos_build.py [-h] [-board_name {A2G_TC397_5V_TFT,E3650_DEV_KIT}] [-app_name APP_NAME] [-sim {0,1}] [-compiler {gcc,ghs,tasking}] [-mode {release,debug}] [-maketool {make,ninja}] [-update] [-clean] [-codegen] [-gcmake] [-fc] [-ic] [-all]

VCOS Build

optional arguments:
  -h, --help            show this help message and exit
  -board_name {A2G_TC397_5V_TFT,E3650_DEV_KIT}
                        ['A2G_TC397_5V_TFT', 'E3650_DEV_KIT']
  -app_name APP_NAME    application name, find from ./vcos/examples/
  -sim {0,1}            is sim build
  -compiler {gcc,ghs,tasking}
                        compiler type
  -mode {release,debug}
                        build config mode, include testcases or not
  -maketool {make,ninja}
                        select make tool, default is [make]
  -update               update build config json file
  -clean                clean output path
  -codegen              dynamic code generation
  -gcmake               gendate cmake config
  -fc                   full compilation
  -ic                   incremental compilation
  -all                  all compilation steps, include '-codegen'、'-gcmake'、'-fc'
```
**编译步骤：**
```bash
## 拆分各步骤进行编译 ##
# 选项数据配置，可以在一条命令中配置多项数据
python3 vcos_build.py -app_name xx -borad_name xx -compiler gcc     # 选择工程和编译器，生成 ./tmp/**_temp.json 保存编译信息
python3 vcos_build.py -app_name xx -borad_name xx -sim [0 | 1]      # 选择sim工程，0：非sim编译，1：sim编译
python3 vcos_build.py -app_name xx -borad_name xx -maketool xx      # 指定make toochain工具，[make | ninja]
# 根据上述配置数据，进行编译
python3 vcos_build.py -app_name xx -borad_name xx -clean            # clean output
python3 vcos_build.py -app_name xx -borad_name xx -codegen          # 动态代码生成
python3 vcos_build.py -app_name xx -borad_name xx -gcmake           # 生成 cmake 编译依赖配置
python3 vcos_build.py -app_name xx -borad_name xx -fc               # 全量编译生成所需二进制镜像文件
python3 vcos_build.py -app_name xx -borad_name xx -ic               # 增量编译生成所需二进制镜像文件
```
```bash
## 合并各步骤，一行命令进行编译 ##
python3 vcos_build.py -app_name xx -borad_name xx -C gcc -sim [0 | 1] -maketool xx -all   # 仅支持全量
```

