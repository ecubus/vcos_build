FROM ubuntu:focal

ENV DEBIAN_FRONTEND=noninteractive

RUN sed -i 's|archive.ubuntu.com|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list && \
	sed -i 's|security.ubuntu.com|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list

RUN apt-get update && \
	apt-get install -y --no-install-recommends \
	python3.8 \
	python3.8-venv \
	python3.8-dev \
	python3-pip \
	build-essential \
	gcc \
	libc6-dev \
	socat \
	can-utils \
	kmod \
	iproute2 \
	tcpdump \
	wireshark \
	git \
	vim \
	gdb \
	minicom \
	iputils-ping \
	&& \
	ln -sf /usr/bin/python3.8 /usr/bin/python3 && \
	ln -sf /usr/bin/python3.8 /usr/bin/python && \
	ln -sf /usr/bin/pip3 /usr/bin/pip && \
	rm -rf /var/lib/apt/lists/*

ENV Python3_EXECUTABLE=/usr/bin/python3.8 \
	Python3_ROOT_DIR=/usr

RUN git config --global --add safe.directory "*"

WORKDIR /home
ENV INTERACTOR=/dev/vttyM0

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
