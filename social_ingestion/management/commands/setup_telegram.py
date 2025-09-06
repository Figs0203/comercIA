import os
from django.core.management.base import BaseCommand
from social_ingestion.models import SocialSource


class Command(BaseCommand):
    """Comando para configurar fuentes de Telegram en el sistema"""
    help = "Configura fuentes de Telegram para monitorear canales y grupos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--chat-id", 
            type=str, 
            help="ID del chat/canal de Telegram a monitorear"
        )
        parser.add_argument(
            "--name", 
            type=str, 
            help="Nombre descriptivo para la fuente"
        )
        parser.add_argument(
            "--list", 
            action="store_true", 
            help="Listar fuentes de Telegram existentes"
        )
        parser.add_argument(
            "--remove", 
            type=int, 
            help="ID de la fuente a eliminar"
        )

    def handle(self, *args, **options):
        # Verificar configuración del bot
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            self.stdout.write(
                self.style.ERROR("TELEGRAM_BOT_TOKEN no configurado en variables de entorno")
            )
            return

        # Listar fuentes existentes
        if options["list"]:
            sources = SocialSource.objects.filter(platform="telegram")
            if sources.exists():
                self.stdout.write(self.style.SUCCESS("Fuentes de Telegram configuradas:"))
                for source in sources:
                    status = "Activa" if source.active else "Inactiva"
                    self.stdout.write(f"  ID: {source.id} | Chat: {source.handle} | Estado: {status}")
            else:
                self.stdout.write(self.style.WARNING("No hay fuentes de Telegram configuradas"))
            return

        # Eliminar fuente
        if options["remove"]:
            try:
                source = SocialSource.objects.get(id=options["remove"], platform="telegram")
                source.delete()
                self.stdout.write(
                    self.style.SUCCESS(f"Fuente de Telegram {options['remove']} eliminada")
                )
            except SocialSource.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Fuente de Telegram {options['remove']} no encontrada")
                )
            return

        # Crear nueva fuente
        chat_id = options.get("chat_id")
        name = options.get("name", f"Canal {chat_id}")

        if not chat_id:
            self.stdout.write(
                self.style.ERROR("Debe proporcionar --chat-id para crear una nueva fuente")
            )
            return

        # Verificar si ya existe
        if SocialSource.objects.filter(platform="telegram", handle=chat_id).exists():
            self.stdout.write(
                self.style.WARNING(f"Ya existe una fuente para el chat {chat_id}")
            )
            return

        # Crear la fuente
        source = SocialSource.objects.create(
            platform="telegram",
            handle=chat_id,
            active=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Fuente de Telegram creada: ID {source.id} | Chat: {chat_id}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Puedes usar 'python manage.py fetch_social --platform telegram' para probar"
            )
        )
