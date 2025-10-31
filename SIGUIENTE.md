### Pasos manuales requeridos

- Configurar variables de entorno en `.env` o en la plataforma de despliegue:
  - `SECRET_KEY`: clave segura para Django.
  - `DEBUG`: `0` en producción.
  - `ALLY_PRODUCTS_API_URL`: URL del servicio JSON del equipo anterior (ej: `https://equipo1.com/api/products/`).
  - Opcionales de X (Twitter):
    - `X_BEARER_TOKEN`: token de acceso a la API de X.
    - `X_USER_ID` o `X_USERNAME`.


- Proveer servicio para el siguiente equipo:
  - Comparte la ruta `https://TU_DOMINIO/api/products/` al siguiente equipo.

- Consumir servicio del equipo anterior:
  * Define `ALLY_PRODUCTS_API_URL` en las variables de entorno con la URL JSON que te entregan.
  * Verifica la página `/productos-aliados` mostrando los datos.

- Despliegue con Docker en GCP:
  * Construir imagen: `docker build -t gcr.io/TU_PROYECTO/comercia:latest .`
  * Autenticarse: `gcloud auth configure-docker`
  * Subir imagen: `docker push gcr.io/TU_PROYECTO/comercia:latest`
  * Desplegar (Cloud Run recomendado):
    - `gcloud run deploy comercia --image gcr.io/TU_PROYECTO/comercia:latest --platform managed --region us-central1 --allow-unauthenticated`
  * Configurar variables de entorno en el servicio (SECRET_KEY, DEBUG=0, ALLOWED_HOSTS, ALly URL, etc.).

- Dominio .tk (opcional):
  * Registra el dominio en `http://www.dot.tk/`.
  * Apunta el dominio al servicio (DNS -> CNAME a la URL de Cloud Run o a un balanceador si usas GCE/GKE).

- GitHub Projects (usabilidad):
  * Crea un proyecto con columnas: Backlog, In Progress, Review, Done.
  * Crea tarjetas para: unificación visual, formularios persistentes al error, navegación/breadcrumbs (opcional), responsive.

- Ngrok (opcional local):
  * Si necesitas túnel, añade tu token en el código o como variable de entorno y usa la acción “Iniciar ngrok” siendo superusuario.


### Checklist Entregable #2 (faltantes/por verificar)


- Pruebas unitarias (mínimo 2):
  - Ya existen 2 (`products/tests.py`). Ejecutar en CI/local: `python manage.py test` y dejar captura/evidencia.

- Servicio JSON propio (para el siguiente equipo):
  - Ya existe en `GET /api/products/`. Compartir URL pública desplegada.

- Consumir servicio del equipo anterior:
  - Ya existe vista `/productos-aliados`. Configurar `ALLY_PRODUCTS_API_URL` en el entorno de producción y validar en despliegue.


- Inversión de dependencias (DI):
  - Implementada en `products/services/reporting.py` con interfaz y 2 clases. Expuesta en `GET /reporte/descargar/`.
  - Tarea: documentar variable `REPORT_GENERATOR` (`csv`|`json`) en README/SIGUIENTE y probar descarga en despliegue.


- Docker en GCP:
  - Finalizar despliegue en Cloud Run (pasos arriba). Configurar variables de entorno y `ALLOWED_HOSTS`.
  - Subir evidencia (URL pública) y dejar comandos usados.

- Dominio .tk (opcional):
  - Registrar y apuntar al servicio. Dejar dominio en este archivo.
