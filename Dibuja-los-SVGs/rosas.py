import json
import turtle
import time
import math
from svgpathtools import svg2paths
import xml.etree.ElementTree as ET

SVG_FILE = '13146631_Red and purple roses set.svg'
JSON_FILE = 'roses.json'
POINTS_PER_SEGMENT = 20

def hex_to_rgb(hex_color):
    # Manejar diferentes formatos de color
    if not hex_color or hex_color == 'none':
        return [0.0, 0.0, 0.0]  # Negro por defecto
    
    if hex_color.startswith('#'):
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return [int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
        elif len(hex_color) == 3:
            return [int(hex_color[i]*2, 16) / 255.0 for i in range(3)]
    
    # Si no es hex válido, devolver negro por defecto
    return [0.0, 0.0, 0.0]

# Paso 1: extraer colores por path_id
def extract_colors(svg_file):
    tree = ET.parse(svg_file)
    root = tree.getroot()

    # Namespace fix (SVG usa namespaces)
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    
    path_colors = []
    
    for elem in root.findall('.//svg:path', ns):
        style = elem.attrib.get('style', '')
        fill = elem.attrib.get('fill', '')
        
        # Si no hay fill explícito, tratar de parsear de style
        color = "#000000"  # por defecto negro
        if fill and fill != 'none':
            color = fill
        else:
            # Buscar en style="fill:...;"
            for part in style.split(';'):
                if 'fill:' in part:
                    color_value = part.split(':')[1].strip()
                    if color_value != 'none':
                        color = color_value
        
        path_colors.append(color)
    
    return path_colors

# Paso 2: convertir SVG a JSON con colores
def svg_to_json(svg_file, json_file):
    paths, _ = svg2paths(svg_file)
    colors = extract_colors(svg_file)

    regions = []

    for i, path in enumerate(paths):
        points = []
        for segment in path:
            for j in range(POINTS_PER_SEGMENT + 1):
                t = j / POINTS_PER_SEGMENT
                point = segment.point(t)
                points.append([point.real, point.imag])

        # Color correspondiente
        color_hex = colors[i] if i < len(colors) else "#000000"  # fallback negro
        color_rgb = hex_to_rgb(color_hex)

        regions.append({
            "color": color_rgb,
            "contour": points
        })

    with open(json_file, 'w') as f:
        json.dump(regions, f, indent=2)

    print(f'✅ SVG convertido y guardado en {json_file}')


# Paso 3: dibujar el JSON
def draw_from_json(json_file):
    screen = turtle.Screen()
    screen.bgcolor("black")
    screen.setup(800, 800)
    t = turtle.Turtle()
    t.hideturtle()
    t.speed(0)
    screen.tracer(0)

    with open(json_file) as f:
        regions = json.load(f)

    all_points = [(p[0], p[1]) for r in regions for p in r['contour']]
    min_x = min(p[0] for p in all_points)
    max_x = max(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_y = max(p[1] for p in all_points)

    width = max_x - min_x
    height = max_y - min_y
    scale = min(600 / width, 600 / height)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    # Primero pintar normalmente para ver el proceso
    for region in regions:
        points = region['contour']
        
        # Calcular área aproximada del elemento
        if len(points) >= 3:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            width = max(xs) - min(xs)
            height = max(ys) - min(ys)
            area = width * height
            
            # Filtrar elementos muy grandes (fondos)
            if area > (max_x - min_x) * (max_y - min_y) * 0.5:
                continue
        
        color = '#{:02x}{:02x}{:02x}'.format(
            int(region['color'][0] * 255),
            int(region['color'][1] * 255),
            int(region['color'][2] * 255)
        )
        t.color(color, color)

        t.begin_fill()
        t.penup()

        x = (points[0][0] - center_x) * scale
        y = (center_y - points[0][1]) * scale
        t.goto(x, y)
        t.pendown()

        for point in points[1:]:
            x = (point[0] - center_x) * scale
            y = (center_y - point[1]) * scale
            t.goto(x, y)

        t.goto((points[0][0] - center_x) * scale, (center_y - points[0][1]) * scale)
        t.end_fill()
        screen.update()

    print("✅ Pintado terminado. Iniciando rotación...")
    time.sleep(1)

    # Función para rotar la imagen completa
    def draw_rotated_image(rotation_angle):
        t.clear()
        angle_rad = math.radians(rotation_angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        for region in regions:
            points = region['contour']
            
            if len(points) >= 3:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                width = max(xs) - min(xs)
                height = max(ys) - min(ys)
                area = width * height
                
                if area > (max_x - min_x) * (max_y - min_y) * 0.5:
                    continue
            
            color = '#{:02x}{:02x}{:02x}'.format(
                int(region['color'][0] * 255),
                int(region['color'][1] * 255),
                int(region['color'][2] * 255)
            )
            t.color(color, color)
            t.begin_fill()
            t.penup()

            x_orig = (points[0][0] - center_x) * scale
            y_orig = (center_y - points[0][1]) * scale
            x = x_orig * cos_a - y_orig * sin_a
            y = x_orig * sin_a + y_orig * cos_a
            t.goto(x, y)
            t.pendown()

            for point in points[1:]:
                x_orig = (point[0] - center_x) * scale
                y_orig = (center_y - point[1]) * scale
                x = x_orig * cos_a - y_orig * sin_a
                y = x_orig * sin_a + y_orig * cos_a
                t.goto(x, y)

            x_orig = (points[0][0] - center_x) * scale
            y_orig = (center_y - points[0][1]) * scale
            x = x_orig * cos_a - y_orig * sin_a
            y = x_orig * sin_a + y_orig * cos_a
            t.goto(x, y)
            t.end_fill()
        
        screen.update()
    
    # Rotar la imagen completa sin pausas
    for angle in range(0, 360, 5):
        draw_rotated_image(angle)

    print("✅ Dibujo terminado. Cierra la ventana para finalizar.")
    screen.mainloop()


# --- MAIN ---
if __name__ == "__main__":
    svg_to_json(SVG_FILE, JSON_FILE)
    draw_from_json(JSON_FILE)