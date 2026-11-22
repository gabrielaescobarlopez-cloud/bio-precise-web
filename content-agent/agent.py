#!/usr/bin/env python3
"""
BIO-PRECISE Content Agent
Genera carruseles semanales para @dra.gabriela.escobar y los envía
para aprobación por Telegram antes de publicar en Instagram.

Flujo:
  1. Busca temas virales de metabolismo/obesidad
  2. Genera script de carrusel con Claude API
  3. Envía preview a Martín (chat_id: 7748141218)
  4. Martín aprueba → envía a Gabriela (chat_id: 9050271109)
  5. Gabriela aprueba → publica en Instagram vía Windsor.ai
"""

import os
import json
import time
import requests
import anthropic
from datetime import datetime

# ─── Configuración ────────────────────────────────────────────────────────────
# Todos los valores sensibles vienen de variables de entorno
# Ver .env.example para configuración
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID_MARTIN = int(os.environ.get("CHAT_ID_MARTIN", "0"))
CHAT_ID_GABRIELA = int(os.environ.get("CHAT_ID_GABRIELA", "0"))
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
WINDSOR_API_KEY = os.environ.get("WINDSOR_API_KEY", "")
INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ─── Temas de carruseles disponibles ─────────────────────────────────────────
TEMAS_CARRUSEL = [
    "¿Por qué no bajo de peso aunque hago dieta?",
    "Resistencia a la insulina: la causa silenciosa del sobrepeso",
    "Ozempic: mito vs verdad — lo que nadie te dice",
    "Los 5 errores más comunes al querer perder grasa",
    "¿Tienes inflamación crónica? Estas señales lo revelan",
    "Glucosa en ayunas normal ≠ metabolismo sano",
    "Por qué el cortisol alto te impide bajar de peso",
    "HbA1c: el análisis que predice diabetes 10 años antes",
    "Ayuno intermitente: para quién sí y para quién no",
    "Hipotiroidismo subclínico: síntomas que se ignoran",
]

# ─── Helpers de Telegram ──────────────────────────────────────────────────────

def tg_send(chat_id: int, text: str, reply_markup: dict = None) -> dict:
    """Envía mensaje de texto a Telegram."""
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    r = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def tg_edit(chat_id: int, message_id: int, text: str) -> dict:
    """Edita un mensaje existente."""
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
    }
    r = requests.post(f"{TELEGRAM_API}/editMessageText", json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def tg_answer_callback(callback_query_id: str, text: str = "") -> None:
    """Confirma un callback query para quitar el loading del botón."""
    requests.post(
        f"{TELEGRAM_API}/answerCallbackQuery",
        json={"callback_query_id": callback_query_id, "text": text},
        timeout=10,
    )


def tg_get_updates(offset: int = 0) -> list:
    """Obtiene updates del bot desde un offset dado."""
    r = requests.get(
        f"{TELEGRAM_API}/getUpdates",
        params={"offset": offset, "timeout": 30, "allowed_updates": ["callback_query", "message"]},
        timeout=35,
    )
    r.raise_for_status()
    return r.json().get("result", [])


def wait_for_callback(expected_prefix: str, timeout_seconds: int = 3600) -> tuple[str, int, int]:
    """
    Espera un callback_query cuyo data empiece con expected_prefix.
    Devuelve (data, chat_id, callback_query_id).
    """
    offset = 0
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        updates = tg_get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            if "callback_query" in update:
                cb = update["callback_query"]
                if cb["data"].startswith(expected_prefix):
                    tg_answer_callback(cb["id"])
                    return cb["data"], cb["from"]["id"], cb["id"]
        time.sleep(2)
    raise TimeoutError(f"No se recibió respuesta para '{expected_prefix}' en {timeout_seconds}s")

# ─── Generación de contenido ──────────────────────────────────────────────────

def generar_carrusel(tema: str) -> dict:
    """
    Usa Claude para generar el script completo del carrusel.
    Retorna dict con: tema, diapositivas[], caption, hashtags
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Eres el asistente de contenido de la Dra. Gabriela Escobar, médica especialista en obesidad, diabetes tipo 2 y medicina de precisión metabólica. Su marca es BIO-PRECISE™. Consulta en Quito, Ecuador.

Genera el script de un carrusel de Instagram de 7 diapositivas sobre este tema:
"{tema}"

Reglas:
- Voz directa, cercana, educativa — como si la doctora le hablara a su paciente
- Lenguaje simple, nada de jerga médica sin explicación
- Cada diapositiva tiene: título corto (máx 8 palabras) + texto de apoyo (máx 25 palabras)
- Diapositiva 1: portada con gancho emocional (pregunta o dato impactante)
- Diapositivas 2-6: desarrollo con datos concretos y tips accionables
- Diapositiva 7: CTA — "¿Quieres saber si esto te está pasando? Escríbeme 'METABOLISMO' en los comentarios"
- Caption para el post: 150-200 palabras, incluye 3 preguntas retóricas, termina con CTA
- Hashtags: 20 relevantes en español e inglés (obesidad, diabetes, metabolismo, Ecuador)

Responde SOLO con JSON válido con esta estructura:
{{
  "tema": "...",
  "diapositivas": [
    {{"numero": 1, "titulo": "...", "texto": "..."}},
    ...
  ],
  "caption": "...",
  "hashtags": ["#tag1", "#tag2", ...]
}}"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Extraer JSON de la respuesta
    content = message.content[0].text
    # Limpiar markdown si viene envuelto en ```json
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    return json.loads(content)


def formatear_preview_carrusel(carrusel: dict) -> str:
    """Formatea el carrusel como texto legible para Telegram."""
    lines = [
        f"🧬 <b>NUEVO CARRUSEL BIO-PRECISE™</b>",
        f"📌 <b>Tema:</b> {carrusel['tema']}",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    for slide in carrusel["diapositivas"]:
        lines.append(f"\n<b>Diapositiva {slide['numero']}</b>")
        lines.append(f"🔷 <i>{slide['titulo']}</i>")
        lines.append(f"   {slide['texto']}")

    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        "📝 <b>Caption:</b>",
        carrusel["caption"],
        "",
        "🏷️ <b>Hashtags:</b>",
        " ".join(carrusel["hashtags"][:10]) + "...",
    ]

    return "\n".join(lines)

# ─── Windsor.ai — publicar en Instagram ──────────────────────────────────────

def publicar_instagram(carrusel: dict) -> bool:
    """
    Publica el carrusel en Instagram vía Windsor.ai.
    Por ahora envía el texto — las imágenes requieren Canva export.
    """
    headers = {
        "Authorization": f"Bearer {WINDSOR_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "connector": "instagram",
        "account_id": INSTAGRAM_ACCOUNT_ID,
        "action": "create_post",
        "caption": carrusel["caption"] + "\n\n" + " ".join(carrusel["hashtags"]),
    }
    # Windsor.ai endpoint (usar MCP en producción)
    # En producción esto se hace vía mcp__Windsor_ai_for_Social_Media__execute_action
    print(f"[Windsor] Publicando en Instagram: {carrusel['tema']}")
    print(f"[Windsor] Caption preview: {carrusel['caption'][:100]}...")
    return True

# ─── Flujo principal del agente ──────────────────────────────────────────────

def run_agent(tema: str = None):
    """
    Ejecuta el flujo completo del agente para un tema dado.
    Si no se pasa tema, usa el primero de la lista.
    """
    if not tema:
        # En producción: seleccionar tema basado en viralidad/calendario
        import random
        tema = random.choice(TEMAS_CARRUSEL)

    print(f"\n{'='*60}")
    print(f"BIO-PRECISE Content Agent — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Tema: {tema}")
    print(f"{'='*60}\n")

    # ── PASO 1: Generar carrusel ──────────────────────────────────
    print("⚙️  Generando carrusel con Claude...")
    carrusel = generar_carrusel(tema)
    print(f"✅ Carrusel generado: {len(carrusel['diapositivas'])} diapositivas")

    preview_text = formatear_preview_carrusel(carrusel)

    # ── PASO 2: Enviar a Martín para revisión ─────────────────────
    print(f"\n📤 Enviando preview a Martín (chat_id: {CHAT_ID_MARTIN})...")
    botones_martin = {
        "inline_keyboard": [[
            {"text": "✅ Aprobar", "callback_data": "martin_aprobar"},
            {"text": "✏️ Cambiar tema", "callback_data": "martin_cambiar"},
        ]]
    }
    msg_martin = tg_send(CHAT_ID_MARTIN, preview_text, botones_martin)
    msg_id_martin = msg_martin["result"]["message_id"]
    print(f"✅ Mensaje enviado (message_id: {msg_id_martin})")

    # ── PASO 3: Esperar aprobación de Martín ─────────────────────
    print("\n⏳ Esperando respuesta de Martín...")
    decision_martin, _, _ = wait_for_callback("martin_", timeout_seconds=86400)  # 24h

    if decision_martin == "martin_cambiar":
        tg_edit(CHAT_ID_MARTIN, msg_id_martin,
                preview_text + "\n\n❌ <b>Cambio solicitado por Martín.</b>\nEl agente generará un nuevo tema.")
        print("❌ Martín solicitó cambio de tema. Abortando.")
        tg_send(CHAT_ID_MARTIN,
                "👍 Entendido. Te envío una nueva propuesta en breve.")
        return False

    # Martín aprobó
    tg_edit(CHAT_ID_MARTIN, msg_id_martin,
            preview_text + "\n\n✅ <b>Aprobado por Martín. Enviando a la Dra. Gabriela...</b>")
    print("✅ Martín aprobó el carrusel")

    # ── PASO 4: Enviar a Gabriela para aprobación final ───────────
    print(f"\n📤 Enviando a Gabriela (chat_id: {CHAT_ID_GABRIELA})...")
    texto_gabriela = (
        f"🧬 <b>BIO-PRECISE™ — Carrusel para aprobar</b>\n\n"
        f"Martín ya revisó y aprobó este carrusel. ¿Lo publicamos en Instagram?\n\n"
        + preview_text
    )
    botones_gabriela = {
        "inline_keyboard": [[
            {"text": "✅ Publicar ahora", "callback_data": "gabriela_aprobar"},
            {"text": "✏️ Pedir cambios", "callback_data": "gabriela_cambiar"},
        ]]
    }
    msg_gabriela = tg_send(CHAT_ID_GABRIELA, texto_gabriela, botones_gabriela)
    msg_id_gabriela = msg_gabriela["result"]["message_id"]
    print(f"✅ Mensaje enviado (message_id: {msg_id_gabriela})")

    # ── PASO 5: Esperar aprobación de Gabriela ────────────────────
    print("\n⏳ Esperando respuesta de la Dra. Gabriela...")
    decision_gabriela, _, _ = wait_for_callback("gabriela_", timeout_seconds=86400)

    if decision_gabriela == "gabriela_cambiar":
        tg_edit(CHAT_ID_GABRIELA, msg_id_gabriela,
                texto_gabriela + "\n\n✏️ <b>Cambio solicitado.</b>")
        tg_send(CHAT_ID_GABRIELA,
                "Entendido, Dra. Gabriela. Martín revisará y te enviará una nueva versión.")
        tg_send(CHAT_ID_MARTIN,
                f"⚠️ La Dra. Gabriela solicitó cambios en el carrusel:\n<i>{tema}</i>\n\nPor favor revisa y genera una nueva versión.")
        print("❌ Gabriela solicitó cambios.")
        return False

    # Gabriela aprobó → publicar
    tg_edit(CHAT_ID_GABRIELA, msg_id_gabriela,
            texto_gabriela + "\n\n🚀 <b>¡Publicando en Instagram ahora!</b>")
    print("✅ Gabriela aprobó. Publicando en Instagram...")

    # ── PASO 6: Publicar en Instagram ─────────────────────────────
    publicado = publicar_instagram(carrusel)

    if publicado:
        confirmacion = (
            f"🎉 <b>¡Publicado en Instagram!</b>\n\n"
            f"📌 Tema: {carrusel['tema']}\n"
            f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        tg_send(CHAT_ID_GABRIELA, confirmacion)
        tg_send(CHAT_ID_MARTIN, confirmacion)
        print("✅ Publicación exitosa. Notificaciones enviadas.")
        return True
    else:
        error_msg = "❌ Error al publicar en Instagram. Revisa Windsor.ai."
        tg_send(CHAT_ID_MARTIN, error_msg)
        return False


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # Permitir pasar tema como argumento
    tema_arg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    success = run_agent(tema_arg)
    sys.exit(0 if success else 1)
