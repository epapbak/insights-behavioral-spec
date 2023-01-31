FROM registry.access.redhat.com/ubi8/ubi:latest

ENV VENV=/insights-behavioral-spec-venv \
    VENV_BIN=/insights-behavioral-spec-venv/bin \
    HOME=/insights-behavioral-spec \
    REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt \
    NOVENV=0 \
    ENV_DOCKER=1 \
    DB_NAME=test \
    DB_HOST=database \
    DB_PORT=5432 \
    DB_USER=postgres \
    DB_PASS=postgres \
    DB_PARAMS="sslmode=disable" \
    KAFKA_HOST=kafka \
    KAFKA_PORT=9092 \
    S3_TYPE=minio \
    S3_HOST=minio \
    S3_PORT=9000 \
    S3_ACCESS_KEY=test_access_key \
    S3_SECRET_ACCESS_KEY=test_secret_access_key \
    S3_BUCKET=test \
    S3_USE_SSL=false

WORKDIR $HOME

COPY . $HOME

ENV PATH="$VENV/bin:$PATH"
RUN dnf copr enable -y bvn13/kcat epel-9-x86_64 && dnf update -y && dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm && rpm --import https://packages.confluent.io/rpm/7.3/archive.key && dnf update -y &&  echo -e '[Confluent]\nname=Confluent repository\nbaseurl=https://packages.confluent.io/rpm/7.3\ngpgcheck=1\ngpgkey=https://packages.confluent.io/rpm/7.3/archive.key\nenabled=1\n\n[Confluent-Clients]\nname=Confluent Clients repository\nbaseurl=https://packages.confluent.io/clients/rpm/centos/$releasever/$basearch\ngpgcheck=1\ngpgkey=https://packages.confluent.io/clients/rpm/archive.key\nenabled=1' > /etc/yum.repos.d/confluent.repo && dnf update -y && dnf install -y kafkacat
RUN dnf install --nodocs -y python3-pip unzip make && \
    python3 -m venv $VENV && \
    curl -ksL https://password.corp.redhat.com/RH-IT-Root-CA.crt \
         -o /etc/pki/ca-trust/source/anchors/RH-IT-Root-CA.crt && \
    update-ca-trust && \
    pip install --no-cache-dir -U pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    dnf clean all && \
    chmod -R g=u $HOME $VENV /etc/passwd && \
    chgrp -R 0 $HOME $VENV

USER 1001

CMD ["sh", "-c", "make $TESTS_TO_EXECUTE"]
