#!/bin/bash
set -e

echo "Настройка сервера"

# Docker
if ! command -v docker &> /dev/null
then
    echo "Установка Docker"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
else
    echo "Docker уже установлен."
fi

# Traefik
if ! docker network ls | grep -q "traefik-net"
then
    echo "Создание сети traefik-net"
    docker network create traefik-net
fi

if ! docker ps | grep -q "traefik"
then
    echo "Запуск Traefik proxy"
    docker run -d \
      --name traefik \
      -p 80:80 \
      -p 8080:8080 \
      -v /var/run/docker.sock:/var/run/docker.sock:ro \
      --network traefik-net \
      --restart unless-stopped \
      traefik:latest \
      --api.insecure=true \
      --providers.docker=true \
      --providers.docker.exposedbydefault=false \
      --entrypoints.web.address=:80 \
      --entrypoints.websecure.address=:443
else
    echo "Traefik уже запущен"
fi

echo "Подготовка сервера завершена"
