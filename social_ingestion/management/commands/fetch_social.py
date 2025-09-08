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
        parser.add_argument("--force", action="store_true", help="Bypass fetch cache and force new requests")
        parser.add_argument("--username", help="X username (without @) to fetch only this account")
        parser.add_argument("--user-id", dest="user_id", help="X user id to fetch only this account")
        parser.add_argument("--no-since", action="store_true", help="Ignore since_id and fetch latest page")
        parser.add_argument("--debug", action="store_true", help="Print request params and API meta when fetching X")
        parser.add_argument("--include-retweets", action="store_true", help="Include retweets in results")
        parser.add_argument("--include-replies", action="store_true", help="Include replies in results")
        parser.add_argument("--save-all", action="store_true", help="Save posts even if they don't match categories")
        parser.add_argument("--reclassify", action="store_true", help="Recompute categories for existing tweets of the account")

    def handle(self, *args, **options):
        global _LAST_FETCH_AT
        now = datetime.now(dt_timezone.utc)
        force = options.get("force", False)
        if not force and _LAST_FETCH_AT and now - _LAST_FETCH_AT < _FETCH_CACHE_TTL:
            self.stdout.write(self.style.WARNING("Fetch saltado (cache activa) para ahorrar consumo."))
            return

        platform_filter = options.get("platform")
        dry_run = options.get("dry_run", False)
        single_username = (options.get("username") or "").strip().lstrip("@")
        single_user_id = (options.get("user_id") or "").strip()
        no_since = options.get("no_since", False)
        debug = options.get("debug", False)
        include_retweets = options.get("include_retweets", False)
        include_replies = options.get("include_replies", False)
        save_all = options.get("save_all", False)
        reclassify = options.get("reclassify", False)

        saved_count = 0
        matched_count = 0
        fetched_count = 0

        if platform_filter == "x" or not platform_filter:
            # Si se especifica una cuenta concreta, usarla y no iterar sobre todas
            if single_username or single_user_id:
                posts = self._fetch_x_by_identifiers(single_user_id, single_username, no_since, debug, include_retweets, include_replies)
                fetched_count += len(posts)
                if reclassify:
                    # Recalcular categorías para los últimos posts del autor
                    existing_qs = SocialPost.objects.filter(platform="x", author__iexact=single_username).order_by("-published_at")[:50]
                    for p in existing_qs:
                        cats = recommend_categories_from_text(p.text or "")
                        p.matched_categories = ",".join(cats)
                        p.save(update_fields=["matched_categories"])
                for post in posts:
                    categories = recommend_categories_from_text(post.get("text", ""))
                    if not categories and not save_all:
                        continue
                    matched_count += 1
                    if dry_run:
                        self.stdout.write(f"DRY: x {post.get('id')} @{post.get('author','')} -> {categories}")
                        continue
                    payload = dict(post)
                    if isinstance(payload.get("published_at"), datetime):
                        payload["published_at"] = payload["published_at"].isoformat()
                    if SocialPost.objects.filter(platform="x", post_id=post["id"]).exists():
                        continue
                    SocialPost.objects.create(
                        platform="x",
                        post_id=post["id"],
                        author=post.get("author", single_username or "unknown"),
                        text=post.get("text", ""),
                        published_at=post.get("published_at", datetime.now(dt_timezone.utc)),
                        raw_payload=payload,
                        matched_categories=",".join(categories),
                    )
                    saved_count += 1
                _LAST_FETCH_AT = now
                # Si se pidió cuenta específica, no continuar con otras plataformas/cuentas
                if platform_filter == "x" or not platform_filter:
                    # Continuar a telegram solo si explicitamente se pidió telegram
                    if platform_filter == "x":
                        # Resumen y salida
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
                        return
            # Iterar sobre TODAS las cuentas vinculadas (multiusuario)
            accounts = SocialAccount.objects.all()
            if not accounts.exists():
                self.stdout.write(self.style.WARNING("No hay cuentas de X vinculadas (SocialAccount). Intentando usar settings X_USER_ID/X_USERNAME..."))
                # Fallback a settings si no hay cuentas
                fallback_posts = self._fetch_x_from_settings()
                fetched_count += len(fallback_posts)
                for post in fallback_posts:
                    categories = recommend_categories_from_text(post.get("text", ""))
                    if not categories and not save_all:
                        continue
                    matched_count += 1
                    if dry_run:
                        self.stdout.write(f"DRY: x {post.get('id')} @{post.get('author','')} -> {categories}")
                    else:
                        payload = dict(post)
                        if isinstance(payload.get("published_at"), datetime):
                            payload["published_at"] = payload["published_at"].isoformat()
                        if not SocialPost.objects.filter(platform="x", post_id=post["id"]).exists():
                            SocialPost.objects.create(
                                platform="x",
                                post_id=post["id"],
                                author=post.get("author", "unknown"),
                                text=post.get("text", ""),
                                published_at=post.get("published_at", datetime.now(dt_timezone.utc)),
                                raw_payload=payload,
                                matched_categories=",".join(categories),
                            )
                            saved_count += 1
            for account in accounts:
                posts = self._fetch_x_for_account(account, no_since, debug, include_retweets, include_replies)
                fetched_count += len(posts)
                if reclassify:
                    existing_qs = SocialPost.objects.filter(platform="x", author__iexact=account.username).order_by("-published_at")[:50]
                    for p in existing_qs:
                        cats = recommend_categories_from_text(p.text or "")
                        p.matched_categories = ",".join(cats)
                        p.save(update_fields=["matched_categories"])
                for post in posts:
                    categories = recommend_categories_from_text(post.get("text", ""))
                    if not categories and not save_all:
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

    def _fetch_x_for_account(self, account: SocialAccount, no_since: bool, debug: bool, include_retweets: bool, include_replies: bool) -> list[dict[str, Any]]:
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

        latest = None
        params = {"max_results": max_results, "tweet.fields": "created_at,text"}
        if not no_since:
            latest = (
                SocialPost.objects.filter(platform="x", author__iexact=username)
                .order_by("-published_at")
                .first()
            )
            if latest and latest.post_id.isnumeric():
                params["since_id"] = latest.post_id

        # Exclude set: Twitter v2 supports exclude=retweets,replies
        exclude_values = []
        if not include_retweets:
            exclude_values.append("retweets")
        if not include_replies:
            exclude_values.append("replies")
        if exclude_values:
            params["exclude"] = ",".join(exclude_values)

        backoff_seconds = 5
        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=15)
                if debug:
                    self.stdout.write(f"X request -> URL: {url}")
                    self.stdout.write(f"X request -> params: {params}")
                if response.status_code == 200:
                    data = response.json()
                    if debug:
                        meta = data.get("meta", {})
                        self.stdout.write(f"X response meta: {meta}")
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
                    reset_header = response.headers.get("x-rate-limit-reset")
                    wait_seconds = None
                    if reset_header:
                        try:
                            reset_ts = int(reset_header)
                            now_ts = int(time.time())
                            wait_seconds = max(0, reset_ts - now_ts)
                        except ValueError:
                            wait_seconds = None
                    if wait_seconds is not None and wait_seconds <= 90:
                        self.stdout.write(self.style.WARNING(f"Rate limit X (429). Esperando hasta reset ({wait_seconds}s)..."))
                        time.sleep(wait_seconds)
                    else:
                        self.stdout.write(self.style.WARNING(f"Rate limit X (429). Reintentando en {backoff_seconds}s..."))
                        time.sleep(backoff_seconds)
                        backoff_seconds *= 2
                    continue
                else:
                    if debug:
                        self.stdout.write(self.style.ERROR(f"X API error body: {response.text}"))
                    self.stdout.write(self.style.ERROR(f"X API error: {response.status_code}"))
                    break
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"X API request failed: {e}"))
                break

        return []

    def _fetch_x_by_identifiers(self, explicit_user_id: str | None, username: str | None, no_since: bool, debug: bool, include_retweets: bool, include_replies: bool) -> list[dict[str, Any]]:
        bearer_token = getattr(settings, "X_BEARER_TOKEN", "").strip()
        if not bearer_token or bearer_token == "TU_TOKEN_DE_ACCESO_AQUI":
            self.stdout.write(self.style.WARNING("X_BEARER_TOKEN no configurado."))
            return []

        user_id = (explicit_user_id or "").strip() or None
        if not user_id and username:
            user_id, username = self._resolve_x_user_id(bearer_token, username)
        if not user_id:
            self.stdout.write(self.style.WARNING("No se resolvió X_USER_ID/X_USERNAME para la cuenta indicada."))
            return []

        url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        headers = {"Authorization": f"Bearer {bearer_token}", "User-Agent": "ComercIA/1.0"}
        max_results = max(5, min(int(getattr(settings, "X_MAX_RESULTS", 5)), 25))

        params = {"max_results": max_results, "tweet.fields": "created_at,text"}
        if not no_since:
            latest = (
                SocialPost.objects.filter(platform="x", author__iexact=username or "")
                .order_by("-published_at")
                .first()
            )
            if latest and latest.post_id.isnumeric():
                params["since_id"] = latest.post_id

        # Exclude set similar to _fetch_x_for_account
        exclude_values = []
        if not include_retweets:
            exclude_values.append("retweets")
        if not include_replies:
            exclude_values.append("replies")
        if exclude_values:
            params["exclude"] = ",".join(exclude_values)

        backoff_seconds = 5
        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=15)
                if debug:
                    self.stdout.write(f"X request -> URL: {url}")
                    self.stdout.write(f"X request -> params: {params}")
                if response.status_code == 200:
                    data = response.json()
                    if debug:
                        meta = data.get("meta", {})
                        self.stdout.write(f"X response meta: {meta}")
                    tweets = data.get("data", [])
                    posts: list[dict[str, Any]] = []
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
                    reset_header = response.headers.get("x-rate-limit-reset")
                    wait_seconds = None
                    if reset_header:
                        try:
                            reset_ts = int(reset_header)
                            now_ts = int(time.time())
                            wait_seconds = max(0, reset_ts - now_ts)
                        except ValueError:
                            wait_seconds = None
                    if wait_seconds is not None and wait_seconds <= 90:
                        self.stdout.write(self.style.WARNING(f"Rate limit X (429). Esperando hasta reset ({wait_seconds}s)..."))
                        time.sleep(wait_seconds)
                    else:
                        self.stdout.write(self.style.WARNING(f"Rate limit X (429). Reintentando en {backoff_seconds}s..."))
                        time.sleep(backoff_seconds)
                        backoff_seconds *= 2
                    continue
                else:
                    if debug:
                        self.stdout.write(self.style.ERROR(f"X API error body: {response.text}"))
                    self.stdout.write(self.style.ERROR(f"X API error: {response.status_code}"))
                    break
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"X API request failed: {e}"))
                break

        return []

    def _fetch_x_from_settings(self) -> list[dict[str, Any]]:
        """Fallback para obtener tweets usando settings cuando no hay SocialAccount."""
        bearer_token = getattr(settings, "X_BEARER_TOKEN", "").strip()
        if not bearer_token or bearer_token == "TU_TOKEN_DE_ACCESO_AQUI":
            self.stdout.write(self.style.WARNING("X_BEARER_TOKEN no configurado."))
            return []
        explicit_id = getattr(settings, "X_USER_ID", "").strip()
        username = getattr(settings, "X_USERNAME", "").strip()
        user_id = explicit_id
        if not user_id and username:
            user_id, username = self._resolve_x_user_id(bearer_token, username)
        if not user_id:
            self.stdout.write(self.style.WARNING("No se resolvió X_USER_ID/X_USERNAME desde settings."))
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
                    posts: list[dict[str, Any]] = []
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
                    reset_header = response.headers.get("x-rate-limit-reset")
                    wait_seconds = None
                    if reset_header:
                        try:
                            reset_ts = int(reset_header)
                            now_ts = int(time.time())
                            wait_seconds = max(0, reset_ts - now_ts)
                        except ValueError:
                            wait_seconds = None
                    if wait_seconds is not None and wait_seconds <= 90:
                        self.stdout.write(self.style.WARNING(f"Rate limit X (429). Esperando hasta reset ({wait_seconds}s)..."))
                        time.sleep(wait_seconds)
                    else:
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
