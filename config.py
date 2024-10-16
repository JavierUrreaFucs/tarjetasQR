import os

class Config:
    SECRET_KEY = os.urandom(24)
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'contact_db'

    # Configuración para el envío de correos (recuperación de contraseña)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'jhurrea@fucsalud.edu.co'
    MAIL_PASSWORD = 'ndxr izyz gbux mgrr'
