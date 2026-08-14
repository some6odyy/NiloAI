# Nilo AI — Backend + Dashboard

Plataforma SaaS que automatiza la atención al cliente de pymes por
WhatsApp usando IA. Estructura por capas (FastAPI + SQLAlchemy + SQLite),
fiel al MER y a los RF/RNF del informe del Grupo 7.

## Estructura

```
app/
  core/        -> configuración, seguridad (JWT/bcrypt), dependencias de auth
  db/          -> conexión a la base de datos (SQLAlchemy)
  models/      -> tablas: Administrador, Negocio, Servicio, Cliente,
                  Conversacion, Mensaje, ContextoIA, Agenda
  schemas/     -> validación Pydantic de entrada/salida por módulo
  routers/     -> endpoints agrupados por requerimiento funcional
  services/    -> integración con WhatsApp Cloud API y el proveedor de IA
  main.py      -> arma la app, CORS, monta el Dashboard, registra routers

frontend/      -> Dashboard (HTML/CSS/JS vanilla + fetch a la API)
tests/         -> smoke_test.py: prueba end-to-end con datos de Silvabarber
deploy/        -> systemd + nginx para el VPS
```

## Cómo correrlo localmente

> **Requisito de versión:** usa Python 3.11 o 3.12. Python 3.13+ (y en
> particular 3.14) puede fallar al instalar `pydantic-core` en Windows
> porque todavía no existe wheel precompilado para esas versiones tan
> nuevas, y pip intenta compilarlo desde el código fuente (falla si no
> tienes el toolchain de Rust instalado). Si tienes varias versiones de
> Python instaladas, crea el venv apuntando explícitamente a la correcta:
> `py -3.12 -m venv .venv`

```bash
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # y completa tus credenciales

uvicorn app.main:app --reload
```

Al levantar, SQLAlchemy crea automáticamente `nilo_ai.db` con las 8 tablas
del diccionario de datos.

- API y documentación interactiva: `http://127.0.0.1:8000/docs`
- Dashboard: `http://127.0.0.1:8000/dashboard/`

La primera vez que inicias sesión en el Dashboard, si tu cuenta no tiene
ningún negocio creado, se crea uno automáticamente ("Mi negocio") para que
puedas seguir configurando desde ahí — no queda una pantalla vacía.

## Pruebas end-to-end

Con el backend corriendo en otra terminal:

```bash
python tests/smoke_test.py
```

Recorre el journey completo con datos realistas de Silvabarber: registro,
negocio, catálogo, contexto, conexión WhatsApp, bot encendido, mensaje
entrante simulado, verificación del historial, agenda, y aislamiento
multitenant entre negocios. Es buena práctica correrlo antes de cada
despliegue y después de cualquier cambio grande en los routers.

## Mapeo requerimiento -> archivo

| RF/RNF | Dónde vive |
|---|---|
| RF-01 Autenticación | `routers/auth.py`, `core/security.py` (JWT + bcrypt) |
| RF-02 Perfil del negocio | `routers/negocio.py` |
| RF-03 Inyección de contexto | `routers/contexto.py`, `models/contexto_ia.py`, `models/servicio.py` — en el Dashboard: bloques "Personificación" / "Catálogo & Precios" / "Reglas del Local" |
| RF-04 Control on/off del bot | `routers/negocio.py` (`estado_bot`) |
| RF-05 Historial de logs | `routers/conversaciones.py` |
| RF-06 Recepción de webhooks | `routers/webhook.py`, `services/whatsapp_service.py` |
| RF-07 Prompt dinámico | `services/ai_service.py` (`armar_prompt`) |
| RF-08 Procesamiento NLP | `services/ai_service.py` (`generar_respuesta`, Gemini/OpenAI) — en el Dashboard: bloque "Motor de IA" (proveedor + modelo por negocio) |
| RF-09 Envío de respuesta | `services/whatsapp_service.py` (`enviar_mensaje`) |
| RNF-01 Latencia < 15s | `core/config.py` (`MAX_RESPONSE_LATENCY_SECONDS`), timeout en `ai_service.py` |
| RNF-02 Multitenant | `id_negocio` como FK + `core/deps.py` (`obtener_negocio_propio`) |

## Despliegue en el VPS (producción)

Pensado para un VPS chico (2 vCPU / 2GB RAM), con Nginx como proxy reverso
y gunicorn+uvicorn corriendo la app como servicio del sistema.

1. **Preparar el servidor**
   ```bash
   sudo apt update && sudo apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx
   sudo adduser --system --group nilo
   ```

2. **Subir el código y crear el entorno**
   ```bash
   git clone <tu-repo> /home/nilo/nilo-ai-backend
   cd /home/nilo/nilo-ai-backend
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   cp .env.example .env   # completar con las credenciales reales de producción
   ```

3. **Servicio systemd** — copia `deploy/nilo-ai.service` a
   `/etc/systemd/system/nilo-ai.service`, ajusta usuario/rutas si difieren, y:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now nilo-ai
   sudo systemctl status nilo-ai
   ```

4. **Nginx + HTTPS** — copia `deploy/nginx.conf` a
   `/etc/nginx/sites-available/nilo-ai`, ajusta `server_name` a tu dominio:
   ```bash
   sudo ln -s /etc/nginx/sites-available/nilo-ai /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   sudo certbot --nginx -d tu-dominio.cl
   ```
   HTTPS no es opcional acá: Meta **rechaza** webhooks de WhatsApp que no
   sean HTTPS.

5. **Configurar el webhook en Meta for Developers** — en la sección
   WhatsApp > Configuration de tu app, el Callback URL es
   `https://tu-dominio.cl/webhook` y el Verify Token es el mismo valor que
   pusiste en `WHATSAPP_VERIFY_TOKEN` del `.env`.

6. **Verificar que quedó arriba**
   ```bash
   curl https://tu-dominio.cl/
   python tests/smoke_test.py   # apuntando BASE_URL a tu dominio
   ```

### Después de cada actualización de código

```bash
cd /home/nilo/nilo-ai-backend
git pull
.venv/bin/pip install -r requirements.txt
sudo systemctl restart nilo-ai
python tests/smoke_test.py
```

## Notas de seguridad para producción

- Genera un `SECRET_KEY` real y único (no el placeholder del `.env.example`):
  `python -c "import secrets; print(secrets.token_hex(32))"`
- El `whatsapp_token` de cada negocio se guarda hoy en texto plano en la
  BD — antes de producción real conviene cifrarlo en reposo (ej. con
  `cryptography.fernet`) o moverlo a un secret manager.
- Cambia `CORS_ALLOWED_ORIGINS` de `*` al dominio real del Dashboard una
  vez que esté desplegado.
