#!/bin/bash
set -e

IP_ADDRESS=$1
K8S_VERSION=$2
ANSIBLE_PLAYBOOK_PATH="add_node.yml"

if [ -z "$IP_ADDRESS" ]; then
    echo "IP-адрес не указан"
    exit 1
fi

echo "Запуск Ansible playbook с IP-адресом: $IP_ADDRESS и k8s версией: $K8S_VERSION"
ansible-playbook -i "${IP_ADDRESS}," $ANSIBLE_PLAYBOOK_PATH --extra-vars "k8s_version=$K8S_VERSION" --become-user=root -v
