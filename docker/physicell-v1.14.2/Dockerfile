FROM ubuntu:22.04

ARG PHYSICELL_VERSION=1.14.2
ARG PHYSICELL_TAG=1.14.2
ARG PHYSICELL_TARBALL_URL=https://github.com/MathCancer/PhysiCell/archive/refs/tags/${PHYSICELL_TAG}.tar.gz

LABEL org.opencontainers.image.title="CLONEID PhysiCell backend"
LABEL org.opencontainers.image.version="${PHYSICELL_VERSION}"
LABEL org.opencontainers.image.source="https://github.com/MathCancer/PhysiCell/releases/tag/1.14.2"

ENV DEBIAN_FRONTEND=noninteractive
ENV PHYSICELL_ROOT=/opt/PhysiCell-${PHYSICELL_VERSION}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        make \
        python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN curl -L "${PHYSICELL_TARBALL_URL}" -o physicell.tar.gz \
    && tar -xzf physicell.tar.gz \
    && rm physicell.tar.gz \
    && mv PhysiCell-${PHYSICELL_TAG} "${PHYSICELL_ROOT}"

WORKDIR ${PHYSICELL_ROOT}

RUN make

CMD ["/bin/bash"]
