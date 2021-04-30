FROM python:alpine

LABEL maintainer="Nick [linickx.com]"
LABEL version="0.1"

COPY ./simplenote_sync /root/simplenote_sync
COPY ./snsync /root/snsync

ENTRYPOINT ["/root/snsync"]
