FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV FIJI_EXECUTABLE=/opt/Fiji.app/ImageJ-linux64
ENV FIJI_HEADLESS=true

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-venv \
    openjdk-8-jre \
    wget \
    unzip \
    ca-certificates \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN python3.11 -m pip install --upgrade pip

COPY service/requirements.txt /tmp/requirements.txt
RUN python3.11 -m pip install -r /tmp/requirements.txt

# Fiji 20220414-1745 is the known-good Linux build for this project.
RUN wget -O /tmp/fiji.zip https://downloads.imagej.net/fiji/archive/20220414-1745/fiji-linux64.zip \
    && unzip /tmp/fiji.zip -d /opt \
    && rm /tmp/fiji.zip

COPY . /workspace

RUN chmod +x /workspace/docker/demo/start-demo.sh

EXPOSE 8000

CMD ["/workspace/docker/demo/start-demo.sh"]
