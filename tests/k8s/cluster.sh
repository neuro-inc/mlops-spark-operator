#!/usr/bin/env bash

# based on
# https://github.com/kubernetes/minikube#linux-continuous-integration-without-vm-support

function k8s::install_kubectl {
    local kubectl_version=$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)
    curl -Lo kubectl https://storage.googleapis.com/kubernetes-release/release/${kubectl_version}/bin/linux/amd64/kubectl
    chmod +x kubectl
    sudo mv kubectl /usr/local/bin/
}

function k8s::install_minikube {
    local minikube_version="v1.25.2"
    sudo apt-get update
    sudo apt-get install -y conntrack
    curl -Lo minikube https://storage.googleapis.com/minikube/releases/${minikube_version}/minikube-linux-amd64
    chmod +x minikube
    sudo mv minikube /usr/local/bin/
    sudo -E minikube config set WantReportErrorPrompt false
    sudo -E minikube config set WantNoneDriverWarning false
}

function k8s::start {
    export KUBECONFIG=$HOME/.kube/config
    mkdir -p $(dirname $KUBECONFIG)
    touch $KUBECONFIG

    export MINIKUBE_WANTUPDATENOTIFICATION=false
    export MINIKUBE_WANTREPORTERRORPROMPT=false
    export MINIKUBE_HOME=$HOME
    export CHANGE_MINIKUBE_NONE_USER=true

    sudo -E minikube start \
        --install-addons=true \
        --addons=registry \
        --wait=all \
        --wait-timeout=5m
}

function k8s::stop {
    sudo -E minikube stop || :
    sudo -E minikube delete || :
    sudo -E rm -rf ~/.minikube
    sudo rm -rf /root/.minikube
}

case "${1:-}" in
    install)
        k8s::install_kubectl
        k8s::install_minikube
        ;;
    start)
        k8s::start
        ;;
    stop)
        k8s::stop
        ;;
esac
