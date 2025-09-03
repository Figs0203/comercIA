from datetime import datetime, timezone as dt_timezone
import uuid

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from social_ingestion.models import SocialPost, SocialAccount
from social_ingestion import recommend_categories_from_text


class Command(BaseCommand):
    help = "Seed demo SocialPost entries for the logged-in user's linked X account (for UI testing)"

    def add_arguments(self, parser):
        parser.add_argument("username", help="Django username que tiene SocialAccount vinculado")
        parser.add_argument(
            "--texts",
            nargs="+",
            default=[
                "me gusta la comida como el mango, las papas y el pastel",
                "las papas son lo mejor del mundo",
                "será que me compro un pastel de guayaba?",
            ],
            help="Lista de textos para crear posts demo",
        )

    def handle(self, *args, **options):
        django_username = options["username"]
        texts = options["texts"]

        User = get_user_model()
        try:
            user = User.objects.get(username=django_username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No existe usuario Django: {django_username}"))
            return

        try:
            social = SocialAccount.objects.get(user=user)
        except SocialAccount.DoesNotExist:
            self.stdout.write(self.style.ERROR("El usuario no tiene SocialAccount vinculado"))
            return

        created_count = 0
        for text in texts:
            categories = recommend_categories_from_text(text)
            if not categories:
                continue
            post_id = f"demo-{uuid.uuid4()}"
            obj, created = SocialPost.objects.get_or_create(
                platform="x",
                post_id=post_id,
                defaults={
                    "author": social.username,
                    "text": text,
                    "published_at": datetime.now(dt_timezone.utc),
                    "raw_payload": {"id": post_id, "text": text, "author": social.username},
                    "matched_categories": ",".join(categories),
                },
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Creados {created_count} posts demo."))


