#!/bin/sh
set -e

# 检查是否以 root 用户运行
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: 必须使用 root 权限运行容器！请添加 '--user root' 参数。" >&2
    exit 1
fi

# 日志输出函数
log_info() {
    echo "[INFO] \$1" >&2
}

# 检查CPU配置
log_info "检查CPU配置..."
log_info "可用CPU核心: $(nproc)"
log_info "CPU亲和性掩码: $(taskset -p $$ | awk '{print $NF}')"

# 检查实时调度权限
if chrt -r 50 echo "RT test" >/dev/null 2>&1; then
    log_info "实时调度权限: 已启用"
else
    echo "WARN: 实时调度权限受限，请使用 --cap-add=SYS_NICE 运行容器" >&2
fi

# 网络配置
log_info "配置网络设备..."
if ! ip link show br0 >/dev/null 2>&1; then
    log_info "创建网桥 br0..."
    if ! ip link add name br0 type bridge; then
        echo "ERROR: 创建网桥 br0 失败，请检查权限( 需 --cap-add=NET_ADMIN )" >&2
        exit 1
    fi
    ip link set br0 up
    ip addr add 192.168.10.254/24 dev br0
    bridge vlan add dev br0 vid 3 self
    ip link add link br0 name br0.3 type vlan id 3
    ip link set br0.3 up
    ip addr add 192.168.3.254/24 dev br0.3
    ip link set dev br0 type bridge vlan_filtering 1
fi

# 加载 vcan 模块
log_info "加载 vcan 模块..."
if ! lsmod | grep -q vcan; then
    if ! modprobe vcan; then
        echo "ERROR: 加载 vcan 模块失败，
        请手动执行 'echo "vcan" | sudo tee -a /etc/modules' 加载 vcan 模块" >&2
    fi
fi

# 创建 vcan 设备
log_info "创建 vcan 设备..."
for i in 0 1 2 3 4 5 6 7 8 9; do
    if ! ip link show vcan$i >/dev/null 2>&1; then
        if ! ip link add dev vcan$i type vcan; then
            echo "WARN: 创建 vcan$i 失败" >&2
        else
            ip link set up vcan$i
        fi
    fi
done

# 创建虚拟串口
log_info "创建虚拟串口..."
socat -d -d PTY,link=/dev/vttyS0,raw,echo=0 PTY,link=/dev/vttyM0,raw,echo=0 &
socat -d -d PTY,link=/dev/vttyS1,raw,echo=0 PTY,link=/dev/vttyM1,raw,echo=0 &

# 等待所有后台任务完成
wait

# 保持容器运行
log_info "容器已启动，等待操作..."
exec tail -f /dev/null