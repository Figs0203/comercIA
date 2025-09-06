import os
import json
import time
from datetime import datetime, timezone as dt_timezone, timedelta
from typing import Any
import requests

from django.conf import settings
from django.core.management.base import BaseCommand

from social_ingestion import recommend_categories_from_text
from social_ingestion.models import SocialPost, SocialSource, SocialAccount


_LAST_FETCH_AT: datetime | None = None
_FETCH_CACHE_TTL = timedelta(minutes=3)


class Command(BaseCommand):
    help = "Fetch posts from configured social sources (X and Telegram) and store matches"

    def add_arguments(self, parser):
        parser.add_argument("--platform", choices=["x", "telegram"], help="Filter by platform")
        parser.add_argument("--dry-run", action="store_true", help="Do not save to DB")

    def handle(self, *args, **options):
        global _LAST_FETCH_AT
        now = datetime.now(dt_timezone.utc)
        if _LAST_FETCH_AT and now - _LAST_FETCH_AT < _FETCH_CACHE_TTL:
            self.stdout.write(self.style.WARNING("Fetch saltado (cache activa) para ahorrar consumo."))
            return

        platform_filter = options.get("platform")
        dry_run = options.get("dry_run", False)

        saved_count = 0
        matched_count = 0
        fetched_count = 0

        if platform_filter == "x" or not platform_filter:
            # Iterar sobre TODAS las cuentas vinculadas (multiusuario)
            accounts = SocialAccount.objects.all()
            if not accounts.exists():
                self.stdout.write(self.style.WARNING("No hay cuentas de X vinculadas (SocialAccount)."))
            for account in accounts:
                posts = self._fetch_x_for_account(account)
                fetched_count += len(posts)
                for post in posts:
                    categories = recommend_categories_from_text(post.get("text", ""))
                    if not categories:
                        continue
                    matched_count += 1
                    if dry_run:
                        self.stdout.write(f"DRY: x {post.get('id')} @{account.username} -> {categories}")
                        continue
                    payload = dict(post)
                    if isinstance(payload.get("published_at"), datetime):
                        payload["published_at"] = payload["published_at"].isoformat()
                    if SocialPost.objects.filter(platform="x", post_id=post["id"]).exists():
                        continue
                    SocialPost.objects.create(
                        platform="x",
                        post_id=post["id"],
                        author=account.username,
                        text=post.get("text", ""),
                        published_at=post.get("published_at", datetime.now(dt_timezone.utc)),
                        raw_payload=payload,
                        matched_categories=",".join(categories),
                    )
                    saved_count += 1

        if platform_filter == "telegram" or (not platform_filter and SocialSource.objects.filter(platform="telegram", active=True).exists()):
            sources = SocialSource.objects.filter(active=True, platform="telegram")
            for source in sources:
                posts = self._fetch_telegram(source)
                fetched_count += len(posts)
                for post in posts:
                    categories = recommend_categories_from_text(post.get("text", ""))
                    if not categories:
                        continue
                    matched_count += 1
                    if dry_run:
                        self.stdout.write(f"DRY: telegram {post.get('id')} -> {categories}")
                        continue
                    payload = dict(post)
                    if isinstance(payload.get("published_at"), datetime):
                        payload["published_at"] = payload["published_at"].isoformat()
                    if SocialPost.objects.filter(platform="telegram", post_id=post["id"]).exists():
                        continue
                    SocialPost.objects.create(
                        platform="telegram",
                        post_id=post["id"],
                        author=post.get("author", "unknown"),
                        text=post.get("text", ""),
                        published_at=post.get("published_at", datetime.now(dt_timezone.utc)),
                        raw_payload=payload,
                        matched_categories=",".join(categories),
                    )
                    saved_count += 1

        _LAST_FETCH_AT = now

        # Resumen amigable para el usuario
        if dry_run:
            if matched_count > 0:
                self.stdout.write(self.style.SUCCESS(f"Se detectaron {matched_count} publicaciones con categorías (simulación)."))
            else:
                self.stdout.write(self.style.WARNING("No se detectaron publicaciones con palabras clave (simulación)."))
        else:
            if saved_count > 0:
                self.stdout.write(self.style.SUCCESS(f"Listo: guardadas {saved_count} publicaciones (de {matched_count} con categorías, {fetched_count} obtenidas)."))
            elif fetched_count > 0 and matched_count == 0:
                self.stdout.write(self.style.WARNING("Se obtuvieron publicaciones, pero ninguna coincidió con palabras clave."))
            else:
                self.stdout.write(self.style.WARNING("No se obtuvieron publicaciones nuevas. Puede haber límite de tasa o no hay tweets recientes."))

    def _resolve_x_user_id(self, bearer_token: str, username: str | None) -> tuple[str | None, str | None]:
        username = (username or getattr(settings, "X_USERNAME", "")).strip()
        explicit_id = getattr(settings, "X_USER_ID", "").strip()
        if explicit_id and not username:
            return explicit_id, None
        if not username:
            return None, None
        url = f"https://api.twitter.com/2/users/by/username/{username}"
        headers = {"Authorization": f"Bearer {bearer_token}"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {}).get("id"), username
            self.stdout.write(self.style.ERROR(f"X username->id error: {resp.status_code} - {resp.text}"))
            return None, username
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"X username->id request failed: {e}"))
            return None, username

    def _fetch_x_for_account(self, account: SocialAccount) -> list[dict[str, Any]]:
        bearer_token = getattr(settings, "X_BEARER_TOKEN", "").strip()
        if not bearer_token or bearer_token == "TU_TOKEN_DE_ACCESO_AQUI":
            self.stdout.write(self.style.WARNING("X_BEARER_TOKEN no configurado."))
            return []

        user_id = account.external_user_id.strip() if account.external_user_id else None
        username = account.username
        if not user_id:
            user_id, _ = self._resolve_x_user_id(bearer_token, username)
        if not user_id:
            self.stdout.write(self.style.WARNING("No se resolvió X_USER_ID/X_USERNAME."))
            return []

        url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        headers = {"Authorization": f"Bearer {bearer_token}", "User-Agent": "ComercIA/1.0"}
        max_results = max(5, min(int(getattr(settings, "X_MAX_RESULTS", 5)), 25))

        latest = (
            SocialPost.objects.filter(platform="x", author__iexact=username)
            .order_by("-published_at")
            .first()
        )
        params = {"max_results": max_results, "tweet.fields": "created_at,text"}
        if latest and latest.post_id.isnumeric():
            params["since_id"] = latest.post_id

        backoff_seconds = 5
        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    tweets = data.get("data", [])
                    posts = []
                    for tweet in tweets:
                        posts.append(
                            {
                                "id": tweet["id"],
                                "author": username or "unknown",
                                "text": tweet.get("text", ""),
                                "published_at": datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00")) if tweet.get("created_at") else datetime.now(dt_timezone.utc),
                            }
                        )
                    return posts
                elif response.status_code == 429:
                    self.stdout.write(self.style.WARNING(f"Rate limit X (429). Reintentando en {backoff_seconds}s..."))
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2
                    continue
                else:
                    self.stdout.write(self.style.ERROR(f"X API error: {response.status_code} - {response.text}"))
                    break
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"X API request failed: {e}"))
                break

        return []

    def _fetch_telegram(self, source: SocialSource) -> list[dict[str, Any]]:
        """Obtiene mensajes de un canal/grupo de Telegram usando Bot API"""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = source.handle
        
        if not bot_token:
            self.stdout.write(self.style.WARNING("TELEGRAM_BOT_TOKEN no configurado."))
            return []
        
        if not chat_id:
            self.stdout.write(self.style.WARNING(f"Chat ID no configurado para fuente {source}"))
            return []
        
        # Obtener el último mensaje procesado para evitar duplicados
        latest = (
            SocialPost.objects.filter(platform="telegram", author=chat_id)
            .order_by("-published_at")
            .first()
        )
        
        # Configurar parámetros de la API
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        params = {
            "chat_id": chat_id,
            "limit": 20,  # Máximo 20 mensajes por request
        }
        
        # Si tenemos un mensaje reciente, usar su ID como offset
        if latest and latest.post_id.isnumeric():
            params["offset"] = int(latest.post_id) + 1
        
        try:
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if not data.get("ok"):
                    self.stdout.write(self.style.ERROR(f"Telegram API error: {data.get('description', 'Unknown error')}"))
                    return []
                
                updates = data.get("result", [])
                posts = []
                
                for update in updates:
                    message = update.get("message", {})
                    if not message:
                        continue
                    
                    # Solo procesar mensajes de texto
                    if "text" not in message:
                        continue
                    
                    # Verificar que el mensaje sea del chat correcto
                    chat = message.get("chat", {})
                    if str(chat.get("id")) != str(chat_id):
                        continue
                    
                    # Extraer información del mensaje
                    message_id = str(message.get("message_id", ""))
                    text = message.get("text", "")
                    date = message.get("date", 0)
                    
                    # Convertir timestamp a datetime
                    published_at = datetime.fromtimestamp(date, tz=dt_timezone.utc)
                    
                    posts.append({
                        "id": message_id,
                        "author": chat.get("title", chat.get("username", chat_id)),
                        "text": text,
                        "published_at": published_at,
                    })
                
                return posts
                
            elif response.status_code == 429:
                self.stdout.write(self.style.WARNING("Rate limit de Telegram alcanzado. Reintentando más tarde..."))
                return []
            else:
                self.stdout.write(self.style.ERROR(f"Telegram API error: {response.status_code} - {response.text}"))
                return []
                
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Telegram API request failed: {e}"))
            return []
