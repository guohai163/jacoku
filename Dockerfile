FROM ubuntu:jammy

LABEL org.opencontainers.image.authors="GUOHAI.ORG"
LABEL org.opencontainers.image.source=https://github.com/guohai163/jacoco-report
ENV VERSION_STRING=5:27.3.0-1~ubuntu.22.04~jammy

# 基础功能安装
RUN set -eux && \
    apt-get update -y && \
    apt-get install -y gzip tar curl ca-certificates iputils-tracepath dnsutils vim htop gpg cron pip && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

    RUN curl -OL https://dlcdn.apache.org/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz && \
    tar -zxvf apache-maven-3.9.9-bin.tar.gz && \
    rm -rf apache-maven-3.9.9-bin.tar.gz && \
    ln -sf /opt/apache-maven-3.9.9 /opt/maven && \
    curl -OL https://cdn.azul.com/zulu/bin/zulu11.78.15-ca-jdk11.0.26-linux_x64.tar.gz && \
    tar -zxvf zulu11.78.15-ca-jdk11.0.26-linux_x64.tar.gz && \
    rm -rf zulu11.78.15-ca-jdk11.0.26-linux_x64.tar.gz && \
    ln -sf /opt/zulu11.78.15-ca-jdk11.0.26-linux_x64 /opt/jdk11 && \
    curl -OL https://cdn.azul.com/zulu/bin/zulu17.54.21-ca-jdk17.0.13-linux_x64.tar.gz && \
    tar -zxvf zulu17.54.21-ca-jdk17.0.13-linux_x64.tar.gz && \
    rm -rf zulu17.54.21-ca-jdk17.0.13-linux_x64.tar.gz && \
    ln -sf /opt/zulu17.54.21-ca-jdk17.0.13-linux_x64 /opt/jdk17 && \
    curl -OL https://cdn.azul.com/zulu/bin/zulu21.38.21-ca-jdk21.0.5-linux_x64.tar.gz && \
    tar -zxvf zulu21.38.21-ca-jdk21.0.5-linux_x64.tar.gz && \
    rm -rf zulu21.38.21-ca-jdk21.0.5-linux_x64.tar.gz && \
    ln -sf /opt/zulu21.38.21-ca-jdk21.0.5-linux_x64 /opt/jdk21 && \
    curl -OL https://repo1.maven.org/maven2/org/jacoco/org.jacoco.cli/0.8.12/org.jacoco.cli-0.8.12-nodeps.jar

WORKDIR /opt/jacoco-data/
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY cron.py .
COPY main.py .

CMD ["cron && python3 /opt/jacoco-data/cron.py"]