FROM ubuntu:16.04
MAINTAINER Rodrigo Pinheiro Matias

RUN locale-gen pt_BR.UTF-8

ENV DEBIAN_FRONTEND=nointeractive \
    LANG=pt-BR.UTF-8 \
    LANGUAGE=pt_BR.UTF-8 \
    LC_ALL=pt_BR.UTF-8

RUN apt-get update && \
    apt-get install python3-minimal python3-dev python-virtualenv build-essential nano -y && \
    apt-get autoremove -y && \
    apt-get autoclean -y && \
    useradd -m -s /bin/bash user

VOLUME /app

EXPOSE 8000

COPY ["busybox.py", "/bin/busybox"]
ENTRYPOINT ["/bin/busybox"]

RUN chmod +x /bin/busybox

CMD ["shell"]
