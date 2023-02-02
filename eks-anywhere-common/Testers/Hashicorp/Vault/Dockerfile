FROM ubuntu:22.04

ARG VAULT_VERSION=1.12.2

RUN apt-get update \
 && apt-get install wget curl jq unzip -y \
 && wget https://releases.hashicorp.com/vault/${VAULT_VERSION}/vault_${VAULT_VERSION}_linux_amd64.zip \
 && unzip vault_${VAULT_VERSION}_linux_amd64.zip \
 && mv vault /usr/local/bin/

RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl \
 && chmod +x ./kubectl \
 && mv ./kubectl /usr/local/bin