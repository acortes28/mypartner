#!/bin/sh
set -e

echo "⏳ Aplicando migraciones..."
python manage.py migrate --noinput

echo "📦 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Listo. Iniciando servidor..."
exec "$@"
