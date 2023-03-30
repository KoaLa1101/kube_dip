#!/bin/bash

# Получение аргументов скрипта
cp_addresses="$1"
worker_addresses="$2"
version="$3"
os="$4"
vip="$5"

# Установка пакетов на control-plane узлах
ansible-playbook -i "${cp_addresses}," -e "k8s_version=${version} os=${os} vip=${vip}" playbook_cp.yml --become-user=root

# Установка пакетов на worker узлах
if worker_addresses[0] != '0.0.0.0'
    ansible-playbook -i "${worker_addresses}," -e "k8s_version=${version} os=${os}" playbook_worker.yml --become-user=root

###OLD_START
# Запуск ansible скрипта для установки Kubernetes
#ansible-playbook -i "$cp_addresses,$worker_addresses," \
#    -e "kube_version=$version" \
#    -e "kube_os=$os" \
#    install_kubernetes.yml --become-user=root -v
#
## Вывод сообщения об окончании работы скрипта
#echo "Установка завершена"
