from flask import Flask, redirect, url_for, render_template, session
from flask_oidc import OpenIDConnect
import requests

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': 'uaUkCfrrEmSqf13Qkk5f4bgeLwBhMqNi',
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    'OIDC_SCOPES': ['openid', 'email', 'profile'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post',
    'OIDC_USER_INFO_ENABLED': True,
})
oidc = OpenIDConnect(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/profile')
@oidc.require_login
def profile():
    info = oidc.user_getinfo(['preferred_username', 'email'])
    return render_template('profile.html', info=info)

@app.route('/logout')
def logout():
    oidc.logout()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
