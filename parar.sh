#!/bin/sh
# Pára o sistema (os dados ficam guardados para a próxima vez)
cd "$(dirname "$0")" && docker compose stop
