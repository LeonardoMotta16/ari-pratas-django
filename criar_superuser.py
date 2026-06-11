"""
Script para criar superuser automaticamente no deploy.
Lê as credenciais das variáveis de ambiente.
Não faz nada se o usuário já existir.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aripratas.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
email    = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@aripratas.com")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")

if not password:
    print("AVISO: DJANGO_SUPERUSER_PASSWORD não definida. Superuser não criado.")
else:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superuser '{username}' criado com sucesso.")
    else:
        print(f"Superuser '{username}' já existe. Nada a fazer.")