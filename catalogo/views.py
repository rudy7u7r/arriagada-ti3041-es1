import os
import json
from django.shortcuts import render, redirect
from django.conf import settings

# -------------------------------------------------------------------
# Funciones auxiliares para la gestión de archivos JSON
# -------------------------------------------------------------------
def cargar_json(nombre_archivo):
    ruta = os.path.join(settings.BASE_DIR, 'catalogo', 'data', nombre_archivo)
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as file:
            return json.load(file)
    return []

# Definición explícita de guardar_json
def guardar_json(nombre_archivo, datos):
    ruta = os.path.join(settings.BASE_DIR, 'catalogo', 'data', nombre_archivo)
    with open(ruta, 'w', encoding='utf-8') as file:
        json.dump(datos, file, ensure_ascii=False, indent=4)

# -------------------------------------------------------------------
# Vistas del catálogo
# -------------------------------------------------------------------
def lista_productos(request):
    productos = cargar_json('productos.json')
    return render(request, 'catalogo/lista.html', {'productos': productos})


def detalle_producto(request, producto_id):
    productos = cargar_json('productos.json')
    producto = next((p for p in productos if p['id'] == producto_id), None)
    return render(request, 'catalogo/detalle.html', {'producto': producto})


def agregar_producto(request):
    if not request.session.get('es_admin'):
        return redirect('login_admin')

    if request.method == 'POST':
        productos = cargar_json('productos.json')
        
        nuevo_id = max([p['id'] for p in productos], default=0) + 1
        nuevo_producto = {
            'id': nuevo_id,
            'nombre': request.POST.get('nombre'),
            'descripcion': request.POST.get('descripcion'),
            'precio': float(request.POST.get('precio', 0)),
            'stock': int(request.POST.get('stock', 0)),
            'imagen': request.POST.get('imagen', '')
        }
        
        productos.append(nuevo_producto)
        guardar_json('productos.json', productos)
        return redirect('lista_productos')

    return render(request, 'catalogo/formulario.html')


def editar_producto(request, producto_id):
    if not request.session.get('es_admin'):
        return redirect('login_admin')

    productos = cargar_json('productos.json')
    producto = next((p for p in productos if p['id'] == producto_id), None)

    if request.method == 'POST':
        for p in productos:
            if p['id'] == producto_id:
                p['nombre'] = request.POST.get('nombre')
                p['descripcion'] = request.POST.get('descripcion')
                p['precio'] = float(request.POST.get('precio', 0))
                p['stock'] = int(request.POST.get('stock', 0))
                p['imagen'] = request.POST.get('imagen', '')
                break

        guardar_json('productos.json', productos)
        return redirect('lista_productos')

    return render(request, 'catalogo/formulario.html', {'producto': producto})


def eliminar_producto(request, producto_id):
    if not request.session.get('es_admin'):
        return redirect('login_admin')

    productos = cargar_json('productos.json')
    productos = [p for p in productos if p['id'] != producto_id]
    guardar_json('productos.json', productos)
    return redirect('lista_productos')


def login_admin(request):
    error = None
    if request.method == 'POST':
        user_input = request.POST.get('usuario', '').strip()
        pass_input = request.POST.get('clave', '').strip()
        
        usuarios = cargar_json('usuarios.json')
        
        usuario_valido = any(
            u.get('usuario', '').strip() == user_input and 
            u.get('clave', '').strip() == pass_input 
            for u in usuarios
        )

        if usuario_valido:
            request.session['es_admin'] = True
            request.session.modified = True
            return redirect('agregar_producto')
        else:
            error = "Credenciales incorrectas"
            
    return render(request, 'catalogo/login.html', {'error': error})


def logout_admin(request):
    request.session.flush()
    return redirect('lista_productos')


# Vista para descontar stock al presionar comprar
def agregar_al_carrito(request, producto_id):
    if request.method == 'POST':
        productos = cargar_json('productos.json')
        
        for p in productos:
            if p['id'] == producto_id and p.get('stock', 0) > 0:
                p['stock'] -= 1
                guardar_json('productos.json', productos)
                break

    return redirect('lista_productos')