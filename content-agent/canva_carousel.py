#!/usr/bin/env python3
"""
canva_carousel.py — Genera imágenes de carrusel usando Canva API

Flujo por carrusel:
  1. Copia el diseño base (DAHbl3rVzzQ) → nuevo diseño temporal
  2. Para cada diapositiva (1-7): edita el texto vía find_and_replace_text
  3. Exporta el diseño como PNGs individuales
  4. Descarga los PNGs a /tmp/bio-precise-canva-{hash}/
  5. Retorna lista de rutas locales

Requiere:
  CANVA_API_TOKEN en variables de entorno
"""

import os
import re
import time
import hashlib
import tempfile
import requests
from pathlib import Path

# ─── Configuración ────────────────────────────────────────────────────────────
CANVA_API_TOKEN = os.environ.get("CANVA_API_TOKEN", "")
CANVA_API_BASE = "https://api.canva.com/rest/v1"

# ID del diseño base "Señales de insulina" — 8 páginas BIO-PRECISE™
DESIGN_ID_BASE = "DAHbl3rVzzQ"

# Mapeo de textos originales del diseño base → locator_id aproximado
# Estos se obtienen del read-design y se usan con find_and_replace_text
# El diseño tiene esta estructura de texto por página:
# Página 1: portada (título gancho + subtítulo + "DESLIZA PARA DESCUBRIRLO")
# Páginas 2-6: número + título + texto de apoyo
# Página 7: estadística / dato impactante
# Página 8: CTA final

# Textos originales del diseño base por página (para find_and_replace)
TEXTOS_ORIGINALES = {
    1: {
        "titulo": "¿Tu cuerpo te está mandando\nseñales?",
        "subtitulo": "síntomas de resistencia a la insulina que ignoras.",
    },
    2: {"numero": "01", "titulo": "Cansancio después de comer", "texto": "Si te da sueño 1-2 horas después de comer,tu insulina podría estar fallando al llevar glucosa a las células."},
    3: {"numero": "02", "titulo": "Grasa abdominal que no cede", "texto": "No es falta de voluntad.Es tu metabolismo bloqueado por excesode insulina que promueve almacenamiento de grasa."},
    4: {"numero": "03", "titulo": "Antojos\nde dulce\nconstantes", "texto": "Tu cerebro pide glucosaporque las célulasno la pueden usar.\nEl ciclo no termina sin intervención."},
    5: {"numero": "04", "titulo": "Manchas oscuras en cuello o axilas", "texto": "Acantosis nigricans\nseñal de alarma real que muchos médicos pasan por alto en consulta."},
    6: {"numero": "05", "titulo": "Niebla\nmental", "texto": "La glucosa es combustible del cerebro.\nSi tu insulina falla,\ntu mente también:\nmemoria, concentración, claridad."},
    7: {"stat": "1\nde cada\n3\nadultos\ntiene resistencia\na la insulina\nsin saberlo."},
    8: {"cta": "¿Tienes 2 omás señales?\ncomenta \nmetabolismo \ncon flecha abajo.\ny te digo qué análisis pedir."},
}


def _headers() -> dict:
    """Headers para Canva REST API."""
    return {
        "Authorization": f"Bearer {CANVA_API_TOKEN}",
        "Content-Type": "application/json",
    }


def _copy_design(design_id: str) -> str:
    """Duplica un diseño y retorna el nuevo design_id."""
    r = requests.post(
        f"{CANVA_API_BASE}/designs/{design_id}/copies",
        headers=_headers(),
        json={},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    new_id = data.get("design", {}).get("id") or data.get("id")
    if not new_id:
        raise ValueError(f"No se pudo obtener ID del diseño copiado: {data}")
    return new_id


def _start_transaction(design_id: str) -> str:
    """Inicia una transacción de edición y retorna transaction_id."""
    r = requests.post(
        f"{CANVA_API_BASE}/designs/{design_id}/editing-sessions",
        headers=_headers(),
        json={},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    tx_id = data.get("editing_session_id") or data.get("transaction_id") or data.get("session", {}).get("id")
    if not tx_id:
        raise ValueError(f"No se obtuvo transaction_id: {data}")
    return tx_id


def _apply_text_replacement(design_id: str, tx_id: str, page_index: int,
                             find_text: str, replace_text: str, locator_id: str = None) -> None:
    """Aplica find_and_replace_text en una página del diseño."""
    op = {
        "type": "find_and_replace_text",
        "find_text": find_text,
        "replace_text": replace_text,
    }
    if locator_id:
        op["locator_id"] = locator_id

    payload = {
        "transaction_id": tx_id,
        "page_index": page_index,
        "finalize": "keep_open",
        "operations": [op],
    }
    r = requests.patch(
        f"{CANVA_API_BASE}/designs/{design_id}/pages/{page_index}",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    # Ignorar errores 404 en elementos que no existen en esa página
    if r.status_code not in (200, 201, 204, 404):
        r.raise_for_status()


def _commit_transaction(design_id: str, tx_id: str) -> None:
    """Confirma todos los cambios de la transacción."""
    payload = {
        "transaction_id": tx_id,
        "finalize": "commit",
    }
    r = requests.patch(
        f"{CANVA_API_BASE}/designs/{design_id}/pages/1",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    if r.status_code not in (200, 201, 204):
        r.raise_for_status()


def _export_design_png(design_id: str, pages: list[int] = None) -> list[str]:
    """
    Exporta el diseño como PNGs y retorna lista de URLs de descarga.
    pages: lista 1-based de páginas a exportar. None = todas.
    """
    payload: dict = {"format": {"type": "png", "export_quality": "pro"}}
    if pages:
        payload["format"]["pages"] = pages

    r = requests.post(
        f"{CANVA_API_BASE}/designs/{design_id}/exports",
        headers=_headers(),
        json=payload,
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()

    # El export puede ser asíncrono — polling hasta completar
    export_id = data.get("job", {}).get("id") or data.get("export_id") or data.get("id")
    if export_id:
        return _poll_export(design_id, export_id)

    # Si ya hay URLs directas
    urls = _extract_urls(data)
    if urls:
        return urls

    raise ValueError(f"Respuesta de export inesperada: {data}")


def _poll_export(design_id: str, export_id: str, max_wait: int = 120) -> list[str]:
    """Espera hasta que el export asíncrono esté listo y retorna las URLs."""
    deadline = time.time() + max_wait
    while time.time() < deadline:
        r = requests.get(
            f"{CANVA_API_BASE}/designs/{design_id}/exports/{export_id}",
            headers=_headers(),
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        status = (data.get("job", {}).get("status") or
                  data.get("status") or
                  data.get("export", {}).get("status", ""))
        if status in ("success", "complete", "completed"):
            return _extract_urls(data)
        if status in ("failed", "error"):
            raise RuntimeError(f"Export falló: {data}")
        time.sleep(3)
    raise TimeoutError(f"Export {export_id} no completó en {max_wait}s")


def _extract_urls(data: dict) -> list[str]:
    """Extrae URLs de descarga de la respuesta de export."""
    urls = []
    # Buscar en diferentes estructuras posibles de la API
    for key in ("urls", "download_urls", "pages"):
        if key in data:
            val = data[key]
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        urls.append(item)
                    elif isinstance(item, dict):
                        url = item.get("url") or item.get("download_url") or item.get("href")
                        if url:
                            urls.append(url)
    # Buscar recursivamente en job/export
    for sub in ("job", "export"):
        if sub in data and isinstance(data[sub], dict):
            urls.extend(_extract_urls(data[sub]))
    return urls


def _download_pngs(urls: list[str], output_dir: str) -> list[str]:
    """Descarga las URLs PNG a output_dir y retorna rutas locales."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    paths = []
    for i, url in enumerate(urls, 1):
        path = os.path.join(output_dir, f"slide_{i:02d}.png")
        r = requests.get(url, timeout=60, stream=True)
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        paths.append(path)
        print(f"  ✅ slide_{i:02d}.png descargado")
    return paths


def _limpiar_texto(texto: str) -> str:
    """Limpia texto para usarlo en Canva (sin saltos innecesarios)."""
    return texto.strip()


def generar_carrusel_canva(carrusel: dict) -> list[str]:
    """
    Genera imágenes de carrusel usando Canva API.

    Args:
        carrusel: dict con tema, diapositivas[], caption, hashtags

    Returns:
        Lista de rutas locales a los PNGs generados (1 por diapositiva)

    Raises:
        RuntimeError si falla la generación
    """
    tema = carrusel.get("tema", "carrusel")
    diapositivas = carrusel.get("diapositivas", [])

    # Directorio de salida basado en hash del tema
    short_hash = hashlib.md5(tema.encode()).hexdigest()[:8]
    output_dir = os.path.join(tempfile.gettempdir(), f"bio-precise-canva-{short_hash}")

    print(f"\n🎨 Generando carrusel Canva para: {tema}")
    print(f"   Output: {output_dir}")

    # ── PASO 1: Copiar el diseño base ──────────────────────────────
    print(f"\n📋 Copiando diseño base ({DESIGN_ID_BASE})...")
    new_design_id = _copy_design(DESIGN_ID_BASE)
    print(f"   ✅ Nuevo diseño: {new_design_id}")

    # Dar tiempo a que Canva propague la copia
    time.sleep(2)

    # ── PASO 2: Editar texto de cada diapositiva ───────────────────
    print(f"\n✏️  Editando textos ({len(diapositivas)} diapositivas)...")

    # Iniciar transacción de edición
    tx_id = _start_transaction(new_design_id)
    print(f"   Transaction ID: {tx_id}")

    for slide in diapositivas:
        num = slide.get("numero", 1)
        titulo_nuevo = _limpiar_texto(slide.get("titulo", ""))
        texto_nuevo = _limpiar_texto(slide.get("texto", ""))

        # Página 1: portada
        if num == 1:
            original = TEXTOS_ORIGINALES[1]
            if titulo_nuevo and original["titulo"]:
                _apply_text_replacement(new_design_id, tx_id, 1,
                    original["titulo"], titulo_nuevo)
            if texto_nuevo and original["subtitulo"]:
                _apply_text_replacement(new_design_id, tx_id, 1,
                    original["subtitulo"], texto_nuevo)
            print(f"   ✅ Página 1 (portada): '{titulo_nuevo[:40]}...'")

        # Páginas 2-6: slides de contenido (numero 2-6 → páginas 2-6)
        elif 2 <= num <= 6:
            page_idx = num  # página = número de diapositiva
            orig = TEXTOS_ORIGINALES.get(page_idx, {})
            # Reemplazar título
            if titulo_nuevo and orig.get("titulo"):
                _apply_text_replacement(new_design_id, tx_id, page_idx,
                    orig["titulo"], titulo_nuevo)
            # Reemplazar texto de apoyo
            if texto_nuevo and orig.get("texto"):
                _apply_text_replacement(new_design_id, tx_id, page_idx,
                    orig["texto"], texto_nuevo)
            print(f"   ✅ Página {page_idx}: '{titulo_nuevo[:40]}'")

        # Diapositiva 7: CTA
        elif num == 7:
            orig = TEXTOS_ORIGINALES.get(8, {})
            if texto_nuevo and orig.get("cta"):
                _apply_text_replacement(new_design_id, tx_id, 8,
                    orig["cta"], texto_nuevo)
            print(f"   ✅ Página 8 (CTA): '{texto_nuevo[:40]}...'")

    # ── PASO 3: Confirmar cambios ──────────────────────────────────
    print("\n💾 Guardando cambios...")
    _commit_transaction(new_design_id, tx_id)
    print("   ✅ Cambios guardados")

    # Esperar a que Canva procese los cambios
    time.sleep(3)

    # ── PASO 4: Exportar páginas como PNG ─────────────────────────
    # Exportar solo las páginas que usamos (1-6 y 8, omitir página 7 de estadística)
    pages_to_export = [1, 2, 3, 4, 5, 6, 8]
    print(f"\n📤 Exportando {len(pages_to_export)} páginas como PNG...")
    png_urls = _export_design_png(new_design_id, pages_to_export)
    print(f"   ✅ {len(png_urls)} URLs de exportación obtenidas")

    # ── PASO 5: Descargar PNGs ─────────────────────────────────────
    print(f"\n⬇️  Descargando PNGs a {output_dir}...")
    local_paths = _download_pngs(png_urls, output_dir)
    print(f"\n✅ Carrusel Canva listo: {len(local_paths)} imágenes")

    return local_paths


# ─── Test standalone ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test con un carrusel de ejemplo
    carrusel_test = {
        "tema": "Test carrusel Canva",
        "diapositivas": [
            {"numero": 1, "titulo": "¿Tu glucosa te está fallando?", "texto": "5 señales que tu médico ignora."},
            {"numero": 2, "titulo": "Fatiga post-comida", "texto": "Si te da sueño después de comer, tu insulina podría estar fallando."},
            {"numero": 3, "titulo": "Grasa abdominal rebelde", "texto": "No es voluntad. Es metabolismo bloqueado por insulina elevada."},
            {"numero": 4, "titulo": "Antojos de dulce constantes", "texto": "Tus células no reciben glucosa. El ciclo no para solo."},
            {"numero": 5, "titulo": "Manchas en cuello", "texto": "Acantosis nigricans: señal de alarma que muchos médicos ignoran."},
            {"numero": 6, "titulo": "Niebla mental", "texto": "Sin glucosa en las células, tu mente también falla."},
            {"numero": 7, "titulo": "¿Te identificas?", "texto": "Escribe METABOLISMO en los comentarios y te digo qué análisis pedir."},
        ],
        "caption": "Test caption",
        "hashtags": ["#metabolismo", "#insulina"],
    }

    paths = generar_carrusel_canva(carrusel_test)
    print("\nRutas generadas:")
    for p in paths:
        print(f"  {p}")
