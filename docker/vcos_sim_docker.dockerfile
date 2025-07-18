FROM debian:bullseye-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list \
	&& apt-get update \
	&& apt-get install -y --no-install-recommends \
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
	iputils-ping \
	git \
	vim \
	gdb \
	minicom \
	util-linux \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /home
ENV SHELL__PORT=/dev/vttyM0

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
