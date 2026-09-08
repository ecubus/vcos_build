# vcos_build代码仓库说明

## 1. 代码仓库简介

智能车控OS（VCOS）编译框架支持多种芯片平台、多种编译器以及跨系统环境，为做到更好的兼容性，我们选择了python + json的方式

多芯片demo编译统一编译入口到python脚本，python中主要实现了编译框架适配，逻辑清晰，简约明了，且编译命令一致无需区分Windows和Linux。而json文件中则存放不同芯片demo的差异信息，用以给python编译框架提供编译流程中的差异信息

编译器选择上，我们根据不同的芯片demo，支持不同的编译器种类，例如TriCore相关芯片支持GCC和tasking、芯驰E3650支持GCC和GHS（Green Hills）等，鉴于开源后方便大家集成调试，我们默认使用免费的GCC编译器

## 2. 代码目录

vcos_build 源代码在 haloosspace/vcos/build 目录下，目录结构如下图所示

```bash
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
python vcos_build.py -h
```

**编译参数：**

```bash
lixiang:~/vcos/buid$ python vcos_build.py -h
usage: vcos_build.py [-h] -app_name
                     {multicore_com_demo,diag_demo,nm_demo,rt_demo,vbslite_demo/vbslite_node1,tsyn_demo,vbslite_demo/vbslite_node2,mempool_demo,isolate_demo}
                     -board_name
                     {a2g_tc397_5v_tft,e3650_dev_kit,fc7300f8mdt_evb}
                     [-compiler {gcc,ghs,tasking,arm,HighTec}]
                     [-mode {release,debug}] [-sim {0,1}] [-update] [-clean]
                     [-maketool {make,ninja}] [-codegen] [-gcmake] [-fc] [-ic]
                     [-all]

VCOS Build

optional arguments:
  -h, --help            show this help message and exit
  -app_name {multicore_com_demo,diag_demo,nm_demo,rt_demo,vbslite_demo/vbslite_node1,tsyn_demo,vbslite_demo/vbslite_node2,mempool_demo,isolate_demo}
                        application name, find from ./vcos/examples/
  -board_name {a2g_tc397_5v_tft,e3650_dev_kit,fc7300f8mdt_evb}
                        support board list, with app: ['rt_demo:a2g_tc397_5v_tft', 'rt_demo:e3650_dev_kit', 'vbslite_demo/vbslite_node1:a2g_tc397_5v_tft', 'vbslite_demo/vbslite_node1:e3650_dev_kit', 'vbslite_demo/vbslite_node2:a2g_tc397_5v_tft', 'vbslite_demo/vbslite_node2:e3650_dev_kit', 'multicore_com_demo:a2g_tc397_5v_tft', 'multicore_com_demo:e3650_dev_kit', 'multicore_com_demo:fc7300f8mdt_evb', 'nm_demo:e3650_dev_kit', 'tsyn_demo:e3650_dev_kit', 'isolate_demo:a2g_tc397_5v_tft', 'isolate_demo:e3650_dev_kit', 'diag_demo:e3650_dev_kit', 'mempool_demo:a2g_tc397_5v_tft']
  -compiler {gcc,ghs,tasking,arm,HighTec}
                        Compiler type
  -mode {release,debug}
                        build config mode, include testcases or not
  -sim {0,1}            is sim build
  -update               update build config json file
  -clean                clean output path
  -maketool {make,ninja}
                        select make tool, default is [make]
  -codegen              dynamic code generation
  -gcmake               gendate cmake config
  -fc                   full compilation
  -ic                   incremental compilation
  -all                  all compilation steps, include '-codegen'、'-gcmake'、'-fc'
```

> 提示：各 app 与 board 匹配使用不尽相同，另外对模拟器支持情况也有差异，详情见下表
>
> |app_name|board_name|sim|
> |---|---|---|
> |rt_demo|a2g_tc397_5v_tft|yes|
> |rt_demo|e3650_dev_kit|yes|
> |vbslite_demo/vbslite_node1|a2g_tc397_5v_tft|yes|
> |vbslite_demo/vbslite_node1|e3650_dev_kit|yes|
> |vbslite_demo/vbslite_node2|a2g_tc397_5v_tft|yes|
> |vbslite_demo/vbslite_node2|e3650_dev_kit|yes|
> |isolate_demo|a2g_tc397_5v_tft|no|
> |isolate_demo|e3650_dev_kit|no|
> |nm_demo|e3650_dev_kit|no|
> |multicore_com_demo|a2g_tc397_5v_tft|no|
> |multicore_com_demo|e3650_dev_kit|yes|
> |multicore_com_demo|fc7300f8mdt_evb|no|
> |tsyn_demo|e3650_dev_kit|no|
> |diag_demo|e3650_dev_kit|no|
> |mempool_demo|a2g_tc397_5v_tft|no|

**编译步骤：**

```bash
## 拆分各步骤进行编译 ##
# 选项数据配置，可以在一条命令中配置多项数据
python vcos_build.py -app_name xx -board_name xx -compiler gcc     # 选择工程和编译器，生成 ./tmp/**_temp.json 保存编译信息
python vcos_build.py -app_name xx -board_name xx -sim [0 | 1]      # 选择sim工程，0：非sim编译，1：sim编译
python vcos_build.py -app_name xx -board_name xx -maketool xx      # 指定make toochain工具，[make | ninja]
python vcos_build.py -app_name xx -board_name xx -update           # 强制更新 ./tmp/**_temp.json 中数据内容
# 根据上述配置数据，进行编译
python vcos_build.py -app_name xx -board_name xx -clean            # clean output
python vcos_build.py -app_name xx -board_name xx -codegen          # 动态代码生成，等同于UI界面操作生成代码。如已通过UI操作代码生成，可跳过此命令
python vcos_build.py -app_name xx -board_name xx -gcmake           # 生成 cmake 编译依赖配置
python vcos_build.py -app_name xx -board_name xx -fc               # 全量编译生成所需二进制镜像文件
python vcos_build.py -app_name xx -board_name xx -ic               # 增量编译生成所需二进制镜像文件
```

```bash
## 合并各步骤，一行命令进行编译 ##
python vcos_build.py -app_name xx -board_name xx -compiler gcc -sim [0 | 1] -maketool xx -all   # 仅支持全量
```

> 提示：
> `vcos_build.py` 脚本在编译时会在同目录下生成一个名为 `./tmp/{app_name}_{board_name}_build_temp.json` 的临时json文件，该文件中存放对应app+board编译步骤信息，如多次编译同一个app时出现报错，可以删除此json文件，或者增加 -update 参数来强制更新json文件内容

**编译结果：**

```bash
haloosspace
└── output
```
