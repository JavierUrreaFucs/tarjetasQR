from flask import Flask, render_template, request, redirect, url_for, send_file, abort, flash
import qrcode
from io import BytesIO
from flask_mysqldb import MySQL
from PIL import Image, ImageDraw, ImageFont
from config import Config
from auth import LoginForm, ChangePasswordForm, RegisterForm, ResetPasswordForm
from flask_mail import Mail, Message
import bcrypt

app = Flask(__name__)

# Configuración de la base de datos MySQL
app.config.from_object(Config)

# Configuración de MySQL
mysql = MySQL(app)

# Configuración de correo
mail = Mail(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_contact', methods=['POST'])
def add_contact():
    if request.method == 'POST':
        nombre1 = request.form['nombre1']
        nombre2 = request.form['nombre2']
        apellido1 = request.form['apellido1']
        apellido2 = request.form['apellido2']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        org = request.form['org']

        # Insertar los datos en la base de datos con el status 'active'
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO contacts (nombre1, nombre2, apellido1, apellido2, phone, email, address, org, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')
        """, (nombre1, nombre2, apellido1, apellido2, phone, email, address, org))
        mysql.connection.commit()
        contact_id = cursor.lastrowid
        cursor.close()

        return redirect(url_for('generate_qr', contact_id=contact_id))

@app.route('/generate_qr/<int:contact_id>')
def generate_qr(contact_id):
    # Recuperar los datos del contacto desde la base de datos, incluyendo el status
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT nombre1, nombre2, apellido1, apellido2, phone, email, address, org, status FROM contacts WHERE id = %s", [contact_id])
    contact = cursor.fetchone()
    cursor.close()

    if contact is None:
        return "Contacto no encontrado", 404

    nombre1, nombre2, apellido1, apellido2, phone, email, address, org, status = contact

    # Verificar si el contacto está activo
    if status != 'active':
        # Si el contacto está inactivo, se aborta con un código de estado 403 (Forbidden)
        abort(403)

    # Crear el contenido vCard solo si el contacto está activo
    vcard = f"""BEGIN:VCARD
VERSION:3.0
N:{apellido2};{nombre2};{apellido1};{nombre1}
FN:{nombre1} {nombre2} {apellido1} {apellido2}
TEL;TYPE=WORK,VOICE:+57{phone}
EMAIL:{email}
ORG:FUCS
TITLE:{org}
URL:https://www.fucsalud.edu.co/
ADR;TYPE=work: ;;{address};;;;
END:VCARD"""

    # Generar el código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(vcard)
    qr.make(fit=True)

    qr_img = qr.make_image(fill='black', back_color='white')

    # Cargar la imagen base desde el archivo que subiste
    base_img = Image.open("static/img/DIGITAL-MUESTRA.jpg")  # Ruta a la imagen subida

    # Redimensionar el código QR para ajustarlo al recuadro
    qr_img = qr_img.resize((360, 360))  # Ajusta el tamaño según lo que necesites

    # Coordenadas del recuadro blanco donde colocar el QR
    qr_position = (143, 590)  # Ajusta estas coordenadas si es necesario

    # Superponer el QR sobre la imagen base
    base_img.paste(qr_img, qr_position)

    # Añadir el nombre y la organización
    draw = ImageDraw.Draw(base_img)

    # Cargar una fuente, puedes ajustar la ruta y el tamaño
    font = ImageFont.truetype("static/font/Poppins-SemiBold.ttf", 48)  # Puedes cambiar por una fuente TrueType si tienes

    # Definir las posiciones y el texto
    text_position_name = (165, 350)  # Coordenadas para el nombre
    text_position_org = (105, 420)   # Coordenadas para la organización

    # Añadir el nombre y la organización
    full_name = f"{nombre1} {apellido1}"
    draw.text(text_position_name, full_name, font=font, fill="#0A2655")
    draw.text(text_position_org, org, font=font, fill="#0A2655")

    # Guardar la imagen resultante en un buffer en memoria
    buffer = BytesIO()
    base_img.save(buffer, 'PNG')
    buffer.seek(0)

    # Enviar la imagen con el QR y texto superpuestos como respuesta
    return send_file(buffer, mimetype='image/png')

# Manejo de error para contactos inactivos o no autorizados
@app.errorhandler(403)
def forbidden(error):
    return "El contacto no está disponible.", 403

# Rutas del Login 
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email=%s',(email,))
        user = cursor.fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'),user[3].encode('utf-8')):
            if user[4] == 1:  # Suponiendo que 'first_login' es la columna 5
                flash('Es necesario cambiar la contraseña al iniciar por primera vez.', 'warning')
                return redirect(url_for('change_password', user_id=user[0]))
            else:
                # Lógica para el inicio de sesión normal
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check your credentials.', 'danger')
    return render_template('login.html', form=form)

@app.route('/change_password/<int:user_id>', methods=['GET', 'POST'])
def change_password(user_id):
    form = ChangePasswordForm()
    if form.validate_on_submit():
        new_password = form.new_password.data
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE users SET password=%s, first_login=0 WHERE id=%s', (hashed_password, user_id))
        mysql.connection.commit()
        cursor.close()
        flash('Contraseña actualizada con éxito.', 'success')
        return redirect(url_for('login'))
    return render_template('change_password.html', form=form, user_id=user_id)


@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = "fucsalud123*"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO users (username, email, password) VALUES (%s,%s, %s)',(name, email, hashed_password))
        mysql.connection.commit()
        flash('Registro exitoso. La contraseña predeterminada es "fucsalud123*', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        # Aqui verificas si el email existe en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email=%s', (email,))
        user = cursor.fetchone()
        if user:
            token = '13467982'  # Aquí deberías generar un token real
            msg = Message('Solicitud de restablecimiento de contraseña', sender='noreply@demo.com', recipients=[email])
            msg.body = f'''Para restablecer su contraseña, visite el siguiente enlace:
http://localhost:5000/reset_password/{token}
Si no realizó esta solicitud, simplemente ignore este correo electrónico y no se realizarán cambios..
'''
            mail.send(msg)
            flash('Se ha enviado un correo electrónico con instrucciones para restablecer su contraseña.', 'info')
        else:
            flash('No se encontró ninguna cuenta con ese correo electrónico.', 'warning')
    return render_template('reset_password.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
