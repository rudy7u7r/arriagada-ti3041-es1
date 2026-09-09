import os
import json
from datetime import datetime
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
            'imagen': request.POST.get('imagen', '').strip()
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
                p['imagen'] = request.POST.get('imagen', '').strip()
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


# -------------------------------------------------------------------
# Autenticación (admin y usuarios normales) usando usuarios.json
# -------------------------------------------------------------------
def login_admin(request):
    error = None
    if request.method == 'POST':
        user_input = request.POST.get('usuario', '').strip()
        pass_input = request.POST.get('clave', '').strip()

        usuarios = cargar_json('usuarios.json')

        usuario_encontrado = next(
            (u for u in usuarios
             if u.get('usuario', '').strip() == user_input
             and u.get('clave', '').strip() == pass_input),
            None
        )

        if usuario_encontrado:
            rol = usuario_encontrado.get('rol', 'cliente')
            request.session['usuario'] = usuario_encontrado.get('usuario')
            request.session['rol'] = rol
            request.session['es_admin'] = (rol == 'admin')
            request.session.modified = True

            if rol == 'admin':
                return redirect('agregar_producto')
            return redirect('lista_productos')
        else:
            error = "Credenciales incorrectas"

    return render(request, 'catalogo/login.html', {'error': error})


def registro_usuario(request):
    error = None
    if request.method == 'POST':
        usuario = request.POST.get('usuario', '').strip()
        clave = request.POST.get('clave', '').strip()
        clave2 = request.POST.get('clave2', '').strip()

        if not usuario or not clave:
            error = "Debes completar usuario y contraseña."
        elif clave != clave2:
            error = "Las contraseñas no coinciden."
        else:
            usuarios = cargar_json('usuarios.json')
            existe = any(
                u.get('usuario', '').strip().lower() == usuario.lower()
                for u in usuarios
            )
            if existe:
                error = "Ese nombre de usuario ya existe."
            else:
                usuarios.append({
                    'usuario': usuario,
                    'clave': clave,
                    'rol': 'cliente'
                })
                guardar_json('usuarios.json', usuarios)

                request.session['usuario'] = usuario
                request.session['rol'] = 'cliente'
                request.session['es_admin'] = False
                request.session.modified = True
                return redirect('lista_productos')

    return render(request, 'catalogo/registro.html', {'error': error})


def logout_admin(request):
    request.session.flush()
    return redirect('lista_productos')


# -------------------------------------------------------------------
# Seudocompra: requiere sesión iniciada (admin o cliente)
# -------------------------------------------------------------------
def agregar_al_carrito(request, producto_id):
    if not request.session.get('usuario'):
        return redirect('login_admin')

    if request.method == 'POST':
        productos = cargar_json('productos.json')
        producto = next((p for p in productos if p['id'] == producto_id), None)

        if producto and producto.get('stock', 0) > 0:
            producto['stock'] -= 1
            guardar_json('productos.json', productos)

            compras = cargar_json('compras.json')
            nuevo_id = max([c['id'] for c in compras], default=0) + 1
            compras.append({
                'id': nuevo_id,
                'usuario': request.session.get('usuario'),
                'producto_id': producto['id'],
                'producto_nombre': producto['nombre'],
                'precio': producto.get('precio', 0),
                'cantidad': 1,
                'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            guardar_json('compras.json', compras)

    return redirect('lista_productos')


def mis_compras(request):
    if not request.session.get('usuario'):
        return redirect('login_admin')

    compras = cargar_json('compras.json')
    mis = [c for c in compras if c.get('usuario') == request.session.get('usuario')]
    mis.reverse()
    return render(request, 'catalogo/mis_compras.html', {'compras': mis})