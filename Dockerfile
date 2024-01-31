FROM python:3.11.3-slim

ARG WORKDIR=/opt/cv_builder

ENV RUNNING_IN_DOCKER=1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=${WORKDIR}
ENV CONTAINER_GIT_COMMIT=${GIT_COMMIT}

RUN apt update && \
    apt install -y bash git vim curl htop tmux unzip nano ca-certificates wget sudo && \
    apt autoremove -y && \
    apt clean && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt ${WORKDIR}/requirements.txt
RUN python3 -m pip install --upgrade pip && \
    ln -sf /usr/bin/pip3 /usr/bin/pip && \
    ln -sf /usr/bin/python3 /usr/bin/python
RUN pip install -r ${WORKDIR}/requirements.txt

# create a non-root user (see https://github.com/moby/moby/issues/5419#issuecomment-41478290 and https://github.com/facebookresearch/detectron2/blob/main/docker/Dockerfile)
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN useradd -m --no-log-init --system  --uid ${USER_ID} developer -g sudo \
    && groupadd -g ${GROUP_ID} developer
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

COPY . ${WORKDIR}
WORKDIR ${WORKDIR}

USER developer
ENV PATH="/home/developer/.local/bin:${PATH}"
ENV HOME=/home/developer
