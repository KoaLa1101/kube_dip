#!/bin/bash

# shellcheck disable=SC2206
cp_addresses=($1)
worker_addresses=($2)
vip=$3
first_cp_address=$(echo ${cp_addresses[0]} | cut -d',' -f1)

# Запуск Ansible плейбука для инициализации кластера Kubernetes на первом сервере
ansible-playbook -i "${first_cp_address}," init_k8s_master.yml --extra-vars "vip=${vip}" --become-user=root -v

# Обход всех остальных серверов из списка cp_addresses и добавление их как control plane
# shellcheck disable=SC2128
for ip in $(echo "$cp_addresses" | tr ',' ' '); do
  if [[ "$ip" != "$first_cp_address" ]]; then
  ansible-playbook -i "${ip}," join_control_plane.yml --become-user=root -v
  fi
done

# shellcheck disable=SC2128
if [[ $worker_addresses != "0.0.0.0" ]]; then
  # Обход всех серверов из списка worker_addresses и добавление их как worker
  for ip in $(echo "$cp_addresses" | tr ',' ' '); do
    ansible-playbook -i "${ip}," join_worker.yml --become-user=root -v
  done
fi