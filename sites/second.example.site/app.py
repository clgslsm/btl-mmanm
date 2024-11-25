from flask import Flask, redirect, url_for, render_template, session, request, flash, jsonify
from flask_oidc import OpenIDConnect
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime
import json, pytz, jwt
import os

client_secrets = json.loads(os.getenv("CLIENT_SECRETS", "{}"))

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': client_secrets['web']['client_secret'],
    'OIDC_CLIENT_SECRETS': client_secrets,
    'OIDC_SCOPES': ['openid', 'email', 'profile'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post',
    'OIDC_USER_INFO_ENABLED': True,
})
oidc = OpenIDConnect(app)

# Add SQLAlchemy config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scholarships.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Add Scholarship Model
class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/profile')
@oidc.require_login
def profile():
    # Get user info including access token
    # info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    info = session.get('oidc_auth_profile', {})
    
    # Get the access token from the OAuth info
    access_token = oidc.get_access_token()
    print(access_token)
    
    if access_token:
        token_data = jwt.decode(access_token, options={"verify_signature": False})
        token_expiry = token_data.get('exp')  # Expiry time is in the 'exp' field (in seconds)
    else:
        token_expiry = None
    
    return render_template('profile.html', info=info, token_expiry=token_expiry, access_token=access_token, oidc=oidc)

@app.route('/logout_sso')
def logout_sso():
    oidc.logout()
    session.clear()
    keycloak_logout_url = app.config['OIDC_CLIENT_SECRETS']['web']['logout_uri']
    cliend_id = app.config['OIDC_CLIENT_SECRETS']['web']['client_id']
    return redirect(f"{keycloak_logout_url}?client_id={cliend_id}&post_logout_redirect_uri={url_for('home', _external=True)}")

@app.route('/')
def home():
    return render_template('home.html', oidc=oidc)

@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    if timestamp:
        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        dt = datetime.fromtimestamp(timestamp, tz=pytz.utc)  # Convert timestamp to UTC
        vietnam_time = dt.astimezone(vietnam_tz)
        return vietnam_time.strftime('%Y-%m-%d %H:%M:%S')
    
    return "Unknown"

@app.route('/refresh_token')
@oidc.require_login
def refresh_token():
    refresh_token = oidc.get_refresh_token()
    
    if not refresh_token:
        return jsonify({'error': 'No refresh token available'}), 400

    # Get the client credentials from the loaded client secrets
    client_id = app.config['OIDC_CLIENT_SECRETS']['web']['client_id']
    client_secret = app.config['OIDC_CLIENT_SECRETS']['web']['client_secret']
    token_uri = app.config['OIDC_CLIENT_SECRETS']['web']['token_uri']
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    response = requests.post(token_uri, data=data)

    if response.status_code == 200:
        refreshed_token = response.json().get('access_token')
        token_data = jwt.decode(refreshed_token, options={"verify_signature": False})
        new_token_expiry = timestamp_to_date(token_data.get('exp'))
        print(f"Token refreshed successfully. New expiry time: {new_token_expiry}")
        return jsonify({'token_expiry': new_token_expiry, 'access_token': refreshed_token}), 200
    else:
        return jsonify({'error': 'Failed to refresh the token', 'details': response.json()}), 400

@app.route('/public')
def public():
    return render_template('public.html', oidc=oidc)

@app.route('/scholarships')
@oidc.require_login
def scholarships():
    info = oidc.user_getinfo(['email'])
    user_email = info.get('email')
    scholarships = Scholarship.query.filter_by(email=user_email).all()
    return render_template('scholarships.html', scholarships=scholarships, oidc=oidc)

@app.route('/scholarship/add', methods=['GET', 'POST'])
@oidc.require_login
def add_scholarship():
    if request.method == 'POST':
        info = oidc.user_getinfo(['email'])
        user_email = info.get('email')
        
        scholarship = Scholarship(
            email=user_email,
            title=request.form['title'],
            amount=float(request.form['amount']),
            description=request.form['description'],
            deadline=datetime.strptime(request.form['deadline'], '%Y-%m-%d')
        )
        db.session.add(scholarship)
        db.session.commit()
        flash('Scholarship added successfully!', 'success')
        return redirect(url_for('scholarships'))
    
    return render_template('scholarship_form.html', oidc=oidc)

@app.route('/scholarship/edit/<int:id>', methods=['GET', 'POST'])
@oidc.require_login
def edit_scholarship(id):
    scholarship = Scholarship.query.get_or_404(id)
    info = oidc.user_getinfo(['email'])
    
    # Verify ownership
    if scholarship.email != info.get('email'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('scholarships'))
    
    if request.method == 'POST':
        scholarship.title = request.form['title']
        scholarship.amount = float(request.form['amount'])
        scholarship.description = request.form['description']
        scholarship.deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d')
        db.session.commit()
        flash('Scholarship updated successfully!', 'success')
        return redirect(url_for('scholarships'))
    
    return render_template('scholarship_form.html', scholarship=scholarship, oidc=oidc)

@app.route('/scholarship/delete/<int:id>')
@oidc.require_login
def delete_scholarship(id):
    scholarship = Scholarship.query.get_or_404(id)
    info = oidc.user_getinfo(['email'])
    
    if scholarship.email != info.get('email'):
        flash('Unauthorized access', 'error')
        return redirect(url_for('scholarships'))
    
    db.session.delete(scholarship)
    db.session.commit()
    flash('Scholarship deleted successfully!', 'success')
    return redirect(url_for('scholarships'))

# Add this at the end of the file
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)