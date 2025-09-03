from django.core.management.base import BaseCommand
from social_ingestion.models import SocialSource


class Command(BaseCommand):
    help = "Create test social sources for development"

    def handle(self, *args, **options):
        # Create X source
        x_source, created = SocialSource.objects.get_or_create(
            platform="x",
            handle="test_user",
            defaults={"active": True}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created X source: {x_source}"))
        else:
            self.stdout.write(f"X source already exists: {x_source}")

        # Create Telegram source
        tg_source, created = SocialSource.objects.get_or_create(
            platform="telegram",
            handle="test_channel",
            defaults={"active": True}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Telegram source: {tg_source}"))
        else:
            self.stdout.write(f"Telegram source already exists: {tg_source}")

        self.stdout.write(self.style.SUCCESS("Test sources ready. Run: python manage.py fetch_social --dry-run"))
