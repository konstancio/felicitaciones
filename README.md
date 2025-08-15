# WhatsApp Greetings (Railway + WhatsApp Cloud API)

Envío automático de felicitaciones de **cumpleaños** y **santos** por WhatsApp a las **09:00 locales de cada contacto**, con **multiidioma** y **multizona horaria**. Preparado para desplegar en **Railway**.

---

## 1) Requisitos

- Cuenta en **Meta Developers** con **WhatsApp Cloud API** activa.
- Un **número remitente** configurado y un **token permanente**.
- **Plantillas** (message templates) creadas y aprobadas (mismo nombre para todos los idiomas):
  - `feliz_cumple`
  - `feliz_santo`
- Cuenta en **GitHub** y **Railway**.

> Nota: WhatsApp Cloud API **no expone la localización ni la zona horaria** del destinatario. Por eso este bot usa la **zona horaria guardada por contacto** (o la infiere por prefijo del teléfono como aproximación).

---

## 2) Estructura del proyecto

```
.
├─ app/
│  ├─ main.py
│  ├─ events.csv
│  └─ settings.example.env
├─ requirements.txt
├─ Procfile
├─ .gitignore
└─ README.md
```

- `app/events.csv`: tu agenda de destinatarios.
- `app/main.py`: lógica de envíos a las 09:00 locales de cada contacto.
- `Procfile`: proceso tipo “worker” para Railway.
- `requirements.txt`: dependencias de Python.

---

## 3) Variables de entorno (Railway → Variables)

Crea estas claves:

- `META_WA_TOKEN` → **token permanente** de WhatsApp Cloud API.
- `WABA_PHONE_NUMBER_ID` → ID del **número remitente**.
- `WA_API_VERSION` → por ejemplo `v21.0`.
- `SENDER_NAME` → tu firma (ej.: `Consta`).

Opcional en local: copia `app/settings.example.env` a `app/settings.env` y rellénalo (no subas tus secretos).

---

## 4) Plantillas multiidioma (en WhatsApp Cloud API)

Nombre único por tipo, con traducciones aprobadas en los idiomas que uses (`es`, `en`, `fr`, ...). Cuerpo sugerido (parámetros `{{1}} = nombre`, `{{2}} = firma`):

- `feliz_cumple`
  - **es**: `¡Feliz cumpleaños, {{1}}! 🎉 Que tengas un día estupendo. Un abrazo, {{2}}.`
  - **en**: `Happy birthday, {{1}}! 🎉 Have a fantastic day. Hugs, {{2}}.`
  - **fr**: `Joyeux anniversaire, {{1}} ! 🎉 Passe une excellente journée. Amitiés, {{2}}.`

- `feliz_santo`
  - **es**: `¡Felicidades por tu santo, {{1}}! 🙌 Que pases un gran día. Un abrazo, {{2}}.`
  - **en**: `Happy name day, {{1}}! 🙌 Wishing you a great day. Hugs, {{2}}.`
  - **fr**: `Bonne fête, {{1}} ! 🙌 Passe une très bonne journée. Amitiés, {{2}}.`

---

## 5) `app/events.csv` (agenda)

Columnas obligatorias:

```
name,phone,event_type,date,lang,tz
```

- `event_type`: `cumple` o `santo`
- `date`: cumpleaños `YYYY-MM-DD` (se usa mes y día) o santo `----MM-DD`
- `lang`: código de idioma de la plantilla (`es`, `en`, `fr`, ...)
- `tz`: zona horaria IANA (`Europe/Madrid`, `America/Los_Angeles`, ...). Si la dejas vacía, el bot intenta inferirla por prefijo del teléfono (aprox.).

Este repo ya incluye un `events.csv` de ejemplo (tus datos).

---

## 6) Despliegue en Railway (cron cada 10 minutos)

1. **Sube este repo a GitHub**.
2. En Railway: **New Project → Deploy from GitHub Repo** (selecciona este repo).
3. Ve a **Variables** y añade: `META_WA_TOKEN`, `WABA_PHONE_NUMBER_ID`, `WA_API_VERSION`, `SENDER_NAME`.
4. Crea un **Scheduled Job** con cron `*/10 * * * *` y comando:
   ```
   railway run python -m app.main
   ```
   El script sólo envía cuando es **09:00–09:09 locales** del contacto.

> Alternativa: `*/15` y cambiar la ventana en el código a `range(0, 15)`.

---

## 7) Prueba rápida

- Edita temporalmente `within_local_window` en `main.py` para que acepte la hora actual de tu zona y lanza el job manualmente desde Railway (`Run`).
- Revisa los logs: verás `[OK] +34... -> feliz_cumple (es) 200` si todo ha ido bien.

---

## 8) Seguridad y buen uso

- Usa **plantillas** para iniciar conversaciones (política de WhatsApp).
- Respeta el consentimiento de tus contactos.
- Protege tu `META_WA_TOKEN` (no lo subas al repo).

---

## 9) Licencia

Este ejemplo se publica sin garantía; úsalo bajo tu responsabilidad.
