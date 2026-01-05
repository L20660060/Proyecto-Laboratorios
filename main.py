from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, User, Equipo, Prestamo
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Crear DB y usuario admin
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin', nombre='Administrador', codigo='ADMIN001')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Usuario admin creado: admin / admin123")

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('historial'))
        flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# === EQUIPOS (solo admin) ===
@app.route('/equipos')
@login_required
def equipos():
    if current_user.role != 'admin':
        flash('Acceso denegado')
        return redirect(url_for('historial'))
    equipos_list = Equipo.query.all()
    return render_template('equipos/lista.html', equipos=equipos_list)

@app.route('/equipos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_equipo():
    if current_user.role != 'admin':
        flash('Acceso denegado')
        return redirect(url_for('historial'))
    if request.method == 'POST':
        multa_por_dia = request.form.get('multa_por_dia', 50.0, type=float)
        equipo = Equipo(
            nombre=request.form['nombre'],
            codigo=request.form['codigo'],
            condicion=request.form.get('condicion', ''),
            multa_por_dia=multa_por_dia
        )
        db.session.add(equipo)
        db.session.commit()
        flash('Equipo agregado correctamente')
        return redirect(url_for('equipos'))
    return render_template('equipos/nuevo.html')

@app.route('/equipos/editar/<int:equipo_id>', methods=['GET', 'POST'])
@login_required
def editar_equipo(equipo_id):
    if current_user.role != 'admin':
        flash('Acceso denegado')
        return redirect(url_for('historial'))
    
    equipo = Equipo.query.get_or_404(equipo_id)
    if request.method == 'POST':
        equipo.nombre = request.form['nombre']
        equipo.codigo = request.form['codigo']
        equipo.condicion = request.form.get('condicion', '')
        equipo.multa_por_dia = request.form.get('multa_por_dia', 50.0, type=float)
        db.session.commit()
        flash('Equipo actualizado correctamente')
        return redirect(url_for('equipos'))
    
    return render_template('equipos/editar.html', equipo=equipo)

@app.route('/equipos/eliminar/<int:equipo_id>')
@login_required
def eliminar_equipo(equipo_id):
    if current_user.role != 'admin':
        flash('Acceso denegado')
        return redirect(url_for('historial'))
    
    equipo = Equipo.query.get_or_404(equipo_id)
    if equipo.estado == 'Prestado':
        flash('No se puede eliminar un equipo que está prestado', 'error')
    else:
        db.session.delete(equipo)
        db.session.commit()
        flash('Equipo eliminado correctamente')
    return redirect(url_for('equipos'))

# === ALUMNOS (admin y consulta) ===
@app.route('/alumnos')
@login_required
def alumnos():
    if current_user.role not in ['admin', 'consulta']:
        flash('Acceso denegado')
        return redirect(url_for('historial'))
    
    alumnos_list = User.query.filter_by(role='alumno').all()
    return render_template('alumnos/lista.html', alumnos=alumnos_list)

@app.route('/alumnos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_alumno():
    if current_user.role != 'admin':
        flash('Acceso denegado')
        return redirect(url_for('historial'))
    
    if request.method == 'POST':
        username = request.form['username']
        codigo = request.form['codigo']

        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'error')
            return redirect(url_for('nuevo_alumno'))
        
        if User.query.filter_by(codigo=codigo).first():
            flash('El código/matrícula ya está registrado', 'error')
            return redirect(url_for('nuevo_alumno'))

        alumno = User(
            username=username,
            nombre=request.form['nombre'],
            codigo=codigo,
            role='alumno'
        )
        alumno.set_password(request.form['password'])
        db.session.add(alumno)
        db.session.commit()
        flash('Alumno creado correctamente')
        return redirect(url_for('alumnos'))
    
    return render_template('alumnos/nuevo.html')

@app.route('/alumnos/editar/<int:alumno_id>', methods=['GET', 'POST'])
@login_required
def editar_alumno(alumno_id):
    if current_user.role != 'admin':
        flash('Acceso denegado')
        return redirect(url_for('historial'))
    
    alumno = User.query.get_or_404(alumno_id)
    if alumno.role != 'alumno':
        flash('No se puede editar este usuario', 'error')
        return redirect(url_for('alumnos'))
    
    if request.method == 'POST':
        username = request.form['username']
        codigo = request.form['codigo']
        
        if User.query.filter(User.username == username, User.id != alumno.id).first():
            flash('El nombre de usuario ya existe', 'error')
            return redirect(url_for('editar_alumno', alumno_id=alumno.id))
        
        if User.query.filter(User.codigo == codigo, User.id != alumno.id).first():
            flash('El código/matrícula ya está registrado', 'error')
            return redirect(url_for('editar_alumno', alumno_id=alumno.id))
        
        alumno.username = username
        alumno.nombre = request.form['nombre']
        alumno.codigo = codigo
        if request.form['password']:
            alumno.set_password(request.form['password'])
        db.session.commit()
        flash('Alumno actualizado correctamente')
        return redirect(url_for('alumnos'))
    
    return render_template('alumnos/editar.html', alumno=alumno)

@app.route('/alumnos/eliminar/<int:alumno_id>')
@login_required
def eliminar_alumno(alumno_id):
    if current_user.role != 'admin':
        flash('Acceso denegado')
        return redirect(url_for('historial'))
    
    alumno = User.query.get_or_404(alumno_id)
    if alumno.role != 'alumno':
        flash('No se puede eliminar este usuario', 'error')
        return redirect(url_for('alumnos'))

    prestamos = Prestamo.query.filter_by(alumno_id=alumno.id).all()
    for prestamo in prestamos:
        if prestamo.estado == 'Activo' and prestamo.equipo:
            prestamo.equipo.estado = 'Disponible'
        db.session.delete(prestamo)

    db.session.delete(alumno)
    db.session.commit()
    flash('Alumno y todos sus préstamos eliminados correctamente')
    return redirect(url_for('alumnos'))

# === PRÉSTAMOS ===
@app.route('/prestamos')
@login_required
def prestamos():
    if current_user.role == 'admin':
        prestamos_list = Prestamo.query.filter_by(estado='Activo').all()
    else:
        prestamos_list = Prestamo.query.filter_by(alumno_id=current_user.id, estado='Activo').all()
    return render_template('prestamos/lista.html', prestamos=prestamos_list, datetime=datetime)

@app.route('/prestamo/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_prestamo():
    if current_user.role != 'alumno':
        flash('Acceso denegado')
        return redirect(url_for('historial'))
    
    equipos = Equipo.query.filter_by(estado='Disponible').all()
    if request.method == 'POST':
        equipo = Equipo.query.get(request.form['equipo_id'])
        equipo.estado = 'Prestado'
        fecha_prevista_str = request.form['fecha_prevista_devolucion']
        fecha_prevista = datetime.strptime(fecha_prevista_str, '%Y-%m-%dT%H:%M') if fecha_prevista_str else None
        
        prestamo = Prestamo(
            equipo_id=request.form['equipo_id'],
            alumno_id=current_user.id,
            fecha_prevista_devolucion=fecha_prevista
        )
        db.session.add(prestamo)
        db.session.commit()
        flash('Préstamo solicitado correctamente')
        return redirect(url_for('prestamos'))
    
    return render_template('prestamos/nuevo.html', equipos=equipos, now=datetime.utcnow())

@app.route('/prestamo/devolver/<int:prestamo_id>', methods=['GET', 'POST'])
@login_required
def devolver(prestamo_id):
    prestamo = Prestamo.query.get_or_404(prestamo_id)
    
    if current_user.role != 'admin' and prestamo.alumno_id != current_user.id:
        flash('Acceso denegado')
        return redirect(url_for('prestamos'))
    
    if request.method == 'POST':
        prestamo.estado = 'Devuelto'
        prestamo.fecha_devolucion = datetime.utcnow()
        prestamo.equipo.estado = 'Disponible'
        
        dias_retraso = 0
        multa = 0.0
        if prestamo.fecha_prevista_devolucion and prestamo.fecha_devolucion > prestamo.fecha_prevista_devolucion:
            delta = prestamo.fecha_devolucion - prestamo.fecha_prevista_devolucion
            dias_retraso = delta.days
            multa_por_dia = prestamo.equipo.multa_por_dia if prestamo.equipo.multa_por_dia else 50.0
            multa = dias_retraso * multa_por_dia
        
        prestamo.dias_retraso = dias_retraso
        prestamo.multa_aplicada = multa
        
        db.session.commit()
        
        if multa > 0:
            flash(f'Devolución registrada. Multa aplicada: ${multa:.2f} ({dias_retraso} días de retraso)', 'warning')
        else:
            flash('Devolución registrada correctamente', 'success')
        
        return redirect(url_for('prestamos'))
    
    vencido = False
    dias_retraso = 0
    multa = 0.0
    if prestamo.fecha_prevista_devolucion and datetime.utcnow() > prestamo.fecha_prevista_devolucion:
        vencido = True
        delta = datetime.utcnow() - prestamo.fecha_prevista_devolucion
        dias_retraso = delta.days
        multa_por_dia = prestamo.equipo.multa_por_dia if prestamo.equipo.multa_por_dia else 50.0
        multa = dias_retraso * multa_por_dia

    return render_template('prestamos/devolver.html', 
                         prestamo=prestamo, 
                         vencido=vencido, 
                         dias_retraso=dias_retraso, 
                         multa=multa)

@app.route('/historial')
@login_required
def historial():
    if current_user.role == 'admin':
        prestamos_list = Prestamo.query.all()
    else:
        prestamos_list = Prestamo.query.filter_by(alumno_id=current_user.id).all()
    return render_template('historial.html', prestamos=prestamos_list, datetime=datetime)

# Corregido para Render.com
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
