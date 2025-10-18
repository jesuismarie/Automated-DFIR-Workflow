FROM python:3.11-slim-bookworm

ARG USER=analyzer
ARG UID=1000
ARG GID=1000

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	&& rm -rf /var/lib/apt/lists/*

RUN groupadd -g ${GID} ${USER} || true \
	&& useradd -m -u ${UID} -g ${GID} -s /bin/bash ${USER} || true

RUN mkdir -p /analysis/processed /analysis/yara_rules /analysis/analyzers \
	&& chown -R ${USER}:${USER} /analysis

WORKDIR /analysis

COPY analyzers /analysis/analyzers
COPY sandbox/entrypoint.sh /analysis/entrypoint.sh
COPY sandbox/requirements.txt /analysis/requirements.txt

RUN pip install --no-cache-dir -r /analysis/requirements.txt

RUN chmod +x /analysis/entrypoint.sh

USER ${USER}

ENTRYPOINT ["/analysis/entrypoint.sh"]
