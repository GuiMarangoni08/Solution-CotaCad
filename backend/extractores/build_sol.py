# Extrator SOL - Le DXF de stands/decorados
# Retorna dict com ambientes, areas, piso, rodape, etc.

import ezdxf
import math
from ezdxf.tools.text import plain_mtext


def area_perim_bbox(verts):
    """Calcula area, perimetro, largura, comprimento de um poligono."""
    pts = [(v[0], v[1]) for v in verts]
    n = len(pts)
    if n < 3:
        return 0, 0, 0, 0, 0, 0

    A = abs(sum(pts[i][0]*pts[(i+1)%n][1] - pts[(i+1)%n][0]*pts[i][1] for i in range(n))) / 2
    P = sum(math.sqrt((pts[(i+1)%n][0]-pts[i][0])**2 + (pts[(i+1)%n][1]-pts[i][1])**2) for i in range(n))

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    larg = max(xs) - min(xs)
    comp = max(ys) - min(ys)
    if larg > comp:
        larg, comp = comp, larg

    cx = (max(xs) + min(xs)) / 2
    cy = (max(ys) + min(ys)) / 2

    return round(A, 3), round(P, 3), round(larg, 3), round(comp, 3), cx, cy


def dist(ax, ay, bx, by):
    """Distancia euclidiana entre dois pontos."""
    return math.sqrt((ax-bx)**2 + (ay-by)**2)


def point_in_poly(px, py, vertices):
    """Ray casting para determinar se ponto esta dentro de poligono."""
    pts = [(v[0], v[1]) for v in vertices]
    n = len(pts)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if ((yi > py) != (yj > py)) and (px < (xj-xi)*(py-yi)/(yj-yi+1e-12)+xi):
            inside = not inside
        j = i
    return inside


def detect_main_cluster(msp, layer_name, text_layer_hint, radius=80, max_area=200):
    """Auto-detecta o cluster principal quando o DXF tem multiplas instancias."""
    all_polys = []
    for e in msp:
        if e.dxftype() == 'LWPOLYLINE' and e.dxf.layer == layer_name:
            try:
                verts = list(e.vertices())
                if len(verts) >= 3:
                    A, P, larg, comp, cx, cy = area_perim_bbox(verts)
                    if 0.3 < A <= max_area:
                        all_polys.append({
                            'area': A, 'perim': P, 'larg': larg, 'comp': comp,
                            'cx': cx, 'cy': cy, 'verts': verts
                        })
            except:
                pass

    if not all_polys:
        return None, [], []

    max_area_val = max(p['area'] for p in all_polys)
    anchors = [p for p in all_polys if abs(p['area'] - max_area_val) < 0.5]

    all_texts = []
    for e in msp:
        if e.dxftype() == 'MTEXT':
            lyr = e.dxf.layer.lower()
            if text_layer_hint in lyr:
                try:
                    txt = plain_mtext(e.text).strip().replace('\n', ' ')
                    ins = e.dxf.insert
                    all_texts.append({'name': txt, 'x': float(ins.x), 'y': float(ins.y)})
                except:
                    pass

    best_anchor = None
    best_count = -1
    for anchor in anchors:
        ax, ay = anchor['cx'], anchor['cy']
        count = sum(1 for t in all_texts if dist(ax, ay, t['x'], t['y']) <= radius)
        if count > best_count:
            best_count = count
            best_anchor = (ax, ay)

    if best_anchor is None:
        return None, anchors, all_texts

    ax, ay = best_anchor
    main_polys = [p for p in all_polys if dist(ax, ay, p['cx'], p['cy']) <= radius]
    main_texts = [t for t in all_texts if dist(ax, ay, t['x'], t['y']) <= radius]

    return best_anchor, main_polys, main_texts


def extrair_sol_dxf(dxf_path: str, unidade: str = "m") -> dict:
    """
    Extrai dados do DXF tipo SOL.

    Returns dict com ambientes, areas, perimetros, etc.
    """
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        int_anchor, int_polys, int_texts = detect_main_cluster(
            msp,
            layer_name="SOL - AMBIENTES INTERNOS",
            text_layer_hint="amb",
            radius=80,
            max_area=200
        )

        ext_anchor, ext_polys, ext_texts = detect_main_cluster(
            msp,
            layer_name="SOL - AMBIENTES EXTERNOS",
            text_layer_hint="amb",
            radius=100,
            max_area=150
        )

        ambientes = []
        area_total = 0

        for poly in int_polys:
            verts = poly['verts']
            matching_text = None
            for text in int_texts:
                if point_in_poly(text['x'], text['y'], verts):
                    matching_text = text['name']
                    break

            if matching_text is None and int_texts:
                distances = [(dist(poly['cx'], poly['cy'], t['x'], t['y']), t['name']) for t in int_texts]
                if distances:
                    matching_text = min(distances)[1]

            amb_data = {
                "ambiente": matching_text or "SEM NOME",
                "tipo": "Interno",
                "area": poly['area'],
                "perimetro": poly['perim'],
                "largura": poly['larg'],
                "comprimento": poly['comp'],
                "piso": None,
                "rodape": None,
                "parede": None,
                "forro": None,
                "pd": "2,50m",
            }
            ambientes.append(amb_data)
            area_total += poly['area']

        for poly in ext_polys:
            verts = poly['verts']
            matching_text = None
            for text in ext_texts:
                if point_in_poly(text['x'], text['y'], verts):
                    matching_text = text['name']
                    break

            amb_data = {
                "ambiente": matching_text or "SEM NOME",
                "tipo": "Externo",
                "area": poly['area'],
                "perimetro": poly['perim'],
                "largura": poly['larg'],
                "comprimento": poly['comp'],
                "piso": "INTERTRAVADO",
                "rodape": None,
                "parede": None,
                "forro": None,
                "pd": None,
            }
            ambientes.append(amb_data)
            area_total += poly['area']

        return {
            "tipo": "SOL",
            "arquivo": dxf_path.split("\\")[-1],
            "unidade": unidade,
            "status": "ok",
            "ambientes": ambientes,
            "area_total": round(area_total, 2),
            "area_interna": round(sum(a['area'] for a in ambientes if a['tipo'] == 'Interno'), 2),
            "area_externa": round(sum(a['area'] for a in ambientes if a['tipo'] == 'Externo'), 2),
            "diag": {
                "cluster_interno": "detectado" if int_anchor else "nao encontrado",
                "num_polys_internos": len(int_polys),
                "num_texts_internos": len(int_texts),
                "cluster_externo": "detectado" if ext_anchor else "nao encontrado",
                "num_polys_externos": len(ext_polys),
                "num_texts_externos": len(ext_texts),
            }
        }

    except Exception as e:
        return {
            "tipo": "SOL",
            "arquivo": dxf_path.split("\\")[-1],
            "status": "erro",
            "erro_msg": str(e),
            "ambientes": [],
        }
