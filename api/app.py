from flask import Flask, request, jsonify, g
from flask_oidc import OpenIDConnect
import requests
import python_jwt as jwt  # For decoding tokens locally
from flasgger import Swagger  # Import Swagger
import sqlite3

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': 'uaUkCfrrEmSqf13Qkk5f4bgeLwBhMqNi',
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    'OIDC_SCOPES': ['openid', 'email', 'profile'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post',
    'OIDC_USER_INFO_ENABLED': True,
})
oidc = OpenIDConnect(app)
swagger = Swagger(app, template={
    'securityDefinitions': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
})  # Initialize Swagger

KEYCLOAK_REALM = "demo-sso-realm"
KEYCLOAK_SERVER = "http://localhost:8080"
KEYCLOAK_INTROSPECTION_ENDPOINT = f"{KEYCLOAK_SERVER}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token/introspect"
KEYCLOAK_PUBLIC_KEY_URL = f"{KEYCLOAK_SERVER}/realms/{KEYCLOAK_REALM}"

DATABASE = 'university.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                course TEXT NOT NULL
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize the database
init_db()

# Get the Keycloak public key for local JWT validation
def get_keycloak_public_key():
    try:
        response = requests.get(f"{KEYCLOAK_PUBLIC_KEY_URL}")
        response.raise_for_status()
        key_data = response.json()
        return f"-----BEGIN PUBLIC KEY-----\n{key_data['public_key']}\n-----END PUBLIC KEY-----"
    except Exception as e:
        print(f"Error fetching public key: {e}")
        return None

PUBLIC_KEY = get_keycloak_public_key()


def validate_token(token):
    """Validate the access token using Keycloak introspection endpoint or local decoding."""
    try:
        # Option 1: Use Keycloak Introspection Endpoint
        response = requests.post(
            KEYCLOAK_INTROSPECTION_ENDPOINT,
            data={'token': token, 'client_id': 'flask-app', 'client_secret': 'WOn0ssWpd5EZmZG14NpEepvMvc3I7man'},
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        print(KEYCLOAK_INTROSPECTION_ENDPOINT)
        print(response.json())
        if response.status_code == 200 and response.json().get('active'):
            return response.json()  # Return decoded token info
        return None

        # Option 2: Local JWT Decoding
        # header, claims = jwt.verify_jwt(token, PUBLIC_KEY, ['RS256'], audience='flask-app')
        # print(claims)
        # return claims

    except Exception as e:
        print(f"Token validation error: {e}")
        return None


@app.route('/api/resource', methods=['GET'])
def get_resource():
    """
    Fetch student data for the authenticated user.
    ---
    tags:
      - Student Resources
    security:
      - Bearer: []
    responses:
      200:
        description: Student data retrieved successfully
        schema:
          properties:
            message:
              type: string
              example: "GET request successful"
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  email:
                    type: string
                  name:
                    type: string
                  course:
                    type: string
      401:
        description: Unauthorized - Invalid or missing token
      403:
        description: Forbidden - Insufficient permissions
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    token = auth_header
    decoded_token = validate_token(token)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired token"}), 401

    roles = decoded_token.get('resource_access', {}).get('flask-app', {}).get('roles', [])
    if 'Dev' not in roles:
        return jsonify({"error": "Insufficient permissions"}), 403

    email = decoded_token.get('email')
    if not email:
        return jsonify({"error": "Email not found in token"}), 401

    students = query_db('SELECT * FROM students WHERE email = ?', [email])
    return jsonify({"message": "GET request successful", "data": students})


@app.route('/api/resource', methods=['POST'])
def post_resource():
    """
    Create a new student record.
    ---
    tags:
      - Student Resources
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - course
          properties:
            name:
              type: string
              example: "John Doe"
            course:
              type: string
              example: "Computer Science"
    responses:
      201:
        description: Student created successfully
      400:
        description: Bad request - Student already exists
      401:
        description: Unauthorized - Invalid or missing token
      403:
        description: Forbidden - Insufficient permissions
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    token = auth_header
    decoded_token = validate_token(token)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired token"}), 401

    roles = decoded_token.get('resource_access', {}).get('flask-app', {}).get('roles', [])
    if 'Dev' not in roles:
        return jsonify({"error": "Insufficient permissions"}), 403

    email = decoded_token.get('email')
    if not email:
        return jsonify({"error": "Email not found in token"}), 401

    data = request.json
    try:
        db = get_db()
        db.execute('INSERT INTO students (email, name, course) VALUES (?, ?, ?)',
                   [email, data['name'], data['course']])
        db.commit()
        return jsonify({"message": "POST request successful", "data": data}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Student with this email already exists"}), 400


@app.route('/api/resource', methods=['PUT'])
def put_resource():
    """
    Update student data for the authenticated user.
    ---
    tags:
      - Student Resources
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - course
          properties:
            name:
              type: string
              example: "John Doe"
            course:
              type: string
              example: "Computer Science"
    responses:
      200:
        description: Student data updated successfully
      401:
        description: Unauthorized - Invalid or missing token
      403:
        description: Forbidden - Insufficient permissions
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    token = auth_header
    decoded_token = validate_token(token)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired token"}), 401

    roles = decoded_token.get('resource_access', {}).get('flask-app', {}).get('roles', [])
    if 'Dev' not in roles:
        return jsonify({"error": "Insufficient permissions"}), 403

    email = decoded_token.get('email')
    if not email:
        return jsonify({"error": "Email not found in token"}), 401

    data = request.json
    db = get_db()
    db.execute('UPDATE students SET name = ?, course = ? WHERE email = ?',
               [data['name'], data['course'], email])
    db.commit()
    return jsonify({"message": "PUT request successful", "data": data})


@app.route('/api/resource', methods=['DELETE'])
def delete_resource():
    """
    Delete student record for the authenticated user.
    ---
    tags:
      - Student Resources
    security:
      - Bearer: []
    responses:
      204:
        description: Student deleted successfully
      401:
        description: Unauthorized - Invalid or missing token
      403:
        description: Forbidden - Insufficient permissions
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    token = auth_header
    decoded_token = validate_token(token)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired token"}), 401

    roles = decoded_token.get('resource_access', {}).get('flask-app', {}).get('roles', [])
    if 'Dev' not in roles:
        return jsonify({"error": "Insufficient permissions"}), 403

    email = decoded_token.get('email')
    if not email:
        return jsonify({"error": "Email not found in token"}), 401

    db = get_db()
    db.execute('DELETE FROM students WHERE email = ?', [email])
    db.commit()
    return jsonify({"message": "DELETE request successful"}), 204


@app.route('/api/userinfo', methods=['GET'])
@oidc.require_login
def userinfo():
    """
    Fetch user info using the access token.
    ---
    tags:
      - User Info
    responses:
      200:
        description: User info retrieved successfully
      500:
        description: Error fetching user info
    """
    """Fetch user info using the access token."""
    access_token = oidc.get_access_token()
    headers = {'Authorization': f'Bearer {access_token}'}
    userinfo_endpoint = f"{KEYCLOAK_SERVER}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/userinfo"

    try:
        response = requests.get(userinfo_endpoint, headers=headers)
        if response.status_code == 200:
            return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error fetching user info: {e}"}), 500

    return jsonify({"error": "Unable to fetch user info"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
