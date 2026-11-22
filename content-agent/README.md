# BIO-PRECISE™ Content Agent

Agente automático de contenido para @dra.gabriela.escobar

## Flujo

```
Agente genera carrusel
       ↓
Envía preview a Martín (Telegram)
       ↓
✅ Martín aprueba
       ↓
Envía a Dra. Gabriela (Telegram)
       ↓
✅ Gabriela aprueba → Publica en Instagram
```

## Configuración

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Crear archivo `.env`:
```bash
cp .env.example .env
# Editar .env con tus API keys
```

3. Cargar variables:
```powershell
# Windows (PowerShell) — ejecutar antes de cada sesión
$env:ANTHROPIC_API_KEY="sk-ant-..."
$env:TELEGRAM_TOKEN="..."
$env:CHAT_ID_MARTIN="7748141218"
$env:CHAT_ID_GABRIELA="9050271109"
$env:WINDSOR_API_KEY="..."
$env:INSTAGRAM_ACCOUNT_ID="17841443626145377"
$env:CANVA_API_TOKEN="..."   # Ver sección Canva API más abajo
```

```bash
# Linux/Mac
export ANTHROPIC_API_KEY="sk-ant-..."
export CANVA_API_TOKEN="..."
```

## Uso

```bash
# Con tema aleatorio
python agent.py

# Con tema específico
python agent.py "Resistencia a la insulina: la causa silenciosa del sobrepeso"
```

## Programar ejecución (3x por semana)

**Windows (Task Scheduler):**
- Lunes, Miércoles, Viernes a las 8:00 AM
- Acción: `python C:\Users\gabri\dra-gabriela\content-agent\agent.py`

**Linux/Mac (cron):**
```
0 8 * * 1,3,5 cd /path/to/content-agent && python agent.py
```

## Telegram Bot

- Bot: @bioprecise_content_bot
- Chat IDs configurados en `.env` (ver `.env.example`)

## Canva API — Imágenes profesionales

El agente genera imágenes usando el diseño base de Canva `DAHbl3rVzzQ` ("Señales de insulina").

**Obtener CANVA_API_TOKEN:**
1. Ir a https://www.canva.com/settings/apps
2. Canva Connect → Personal Access Token
3. Crear token con permisos: `design:content:read`, `design:content:write`, `design:meta:read`, `asset:read`

**Fallback:** Si Canva no está disponible, el agente usa imágenes básicas (Pillow).

## Notas

- El agente espera hasta 24h por cada aprobación
- Si Martín o Gabriela solicitan cambios, el agente aborta y notifica
- Diseño base Canva: `DAHbl3rVzzQ` — 8 páginas BIO-PRECISE™
- El agente copia el diseño, edita el texto y exporta como PNG para cada carrusel
