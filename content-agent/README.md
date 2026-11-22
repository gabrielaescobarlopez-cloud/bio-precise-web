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
```bash
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-..."
$env:WINDSOR_API_KEY="..."

# Linux/Mac
export ANTHROPIC_API_KEY="sk-ant-..."
export WINDSOR_API_KEY="..."
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
- Martín chat_id: 7748141218
- Gabriela chat_id: 9050271109

## Notas

- El agente espera hasta 24h por cada aprobación
- Si Martín o Gabriela solicitan cambios, el agente aborta y notifica
- Para publicar imágenes reales, integrar con Canva MCP para exportar las slides
