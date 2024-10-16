from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo

class LoginForm(FlaskForm):
  email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
  password = PasswordField('Contraseña', validators=[DataRequired()])
  submit = SubmitField('Iniciar Sesión')

class ChangePasswordForm(FlaskForm):
  new_password = PasswordField('Nueva Contraseña', validators=[DataRequired()])
  confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired()])
  submit = SubmitField('Cambiar Contraseña')

class RegisterForm(FlaskForm):
  name = StringField('Nombre', validators=[DataRequired()])
  email = StringField('Email', validators=[DataRequired(), Email()])
  submit = SubmitField('Registrar')

class ResetPasswordForm(FlaskForm):
  email = StringField('Correo electrónico', validators=[DataRequired(), Email()])
  submit = SubmitField('Solicitar restablecimiento de contraseña')