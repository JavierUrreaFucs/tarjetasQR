from flask import Flask, render_template, request, redirect, url_for, send_file
import qrcode
from io import BytesIO
from flask_mysqldb import MySQL

app = Flask(__name__)

# Configuración de la base de datos MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'contact_db'

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_contact', methods=['POST'])
def add_contact():
    if request.method == 'POST':
        full_name = request.form['full_name']
        phone = request.form['phone']
        email = request.form['email']
        org = request.form['org']

        # Insertar los datos en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO contacts (full_name, phone, email, org)
            VALUES (%s, %s, %s, %s)
        """, (full_name, phone, email, org))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('generate_qr', contact_id=cursor.lastrowid))

@app.route('/generate_qr/<int:contact_id>')
def generate_qr(contact_id):
    # Recuperar los datos del contacto desde la base de datos
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT full_name, phone, email, org FROM contacts WHERE id = %s", [contact_id])
    contact = cursor.fetchone()
    cursor.close()

    full_name, phone, email, org = contact

    # Crear el contenido vCard
    vcard = f"""BEGIN:VCARD
VERSION:3.0
FN:{full_name}
TEL;TYPE=WORK,VOICE:{phone}
EMAIL:{email}
ORG:{org}
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

    img = qr.make_image(fill='black', back_color='white')

    # Guardar la imagen en un buffer en memoria
    buffer = BytesIO()
    img.save(buffer, 'PNG')
    buffer.seek(0)

    # Enviar la imagen del QR directamente
    return send_file(buffer, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
