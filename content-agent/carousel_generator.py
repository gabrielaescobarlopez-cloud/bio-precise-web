#!/usr/bin/env python3
"""
BIO-PRECISE™ Carousel Generator
Genera imágenes PNG de carrusel con 4 layouts rotativos para Instagram.

Paleta: navy #0D2847 | mint #5BA896 | blanco #FFFFFF | gris claro #F5F7FA
Tamaño: 1080x1080 px (cuadrado Instagram)
"""

import os
import json
import math
import hashlib
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ─── Paleta BIO-PRECISE™ ──────────────────────────────────────────────────────
NAVY    = (13, 40, 71)       # #0D2847
MINT    = (91, 168, 150)     # #5BA896
WHITE   = (255, 255, 255)
LIGHT   = (245, 247, 250)    # #F5F7FA
MINT_LIGHT = (220, 240, 236) # versión clara del mint
NAVY_MID   = (25, 65, 115)   # navy un poco más claro

SIZE = (1080, 1080)
BRAND = "BIO-PRECISE™"
HANDLE = "@dra.gabriela.escobar"

# ─── Utilidades de texto ──────────────────────────────────────────────────────

def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Carga fuente del sistema o fallback."""
    font_paths_bold = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    font_paths_regular = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ]
    paths = font_paths_bold if bold else font_paths_regular
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Divide texto en líneas que caben en max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    x: int,
    y: int,
    max_width: int,
    color: tuple,
    line_spacing: int = 8,
    align: str = "left",
) -> int:
    """Dibuja texto con salto de línea automático. Retorna y final."""
    lines = wrap_text(text, font, max_width, draw)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        if align == "center":
            lx = x - line_w // 2
        elif align == "right":
            lx = x - line_w
        else:
            lx = x
        draw.text((lx, y), line, font=font, fill=color)
        y += bbox[3] - bbox[1] + line_spacing
    return y


def draw_rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple, radius: int, fill: tuple, outline: tuple = None, width: int = 2):
    """Dibuja rectángulo redondeado."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)


def numero_layout(numero_diapositiva: int, semana_num: int) -> int:
    """
    Determina qué layout usar para esta diapositiva.
    - semana_num determina qué familia de layout se usa (rota cada semana)
    - Dentro de un carrusel, portada (1) y última (7) tienen tratamiento especial
    """
    # 4 familias de layout
    return ((semana_num - 1) % 4)


# ─── LAYOUT 0: BOLD BLOCKS ────────────────────────────────────────────────────
# Bloques grandes, tipografía masiva, color dominante en la mitad superior

def render_layout_bold(draw: ImageDraw.ImageDraw, slide: dict, es_portada: bool, es_ultima: bool, numero: int):
    """Layout Bold Blocks — navy arriba, blanco abajo, tipografía grande."""
    w, h = SIZE

    # Fondo dividido
    if es_portada:
        draw.rectangle([0, 0, w, h], fill=NAVY)
        # Bloque mint decorativo
        draw.rectangle([0, h - 220, w, h], fill=MINT)
    elif es_ultima:
        draw.rectangle([0, 0, w, h], fill=MINT)
        draw.rectangle([0, 0, w, 180], fill=NAVY)
    else:
        draw.rectangle([0, 0, w, h // 2 + 40], fill=NAVY)
        draw.rectangle([0, h // 2 + 40, w, h], fill=WHITE)

    if es_portada:
        # Número de slide pequeño
        fn_sm = load_font(22, bold=False)
        fn_brand = load_font(28, bold=True)
        fn_title = load_font(72, bold=True)
        fn_sub = load_font(32, bold=False)

        draw.text((60, 55), BRAND, font=fn_brand, fill=MINT)
        draw.text((60, 95), HANDLE, font=fn_sm, fill=(180, 200, 220))

        # Línea divisoria
        draw.rectangle([60, 140, 200, 146], fill=MINT)

        # Título grande centrado
        y_title = 200
        y_title = draw_wrapped_text(draw, slide["titulo"], fn_title, w // 2, y_title,
                                     w - 120, WHITE, line_spacing=12, align="center")

        # Texto de apoyo
        y_sub = y_title + 40
        draw_wrapped_text(draw, slide["texto"], fn_sub, w // 2, y_sub,
                          w - 160, (200, 220, 230), line_spacing=8, align="center")

        # Footer mint
        draw.text((60, h - 90), "Desliza para saber más →", font=fn_sm, fill=WHITE)

    elif es_ultima:
        fn_brand = load_font(26, bold=True)
        fn_title = load_font(58, bold=True)
        fn_sub = load_font(30, bold=False)
        fn_cta = load_font(36, bold=True)

        draw.text((60, 50), BRAND, font=fn_brand, fill=WHITE)

        y = 220
        y = draw_wrapped_text(draw, slide["titulo"], fn_title, w // 2, y,
                               w - 120, NAVY, line_spacing=10, align="center")
        y += 30
        y = draw_wrapped_text(draw, slide["texto"], fn_sub, w // 2, y,
                               w - 160, NAVY, line_spacing=8, align="center")
        y += 50

        # Caja CTA
        cta = "Escribe METABOLISMO en comentarios"
        draw_rounded_rect(draw, (120, y, w - 120, y + 90), 12, NAVY)
        draw.text((w // 2, y + 28), cta, font=fn_cta, fill=WHITE, anchor="mm")

        draw.text((w // 2, h - 60), HANDLE, font=load_font(26, bold=True), fill=WHITE, anchor="mm")

    else:
        fn_num = load_font(26, bold=True)
        fn_title = load_font(60, bold=True)
        fn_sub = load_font(30, bold=False)

        # Número de slide
        draw.text((60, 55), f"0{numero}", font=fn_num, fill=MINT)
        draw.text((60, 95), BRAND, font=load_font(22), fill=(180, 200, 220))

        y = 180
        y = draw_wrapped_text(draw, slide["titulo"], fn_title, 60, y, w - 120, WHITE, line_spacing=10)
        draw.rectangle([60, y + 20, 180, y + 26], fill=MINT)
        y += 60
        draw_wrapped_text(draw, slide["texto"], fn_sub, 60, y + 20, w - 120, NAVY, line_spacing=8)

        # Handle abajo
        draw.text((w - 60, h - 55), HANDLE, font=load_font(22), fill=(160, 180, 200), anchor="rm")


# ─── LAYOUT 1: SPLIT CARD ─────────────────────────────────────────────────────
# División vertical: barra lateral de color + contenido a la derecha

def render_layout_split(draw: ImageDraw.ImageDraw, slide: dict, es_portada: bool, es_ultima: bool, numero: int):
    """Layout Split Card — barra lateral mint/navy + card blanca."""
    w, h = SIZE

    draw.rectangle([0, 0, w, h], fill=LIGHT)

    barra_w = 180
    if es_portada or es_ultima:
        barra_w = 260

    barra_color = MINT if (numero % 2 == 0) else NAVY
    draw.rectangle([0, 0, barra_w, h], fill=barra_color)

    # Card blanca con sombra simulada
    card_x = barra_w + 60
    card_w = w - card_x - 60
    draw.rectangle([card_x - 4, 164, card_x + card_w + 4, h - 56], fill=(200, 210, 220))
    draw.rectangle([card_x, 160, card_x + card_w, h - 60], fill=WHITE)

    # Texto rotado en barra
    fn_barra = load_font(22, bold=True)
    barra_text = BRAND if not es_portada else "BIO-PRECISE™"
    # Texto vertical en barra (simplificado horizontal en la parte superior)
    draw.text((barra_w // 2, 70), barra_text, font=fn_barra,
              fill=WHITE if barra_color == MINT else MINT, anchor="mm")

    # Línea decorativa en la barra
    for i in range(5):
        y_line = 180 + i * 170
        draw.rectangle([30, y_line, barra_w - 30, y_line + 3],
                       fill=(255, 255, 255, 80) if barra_color == MINT else MINT)

    if es_portada:
        fn_num = load_font(80, bold=True)
        fn_title = load_font(54, bold=True)
        fn_sub = load_font(28, bold=False)

        # Número grande decorativo
        draw.text((card_x + 30, 180), "→", font=fn_num, fill=MINT_LIGHT)

        y = 320
        y = draw_wrapped_text(draw, slide["titulo"], fn_title, card_x + 40, y,
                               card_w - 60, NAVY, line_spacing=10)
        draw.rectangle([card_x + 40, y + 20, card_x + 160, y + 26], fill=MINT)
        y += 50
        draw_wrapped_text(draw, slide["texto"], fn_sub, card_x + 40, y,
                          card_w - 60, (80, 100, 120), line_spacing=8)

        draw.text((card_x + 40, h - 100), HANDLE, font=fn_sub, fill=(140, 160, 180))
        draw.text((card_x + 40, h - 68), "Desliza →", font=load_font(22, True), fill=MINT)

    elif es_ultima:
        fn_title = load_font(50, bold=True)
        fn_sub = load_font(28, bold=False)
        fn_cta = load_font(26, bold=True)

        y = 200
        y = draw_wrapped_text(draw, slide["titulo"], fn_title, card_x + 40, y,
                               card_w - 60, NAVY, line_spacing=10)
        y += 25
        y = draw_wrapped_text(draw, slide["texto"], fn_sub, card_x + 40, y,
                               card_w - 60, (60, 80, 100), line_spacing=8)
        y += 50

        draw_rounded_rect(draw, (card_x + 30, y, card_x + card_w - 30, y + 100), 10, NAVY)
        draw.text((card_x + card_w // 2 + 30, y + 50), "METABOLISMO en comentarios",
                  font=fn_cta, fill=WHITE, anchor="mm")

        draw.text((card_x + 40, h - 85), HANDLE, font=fn_sub, fill=MINT)

    else:
        fn_num = load_font(90, bold=True)
        fn_title = load_font(52, bold=True)
        fn_sub = load_font(28, bold=False)

        # Número grande semitransparente decorativo
        num_str = f"0{numero}"
        draw.text((card_x + card_w - 20, 170), num_str, font=fn_num,
                  fill=(230, 235, 242), anchor="rt")

        y = 200
        y = draw_wrapped_text(draw, slide["titulo"], fn_title, card_x + 40, y,
                               card_w - 80, NAVY, line_spacing=10)
        draw.rectangle([card_x + 40, y + 15, card_x + 100, y + 21], fill=MINT)
        y += 50
        draw_wrapped_text(draw, slide["texto"], fn_sub, card_x + 40, y,
                          card_w - 60, (60, 80, 100), line_spacing=8)

        draw.text((card_x + 40, h - 85), HANDLE, font=load_font(22), fill=(180, 195, 210))


# ─── LAYOUT 2: MINIMAL CLEAN ──────────────────────────────────────────────────
# Fondo blanco/gris muy limpio, tipografía elegante, detalles en mint

def render_layout_minimal(draw: ImageDraw.ImageDraw, slide: dict, es_portada: bool, es_ultima: bool, numero: int):
    """Layout Minimal Clean — fondo claro, mucho espacio, acentos mint."""
    w, h = SIZE

    if es_portada:
        draw.rectangle([0, 0, w, h], fill=NAVY)
        # Círculo decorativo grande
        cx, cy = w - 150, 200
        for r in range(300, 0, -40):
            alpha = max(0, min(255, int(255 * (1 - r / 300) * 0.15)))
            color = (91, 168, 150, alpha)
        draw.ellipse([cx - 280, cy - 280, cx + 280, cy + 280], fill=(20, 55, 100))
        draw.ellipse([cx - 180, cy - 180, cx + 180, cy + 180], fill=(30, 70, 120))
        draw.ellipse([cx - 90, cy - 90, cx + 90, cy + 90], fill=MINT)

        fn_brand = load_font(28, bold=True)
        fn_title = load_font(66, bold=True)
        fn_sub = load_font(30, bold=False)

        draw.text((70, 60), BRAND, font=fn_brand, fill=MINT)
        draw.rectangle([70, 105, 230, 111], fill=MINT)

        y = 300
        y = draw_wrapped_text(draw, slide["titulo"], fn_title, 70, y,
                               w - 180, WHITE, line_spacing=12)
        y += 30
        draw_wrapped_text(draw, slide["texto"], fn_sub, 70, y,
                          w - 180, (170, 200, 215), line_spacing=8)

        draw.text((70, h - 70), HANDLE, font=load_font(24), fill=(130, 160, 180))
        draw.text((w - 70, h - 70), "→ desliza", font=load_font(22, True), fill=MINT, anchor="rt")

    elif es_ultima:
        draw.rectangle([0, 0, w, h], fill=MINT_LIGHT)
        draw.rectangle([0, 0, w, 20], fill=MINT)
        draw.rectangle([0, h - 20, w, h], fill=MINT)

        fn_title = load_font(58, bold=True)
        fn_sub = load_font(30, bold=False)
        fn_cta = load_font(28, bold=True)

        # Icono BIO-PRECISE
        draw.ellipse([w // 2 - 55, 60, w // 2 + 55, 170], fill=MINT)
        draw.text((w // 2, 115), "🧬", font=load_font(50), fill=WHITE, anchor="mm")
        draw.text((w // 2, 200), BRAND, font=load_font(28, True), fill=NAVY, anchor="mm")

        y = 280
        y = draw_wrapped_text(draw, slide["titulo"], fn_title, w // 2, y,
                               w - 160, NAVY, line_spacing=10, align="center")
        y += 20
        y = draw_wrapped_text(draw, slide["texto"], fn_sub, w // 2, y,
                               w - 180, (40, 70, 90), line_spacing=8, align="center")
        y += 50

        draw_rounded_rect(draw, (120, y, w - 120, y + 100), 50, NAVY)
        draw.text((w // 2, y + 50), "Escribe METABOLISMO ↓", font=fn_cta, fill=WHITE, anchor="mm")
        draw.text((w // 2, h - 55), HANDLE, font=load_font(24, True), fill=MINT, anchor="mm")

    else:
        draw.rectangle([0, 0, w, h], fill=WHITE)
        # Banda superior delgada
        draw.rectangle([0, 0, w, 12], fill=MINT)

        fn_num = load_font(130, bold=True)
        fn_title = load_font(54, bold=True)
        fn_sub = load_font(28, bold=False)

        # Número enorme de fondo
        num_str = str(numero)
        draw.text((w - 60, h // 2 + 80), num_str, font=fn_num,
                  fill=(240, 244, 248), anchor="rm")

        # Punto mint decorativo
        draw.ellipse([60, 80, 100, 120], fill=MINT)
        draw.ellipse([110, 86, 136, 112], fill=MINT_LIGHT)

        draw.text((130, 70), BRAND, font=load_font(24, True), fill=NAVY)
        draw.rectangle([60, 140, w - 60, 143], fill=LIGHT)

        y = 180
        y = draw_wrapped_text(draw, slide["titulo"], fn_title, 60, y,
                               w - 180, NAVY, line_spacing=10)
        draw.rectangle([60, y + 20, 60 + min(len(slide["titulo"]) * 8, 220), y + 26], fill=MINT)
        y += 55
        draw_wrapped_text(draw, slide["texto"], fn_sub, 60, y,
                          w - 160, (70, 90, 110), line_spacing=8)

        draw.text((60, h - 65), HANDLE, font=load_font(22), fill=(180, 195, 210))


# ─── LAYOUT 3: DARK ELEGANCE ──────────────────────────────────────────────────
# Fondo muy oscuro (casi negro), acentos en mint vibrante, look premium

def render_layout_dark(draw: ImageDraw.ImageDraw, slide: dict, es_portada: bool, es_ultima: bool, numero: int):
    """Layout Dark Elegance — fondo oscuro premium, acentos mint vibrantes."""
    w, h = SIZE
    DARK = (8, 20, 40)
    DARK_MID = (15, 35, 65)
    MINT_BRIGHT = (100, 190, 170)

    draw.rectangle([0, 0, w, h], fill=DARK)

    # Gradiente simulado en la parte inferior
    for i in range(300):
        alpha = int(255 * (i / 300) * 0.3)
        y_pos = h - 300 + i
        color = (int(MINT[0] * alpha / 255 + DARK[0] * (255 - alpha) / 255),
                 int(MINT[1] * alpha / 255 + DARK[1] * (255 - alpha) / 255),
                 int(MINT[2] * alpha / 255 + DARK[2] * (255 - alpha) / 255))
        draw.rectangle([0, y_pos, w, y_pos + 1], fill=color)

    if es_portada:
        fn_brand = load_font(28, bold=True)
        fn_title = load_font(70, bold=True)
        fn_sub = load_font(31, bold=False)

        # Cruz decorativa en esquina
        draw.rectangle([w - 100, 60, w - 60, 68], fill=MINT)
        draw.rectangle([w - 84, 44, w - 76, 84], fill=MINT)

        draw.text((70, 65), BRAND, font=fn_brand, fill=MINT_BRIGHT)
        draw.rectangle([70, 108, 280, 114], fill=MINT)
        draw.rectangle([70, 118, 180, 122], fill=DARK_MID)

        y = 220
        y = draw_wrapped_text(draw, slide["titulo"], fn_title, 70, y,
                               w - 150, WHITE, line_spacing=12)
        y += 35
        draw_wrapped_text(draw, slide["texto"], fn_sub, 70, y,
                          w - 160, (160, 190, 200), line_spacing=8)

        draw.rectangle([0, h - 80, w, h], fill=DARK_MID)
        draw.text((70, h - 55), HANDLE, font=load_font(23), fill=MINT)
        draw.text((w - 70, h - 55), "→", font=load_font(32, True), fill=MINT_BRIGHT, anchor="rm")

    elif es_ultima:
        fn_title = load_font(55, bold=True)
        fn_sub = load_font(29, bold=False)
        fn_cta = load_font(27, bold=True)

        # Marco decorativo
        draw.rectangle([40, 40, w - 40, h - 40], outline=MINT, width=2)
        draw.rectangle([50, 50, w - 50, h - 50], outline=DARK_MID, width=1)

        draw.text((w // 2, 120), BRAND, font=load_font(30, True), fill=MINT_BRIGHT, anchor="mm")

        y = 220
        y = draw_wrapped_text(draw, slide["titulo"], fn_title, w // 2, y,
                               w - 180, WHITE, line_spacing=10, align="center")
        y += 25
        y = draw_wrapped_text(draw, slide["texto"], fn_sub, w // 2, y,
                               w - 200, (150, 180, 190), line_spacing=8, align="center")
        y += 55

        draw_rounded_rect(draw, (130, y, w - 130, y + 95), 8, MINT)
        draw.text((w // 2, y + 47), "METABOLISMO en comentarios",
                  font=fn_cta, fill=DARK, anchor="mm")

        draw.text((w // 2, h - 75), HANDLE, font=load_font(25, True), fill=MINT_BRIGHT, anchor="mm")

    else:
        fn_num = load_font(26, bold=True)
        fn_title = load_font(58, bold=True)
        fn_sub = load_font(29, bold=False)

        # Línea lateral decorativa
        for i in range(6):
            y_dot = 100 + i * 140
            draw.ellipse([w - 55, y_dot, w - 35, y_dot + 20], fill=MINT if i == (numero % 6) else DARK_MID)

        draw.text((70, 65), f"{numero:02d}", font=fn_num, fill=MINT_BRIGHT)
        draw.rectangle([70, 100, 180, 106], fill=MINT)
        draw.text((200, 62), BRAND, font=load_font(22), fill=(80, 100, 120))

        y = 160
        y = draw_wrapped_text(draw, slide["titulo"], fn_title, 70, y,
                               w - 150, WHITE, line_spacing=10)
        y += 30
        y = draw_wrapped_text(draw, slide["texto"], fn_sub, 70, y,
                               w - 150, (155, 185, 195), line_spacing=8)

        draw.text((70, h - 65), HANDLE, font=load_font(22), fill=(70, 100, 115))


# ─── Dispatcher de layouts ────────────────────────────────────────────────────

LAYOUT_NAMES = ["Bold Blocks", "Split Card", "Minimal Clean", "Dark Elegance"]
LAYOUT_RENDERERS = [render_layout_bold, render_layout_split, render_layout_minimal, render_layout_dark]


def render_slide(slide: dict, layout_idx: int, output_path: str) -> str:
    """
    Renderiza una diapositiva y la guarda como PNG.
    slide: dict con numero, titulo, texto
    layout_idx: 0-3
    output_path: ruta completa del PNG de salida
    """
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow no está instalado. Ejecuta: pip install Pillow")

    img = Image.new("RGB", SIZE, WHITE)
    draw = ImageDraw.Draw(img)

    numero = slide.get("numero", 1)
    es_portada = numero == 1
    es_ultima = numero == 7

    renderer = LAYOUT_RENDERERS[layout_idx % 4]
    renderer(draw, slide, es_portada, es_ultima, numero)

    img.save(output_path, "PNG", optimize=True, quality=95)
    return output_path


def generar_imagenes_carrusel(carrusel: dict, output_dir: str = None) -> list[str]:
    """
    Genera todas las imágenes del carrusel.

    carrusel: dict con tema, diapositivas[], caption, hashtags
    output_dir: directorio de salida (default: /tmp/bio-precise-carousel-{hash})

    Retorna lista de rutas PNG en orden.
    """
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow no está instalado. Ejecuta: pip install Pillow")

    # Determinar layout según el tema (siempre el mismo layout para el mismo tema)
    tema_hash = int(hashlib.md5(carrusel["tema"].encode()).hexdigest()[:8], 16)
    layout_idx = tema_hash % 4

    print(f"🎨 Layout seleccionado: {LAYOUT_NAMES[layout_idx]} (#{layout_idx})")

    # Directorio de salida — compatible con Windows y Linux
    if output_dir is None:
        short_hash = hashlib.md5(carrusel["tema"].encode()).hexdigest()[:8]
        output_dir = os.path.join(tempfile.gettempdir(), f"bio-precise-{short_hash}")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    rutas = []
    for slide in carrusel["diapositivas"]:
        filename = f"slide_{slide['numero']:02d}.png"
        output_path = os.path.join(output_dir, filename)
        render_slide(slide, layout_idx, output_path)
        rutas.append(output_path)
        print(f"  ✅ Slide {slide['numero']}: {output_path}")

    print(f"🎉 {len(rutas)} imágenes generadas en: {output_dir}")
    return rutas


def preview_layouts(output_dir: str = None):
    """
    Genera una diapositiva de muestra de cada layout para previsualización.
    Útil para elegir estilos.
    """
    if output_dir is None:
        output_dir = os.path.join(tempfile.gettempdir(), "bio-precise-preview")
    slide_muestra = {
        "numero": 1,
        "titulo": "¿Por qué no bajas de peso aunque haces dieta?",
        "texto": "La respuesta está en tus hormonas, no en tu fuerza de voluntad."
    }

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(LAYOUT_NAMES):
        path = os.path.join(output_dir, f"layout_{i}_{name.lower().replace(' ', '_')}.png")
        render_slide(slide_muestra, i, path)
        print(f"Layout {i} — {name}: {path}")

    return output_dir


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        print("Generando preview de los 4 layouts...")
        preview_layouts()
    else:
        # Test rápido con contenido de muestra
        carrusel_test = {
            "tema": "Resistencia a la insulina: causa silenciosa del sobrepeso",
            "diapositivas": [
                {"numero": 1, "titulo": "¿Haces dieta pero no bajas de peso?", "texto": "No es falta de disciplina. Es tu metabolismo enviándote señales."},
                {"numero": 2, "titulo": "Qué es la resistencia a la insulina", "texto": "Tu cuerpo produce insulina pero las células no la escuchan. El resultado: más grasa almacenada."},
                {"numero": 3, "titulo": "Las señales que nadie te explica", "texto": "Hambre 2 horas después de comer, fatiga post-almuerzo, antojos de dulce. ¿Te identificas?"},
                {"numero": 4, "titulo": "El análisis que necesitas hacer", "texto": "Insulina en ayunas + glucosa. Calcula el índice HOMA-IR. Si es mayor a 2.5, hay resistencia."},
                {"numero": 5, "titulo": "Alimentos que la empeoran", "texto": "Pan blanco, jugos de fruta, arroz en grandes cantidades. Generan picos de glucosa seguidos de caídas."},
                {"numero": 6, "titulo": "Cómo revertirla paso a paso", "texto": "Proteína en cada comida, caminata 20 min post-cena, dormir 7-8 horas. No hace falta pasar hambre."},
                {"numero": 7, "titulo": "¿Quieres saber si esto te está pasando?", "texto": "Escríbeme METABOLISMO en los comentarios y te cuento los siguientes pasos."},
            ],
            "caption": "Caption de prueba",
            "hashtags": ["#metabolismo", "#insulina", "#bioprecise"]
        }
        print("Generando carrusel de prueba...")
        rutas = generar_imagenes_carrusel(carrusel_test)
        print(f"\nTotal: {len(rutas)} imágenes generadas")
