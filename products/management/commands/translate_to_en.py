from django.core.management.base import BaseCommand
from django.db import transaction
from deep_translator import GoogleTranslator

from products.models import Product
from seller_profiles.models import SellerProfile


class Command(BaseCommand):
    help = (
        "Translate Spanish fields to English for products and seller profiles "
        "(fills name_en/description_en and slogan_en/description_en when empty)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be translated without saving",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=200,
            help="Max objects to process per model (default: 200)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]
        translator = GoogleTranslator(source="auto", target="en")


        with transaction.atomic():
            self._translate_products(translator, dry_run, limit)
            self._translate_profiles(translator, dry_run, limit)
            if dry_run:
                self.stdout.write(self.style.WARNING("Dry run: rolling back changes"))
                transaction.set_rollback(True)

    def _safe_translate(self, translator, text: str) -> str:
        if not text:
            return text
        try:
            translated = translator.translate(text)
            return translated if translated else text
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Translation failed: {e}"))
            return text

    def _translate_products(self, translator, dry_run: bool, limit: int):
        qs = Product.objects.all()[:limit]
        updated = 0
        for p in qs:
            changed = False

            # Traduce si el campo inglés está vacío o igual al español
            if not p.name_en or p.name_en.strip().lower() == p.name.strip().lower():
                p.name_en = self._safe_translate(translator, p.name)
                changed = True

            if (
                not p.description_en
                or p.description_en.strip().lower() == p.description.strip().lower()
            ):
                p.description_en = self._safe_translate(translator, p.description)
                changed = True

            if changed:
                if not dry_run:
                    p.save(update_fields=["name_en", "description_en"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Products updated: {updated}"))

    def _translate_profiles(self, translator, dry_run: bool, limit: int):
        qs = SellerProfile.objects.all()[:limit]
        updated = 0
        for sp in qs:
            changed = False

            if not sp.slogan_en or sp.slogan_en.strip().lower() == sp.slogan.strip().lower():
                sp.slogan_en = self._safe_translate(translator, sp.slogan)
                changed = True

            if (
                not sp.description_en
                or sp.description_en.strip().lower() == sp.description.strip().lower()
            ):
                sp.description_en = self._safe_translate(translator, sp.description)
                changed = True

            if changed:
                if not dry_run:
                    sp.save(update_fields=["slogan_en", "description_en"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Seller profiles updated: {updated}"))
