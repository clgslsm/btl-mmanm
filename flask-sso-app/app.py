from flask import Flask, redirect, url_for, render_template, session, request, flash
from flask_oidc import OpenIDConnect
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': 'uaUkCfrrEmSqf13Qkk5f4bgeLwBhMqNi',
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
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
    info = oidc.user_getinfo(['preferred_username', 'email', 'sub'])
    
    # Get the access token from the OAuth info
    access_token = oidc.get_access_token()
    print(access_token)
    
    # Make request to Keycloak userinfo endpoint using the access token
    headers = {'Authorization': f'Bearer {access_token}'}
    userinfo_endpoint = 'http://localhost:8080/realms/demo-sso-realm/protocol/openid-connect/userinfo'
    
    try:
        response = requests.get(userinfo_endpoint, headers=headers)
        if response.status_code == 200:
            userinfo = response.json()
            # Merge userinfo with existing info
            info.update(userinfo)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user info: {e}")
    
    return render_template('profile.html', info=info)

@app.route('/logout')
def logout():
    oidc.logout()
    return redirect(url_for('home'))

@app.route('/')
def home():
    info = oidc.user_getinfo(['email'])
    user_email = info.get('email')
    scholarships = Scholarship.query.filter_by(email=user_email).all()
    return render_template('scholarships.html', scholarships=scholarships)

@app.route('/scholarships')
@oidc.require_login
def scholarships():
    info = oidc.user_getinfo(['email'])
    user_email = info.get('email')
    scholarships = Scholarship.query.filter_by(email=user_email).all()
    return render_template('scholarships.html', scholarships=scholarships)

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
    
    return render_template('scholarship_form.html')

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
    
    return render_template('scholarship_form.html', scholarship=scholarship)

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
