#!/bin/sh
set -e

echo "⏳ Aplicando migraciones..."
python manage.py migrate --noinput

echo "✅ Migraciones listas. Iniciando servidor..."
exec "$@"
