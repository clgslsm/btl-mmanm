from flask import Flask, request, jsonify, g
import requests
import jwt  # For decoding tokens locally
from flasgger import Swagger  # Import Swagger
import sqlite3, json, os
from flask_cors import CORS  # Import CORS
import time

app = Flask(__name__)
CORS(app)

swagger = Swagger(
    app,
    template={
        "securityDefinitions": {
            "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
        }
    },
)  # Initialize Swagger

KEYCLOAK_PUBLIC_KEY_URL = "https://sso.example.org/realms/demo-sso-realm"

DATABASE = "university.db"

CLIENT_ID = 'first.example.org'


def get_db():
    db = getattr(g, "_database", None)
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
        db.execute("DROP TABLE IF EXISTS students")
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                course TEXT NOT NULL,
                enrollment_date TEXT NOT NULL,
                expected_graduation TEXT,
                gpa FLOAT DEFAULT 0.0,
                credits_completed INTEGER DEFAULT 0,
                major TEXT NOT NULL,
                minor TEXT
            )
        """
        )
        db.commit()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


# Initialize the database
# init_db()

def get_keycloak_public_key(retries=5, delay=5):
    time.sleep(5) # Wait for Keycloak to start
    for attempt in range(retries):
        try:
            response = requests.get(KEYCLOAK_PUBLIC_KEY_URL)
            response.raise_for_status()
            key_data = response.json()
            public_key = key_data.get("public_key")
            return f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
        except Exception as e:
            print(f"Attempt {attempt + 1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print("Failed to fetch public key after retries.")
                return None

PUBLIC_KEY = get_keycloak_public_key()


def validate_token(token):
    """Validate the access token using local JWT validation."""
    try:
        token = token.removeprefix("Bearer ")

        claims = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return claims
    except Exception as e:
        print(f"Token validation error: {e}")
        return None


@app.route("/api/resource", methods=["GET"])
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
                  enrollment_date:
                    type: string
                  expected_graduation:
                    type: string
                  gpa:
                    type: number
                  credits_completed:
                    type: integer
                  major:
                    type: string
                  minor:
                    type: string
      401:
        description: Unauthorized - Invalid or missing token
      403:
        description: Forbidden - Insufficient permissions
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    decoded_token = validate_token(auth_header)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired token"}), 401

    print("decoded_token: ", decoded_token)
    roles = (
        decoded_token.get("resource_access", {}).get(CLIENT_ID, {}).get("roles", [])
    )
    if "Student" not in roles:
        return jsonify({"error": "Insufficient permissions"}), 403

    email = decoded_token.get("email")
    if not email:
        return jsonify({"error": "Email not found in token"}), 401

    # Get column names from the students table
    columns = [
        "id",
        "email",
        "name",
        "course",
        "enrollment_date",
        "expected_graduation",
        "gpa",
        "credits_completed",
        "major",
        "minor",
    ]

    students = query_db("SELECT * FROM students WHERE email = ?", [email])

    # Transform the data into a list of dictionaries
    formatted_students = []
    for student in students:
        student_dict = {columns[i]: student[i] for i in range(len(columns))}
        formatted_students.append(student_dict)

    return jsonify(
        {
            "message": "GET request successful",
            "data": formatted_students[0] if formatted_students else None,
        }
    )


@app.route("/api/resource", methods=["POST"])
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
            - enrollment_date
            - major
          properties:
            name:
              type: string
              example: "John Doe"
            course:
              type: string
              example: "Computer Science"
            enrollment_date:
              type: string
              format: date
              example: "2024-03-15"
            expected_graduation:
              type: string
              format: date
              example: "2028-05-30"
            gpa:
              type: number
              format: float
              example: 3.5
            credits_completed:
              type: integer
              example: 60
            major:
              type: string
              example: "Computer Science"
            minor:
              type: string
              example: "Mathematics"
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
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    decoded_token = validate_token(auth_header)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired token"}), 401

    roles = (
        decoded_token.get("resource_access", {}).get(CLIENT_ID, {}).get("roles", [])
    )
    if "Student" not in roles:
        return jsonify({"error": "Insufficient permissions"}), 403

    email = decoded_token.get("email")
    if not email:
        return jsonify({"error": "Email not found in token"}), 401

    data = request.json
    try:
        db = get_db()
        db.execute(
            """
            INSERT INTO students (
                email, name, course, enrollment_date, expected_graduation,
                gpa, credits_completed, major, minor
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            [
                email,
                data["name"],
                data["course"],
                data["enrollment_date"],
                data.get("expected_graduation"),  # Optional field
                data.get("gpa", 0.0),  # Default to 0.0 if not provided
                data.get("credits_completed", 0),  # Default to 0 if not provided
                data["major"],
                data.get("minor"),  # Optional field
            ],
        )
        db.commit()
        return jsonify({"message": "POST request successful", "data": data}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Student with this email already exists"}), 400


@app.route("/api/resource", methods=["PUT"])
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
            - major
          properties:
            name:
              type: string
            course:
              type: string
            enrollment_date:
              type: string
              format: date
            expected_graduation:
              type: string
              format: date
            gpa:
              type: number
              format: float
            credits_completed:
              type: integer
            major:
              type: string
            minor:
              type: string
    responses:
      200:
        description: Student data updated successfully
      401:
        description: Unauthorized - Invalid or missing token
      403:
        description: Forbidden - Insufficient permissions
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    decoded_token = validate_token(auth_header)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired token"}), 401

    roles = (
        decoded_token.get("resource_access", {}).get(CLIENT_ID, {}).get("roles", [])
    )
    if "Student" not in roles:
        return jsonify({"error": "Insufficient permissions"}), 403

    email = decoded_token.get("email")
    if not email:
        return jsonify({"error": "Email not found in token"}), 401

    data = request.json
    db = get_db()
    db.execute(
        """
        UPDATE students 
        SET name = ?, course = ?, enrollment_date = ?, expected_graduation = ?,
            gpa = ?, credits_completed = ?, major = ?, minor = ?
        WHERE email = ?
    """,
        [
            data["name"],
            data["course"],
            data.get("enrollment_date"),
            data.get("expected_graduation"),
            data.get("gpa", 0.0),
            data.get("credits_completed", 0),
            data["major"],
            data.get("minor"),
            email,
        ],
    )
    db.commit()
    return jsonify({"message": "PUT request successful", "data": data})


@app.route("/api/resource", methods=["DELETE"])
def delete_resource():
    """
    Delete student record for the authenticated user.
    ---
    tags:
      - Student Resources
    security:
      - Bearer: []
    responses:
      200:
        description: Student deleted successfully
      401:
        description: Unauthorized - Invalid or missing token
      403:
        description: Forbidden - Insufficient permissions
      404:
        description: Not found - No student record found for this email
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return jsonify({"error": "Missing Authorization header"}), 401

    decoded_token = validate_token(auth_header)
    if not decoded_token:
        return jsonify({"error": "Invalid or expired token"}), 401

    roles = (
        decoded_token.get("resource_access", {}).get(CLIENT_ID, {}).get("roles", [])
    )
    if "Student" not in roles:
        return jsonify({"error": "Insufficient permissions"}), 403

    email = decoded_token.get("email")
    if not email:
        return jsonify({"error": "Email not found in token"}), 401

    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM students WHERE email = ?", [email])
    db.commit()

    # Check if any row was actually deleted
    if cursor.rowcount == 0:
        return jsonify({"error": "No student record found for this email"}), 404

    return jsonify({"message": "DELETE request successful"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5001)
