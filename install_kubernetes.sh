#!/bin/bash

# Передача параметров скрипту
CP_ADDRESSES=$1
WORKER_ADDRESSES=$2
K8S_VERSION=$3
OS=$4

# Определение параметров в зависимости от операционной системы
if [ "$OS" == "CentOS" ]; then
    KUBE_PACKAGES=(kubelet-$K8S_VERSION kubeadm-$K8S_VERSION kubectl-$K8S_VERSION docker-ce epel-release haproxy keepalived)
    FIREWALL_CMD="systemctl stop firewalld && systemctl disable firewalld"
    SELINUX_CMD="setenforce 0 && sed -i 's/^SELINUX=enforcing$/SELINUX=permissive/g' /etc/selinux/config"
    K8S_REPO_FILE="/etc/yum.repos.d/kubernetes.repo"
    K8S_REPO_CONTENT="[kubernetes]\nname=Kubernetes\nbaseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64\nenabled=1\ngpgcheck=1\nrepo_gpgcheck=1\ngpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg"
elif [ "$OS" == "Ubuntu" ]; then
    KUBE_PACKAGES=(kubelet=$K8S_VERSION kubeadm=$K8S_VERSION kubectl=$K8S_VERSION docker.io haproxy keepalived)
    FIREWALL_CMD="ufw disable"
    SELINUX_CMD=""
    K8S_REPO_FILE="/etc/apt/sources.list.d/kubernetes.list"
    K8S_REPO_CONTENT="deb https://apt.kubernetes.io/ kubernetes-xenial main"
    K8S_REPO_KEY_URL="https://packages.cloud.google.com/apt/doc/apt-key.gpg"
    K8S_REPO_KEY_CMD="curl -s $K8S_REPO_KEY_URL | sudo apt-key add -"
elif [ "$OS" == "Debian" ]; then
    KUBE_PACKAGES=(kubelet=$K8S_VERSION kubeadm=$K8S_VERSION kubectl=$K8S_VERSION docker-ce haproxy keepalived)
    FIREWALL_CMD="systemctl stop ufw && systemctl disable ufw"
    SELINUX_CMD=""
    K8S_REPO_FILE="/etc/apt/sources.list.d/kubernetes.list"
    K8S_REPO_CONTENT="deb https://apt.kubernetes.io/ kubernetes-xenial main"
    K8S_REPO_KEY_URL="https://packages.cloud.google.com/apt/doc/apt-key.gpg"
    K8S_REPO_KEY_CMD="curl -s $K8S_REPO_KEY_URL | sudo apt-key add -"
else
    echo "Неизвестная операционная система"
    exit 1
fi

# Установка репозитория Kubernetes
if [ "$OS" == "CentOS" ]; then
    echo -e $K8S_REPO_CONTENT | sudo tee $K8S_REPO_FILE > /dev/null
    sudo yum install -y $KUBE_PACKAGES
else
    echo $K8S_REPO_CONTENT | sudo tee $K8S_REPO_FILE > /dev/null
    $K8S_REPO_KEY_CMD
    sudo apt-get update -y
fi

# Установка пакетов для control-plane узлов
for ADDRESS in $CP_ADDRESSES; do
    echo "Установка пакетов на $ADDRESS"

    # Отключение SELinux и Firewall
    ssh root@$ADDRESS "$SELINUX_CMD"
    ssh root@$ADDRESS "$FIREWALL_CMD"

    # Установка пакетов
    ssh root@$ADDRESS "yum install -y ${KUBE_PACKAGES[@]}"
done

# Установка пакетов для worker узлов
for ADDRESS in $WORKER_ADDRESSES; do
    echo "Установка пакетов на $ADDRESS"

    # Отключение SELinux и Firewall
    ssh root@$ADDRESS "$SELINUX_CMD"
    ssh root@$ADDRESS "$FIREWALL_CMD"

    # Установка пакетов
    ssh root@$ADDRESS "yum install -y ${KUBE_PACKAGES[@]}"
done
