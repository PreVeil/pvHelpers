FROM ubuntu:16.04


RUN apt-get update \
    && apt-get install -y \
      python2.7 \
      python-pip \
      libsodium-dev \
    && pip install --upgrade pip \
      setuptools \
      tox

RUN addgroup --gid 111 builder && \
    adduser --uid 111 \
            --disabled-password \
            --home /home/builder \
            --gid 111 builder

WORKDIR /home/builder
RUN mkdir pvHelpers
COPY . pvHelpers

RUN chown -R builder:builder .

USER builder

WORKDIR /home/builder/pvHelpers

CMD ["python", "setup.py", "sdist"]