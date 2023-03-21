#!/bin/bash

# Получение аргументов скрипта
cp_addresses="$1"
worker_addresses="$2"
version="$3"
os="$4"
vip="$5"


# Установка пакетов на control-plane узлах
ansible-playbook -i "${cp_addresses}," -e "k8s_version=${version} os=${os} virtual_ip=${vip}" playbook_cp.yml --become-user=root -v

# Установка пакетов на worker узлах
ansible-playbook -i "${worker_addresses}," -e "k8s_version=${version} os=${os}" playbook_worker.yml --become-user=root -v

###OLD_START
# Запуск ansible скрипта для установки Kubernetes
#ansible-playbook -i "$cp_addresses,$worker_addresses," \
#    -e "kube_version=$version" \
#    -e "kube_os=$os" \
#    install_kubernetes.yml --become-user=root -v
#
## Вывод сообщения об окончании работы скрипта
#echo "Установка завершена"
