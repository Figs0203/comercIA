# Configuración de X API v2 para ComercIA

## Paso 1: Obtener credenciales de X API

1. Ve a [https://developer.twitter.com/en/portal/dashboard](https://developer.twitter.com/en/portal/dashboard)
2. Crea una cuenta o inicia sesión
3. Crea una nueva app o usa una existente
4. Ve a "Keys and tokens"
5. Copia el "Bearer Token" (necesitas permisos de lectura)

## Paso 2: Obtener User ID

1. Ve a [https://tweeterid.com/](https://tweeterid.com/)
2. Pega el username (sin @) del usuario cuyos tweets quieres analizar
3. Copia el User ID que aparece

## Paso 3: Configurar en Django

Edita `eafit_trade/settings.py`:

```python
# X API v2 configuration
X_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAA..."  # Tu Bearer Token real
X_USER_ID = "1234567890"  # ID del usuario real
```

## Paso 4: Crear fuente en admin

1. Ejecuta: `python manage.py runserver`
2. Ve a `/admin` y crea un `SocialSource`:
   - Platform: `x`
   - Handle: cualquier identificador (ej: "mi_usuario")
   - Active: ✓

## Paso 5: Probar

```bash
# Probar sin guardar
python manage.py fetch_social --platform x --dry-run

# Guardar en base de datos
python manage.py fetch_social --platform x
```

## Notas importantes

- **Rate limits**: X API tiene límites de 300 requests/15min para cuentas gratuitas
- **Permisos**: Solo necesitas permisos de lectura
- **Fallback**: Si no configuras tokens, se usan datos mock para desarrollo
- **Categorías**: El sistema detecta automáticamente comida, ropa, tecnología en los tweets
