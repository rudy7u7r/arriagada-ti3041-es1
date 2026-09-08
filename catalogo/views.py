import json
import os
from django.conf import settings
from django.shortcuts import render
from django.http import Http404

def cargar_datos():
    ruta_json = os.path.join(settings.BASE_DIR, 'catalogo', 'data', 'productos.json')
    try:
        with open(ruta_json, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def lista_productos(request):
    productos = cargar_datos()
    total_productos = len(productos)
    con_stock = sum(1 for p in productos if p.get('stock', 0) > 0)
    sin_stock = total_productos - con_stock

    contexto = {
        'productos': productos,
        'resumen': {
            'total': total_productos,
            'con_stock': con_stock,
            'sin_stock': sin_stock
        }
    }
    return render(request, 'catalogo/lista.html', contexto)

def detalle_producto(request, producto_id):
    productos = cargar_datos()
    producto = next((p for p in productos if p.get('id') == producto_id), None)

    if producto is None:
        raise Http404("El producto solicitado no existe en el catálogo.")

    return render(request, 'catalogo/detalle.html', {'producto': producto})