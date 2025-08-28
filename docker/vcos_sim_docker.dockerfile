FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN dpkg --add-architecture i386

RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && sed -i 's/security.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    socat \
    can-utils \
    kmod \
    iproute2 \
    net-tools \
    tcpdump \
    wireshark \
    tshark \
    iputils-ping \
    git \
    vim \
    gdb \
    minicom \
    util-linux \
    hwloc \
    numactl \
    htop \
    iperf \
    procps \
    libc6:i386 \
    libstdc++6:i386 \
    libgcc-s1:i386 \
    libc6-dev-i386 \
    lib32z1 \
    lib32ncurses6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home
ENV SHELL__PORT=/dev/vttyM0

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
