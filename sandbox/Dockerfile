FROM python:3.11-ubuntu

ARG USER=analyzer
ARG UID=1000
ARG GID=1000

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	automake \
	libtool \
	pkg-config \
	git \
	ca-certificates \
	python3-dev \
	libssl-dev \
	libffi-dev \
	libyara-dev \
	yara \
	pip \
	file \
	&& rm -rf /var/lib/apt/lists/*
	
RUN mkdir -p /analysis/processed /analysis/yara_rules \
	&& chown -R ${USER}:${USER} /analysis

RUN groupadd -g ${GID} ${USER} || true \
	&& useradd -m -u ${UID} -g ${GID} -s /bin/bash ${USER} \
	&& mkdir -p /analysis/input /analysis/static-output /analysis/dynamic-output \
	&& chown -R ${USER}:${USER} /analysis /queue /static-output /dynamic-output

WORKDIR /analysis

COPY ../analyzers /analysis/analyzers
COPY entrypoint.sh /analysis/entrypoint.sh
COPY requirements.txt /analysis/requirements.txt

RUN pip install --no-cache-dir -r /analysis/requirements.txt

RUN chmod +x /analysis/entrypoint.sh

USER ${USER}

ENTRYPOINT ["/analysis/entrypoint.sh"]
