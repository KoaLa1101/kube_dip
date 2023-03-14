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
if [ ${#CP_ADDRESSES[@]} -eq 3 ]; then
    for ADDRESS in ${CP_ADDRESSES[@]}; do
        echo "Установка пакетов на $ADDRESS"

        # Отключение SELinux и Firewall
        ssh root@$ADDRESS "$SELINUX_CMD"
        ssh root@$ADDRESS "$FIREWALL_CMD"

        # Установка пакетов
        if [ "$OS" == "CentOS" ]; then
            ssh root@$ADDRESS "yum install -y ${KUBE_PACKAGES[@]}"
        else
            ssh root@$ADDRESS "apt-get update -y && apt-get install -y ${KUBE_PACKAGES[@]}"
        fi

        # Настройка haproxy и keepalived
        ssh root@$ADDRESS "echo '
        global
            log /dev/log    local0
            log /dev/log    local1 notice
            chroot /var/lib/haproxy
            stats socket /run/haproxy/admin.sock mode 660 level admin expose-fd listeners
            stats timeout 30s
            user haproxy
            group haproxy
            daemon
            maxconn 256

        defaults
            log global
            mode    tcp
            option  tcplog
            option  dontlognull
            timeout connect 5000
            timeout client  50000
            timeout server  50000

        frontend kubernetes-api
            bind *:6443
            mode tcp
            default_backend kubernetes-control-plane

        backend kubernetes-control-plane
            mode tcp
            balance roundrobin
            option ssl-hello-chk
            server k8s-master-1 ${CP_ADDRESSES[0]}:6443 check
            server k8s-master-2 ${CP_ADDRESSES[1]}:6443 check
            server k8s-master-3 ${CP_ADDRESSES[2]}:6443 check
        ' > /etc/haproxy/haproxy.cfg"

        ssh root@$ADDRESS "systemctl enable haproxy && systemctl start haproxy"
        ssh root@$ADDRESS "echo '
        net.ipv4.ip_nonlocal_bind=1
        net.ipv4.conf.all.rp_filter=0
        net.ipv4.conf.default.rp_filter=0
        ' >> /etc/sysctl.conf && sysctl -p"

        ssh root@$ADDRESS "echo '
        vrrp_script chk_haproxy {
            script \"killall -0 haproxy\"
            interval 2
        }

        vrrp_instance VI_1 {
            interface eth0
            virtual_router_id 51
            priority 200
            advert_int 1
            unicast_src_ip $ADDRESS
            unicast_peer {
                ${CP_ADDRESSES[0]}
                ${CP_ADDRESSES[1]}
                ${CP_ADDRESSES[2]}
            }
            authentication {
                auth_type PASS
                auth_pass password
            }
            track_script {
                chk_haproxy
            }
            virtual_ipaddress {
                $ADDRESS
            }
        }
        ' > /etc/keepalived/keepalived.conf"

        ssh root@$ADDRESS "systemctl enable keepalived && systemctl start keepalived"
    done
fi

# Установка пакетов для worker узлов
for ADDRESS in $WORKER_ADDRESSES; do
    echo "Установка пакетов на $ADDRESS"

    # Отключение SELinux и Firewall
    ssh root@$ADDRESS "$SELINUX_CMD"
    ssh root@$ADDRESS "$FIREWALL_CMD"

    # Установка пакетов
    if [ "$OS" == "CentOS" ]; then
        ssh root@$ADDRESS "yum install -y ${KUBE_WORKER_PACKAGES[@]}"
    else
        ssh root@$ADDRESS "apt-get update -y && apt-get install -y ${KUBE_WORKER_PACKAGES[@]}"
    fi

    # Настройка kubelet
    ssh root@$ADDRESS "echo '
    apiVersion: kubelet.config.k8s.io/v1beta1
    kind: KubeletConfiguration
    cgroupDriver: systemd
    ' > /etc/kubernetes/kubelet-config.yaml"

    ssh root@$ADDRESS "echo '
    KUBELET_EXTRA_ARGS=--config=/etc/kubernetes/kubelet-config.yaml
    ' > /etc/default/kubelet"

    # Запуск kubelet
    ssh root@$ADDRESS "systemctl enable kubelet && systemctl start kubelet"
done

echo "Установка завершена"
zenity --info --text="Пакеты установлены"
