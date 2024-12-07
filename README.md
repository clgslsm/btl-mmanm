How to install the project:

---

### **Step 1: Prerequisites**
Ensure the following tools are installed on your system:
- **Docker** and **Docker Compose** (for managing containers)

---

### **Step 2: Edit the Hosts File**
Add the following entries to your `hosts` file:

**Linux**:
1. Open the `hosts` file:
   ```bash
   sudo nano /etc/hosts
   ```
2. Add the following lines at the end:
   ```
   127.0.0.1 sso.example.org
   127.0.0.1 first.example.org
   127.0.0.1 second.example.org
   ```
3. Save and exit (Ctrl+O, Enter, Ctrl+X).

**Windows**:
1. Navigate to `C:\Windows\System32\drivers\etc\hosts`.
2. Open the `hosts` file with administrative privileges (e.g., Notepad as Administrator).
3. Add the same lines and save.

---

### **Step 3: Start Services Using Docker Compose**
1. Navigate to the root of the project directory where `docker-compose.yml` is located.
2. Build and start the containers:
   ```bash
   docker-compose up --build
   ```
3. This command will build and start all necessary services, including Keycloak, LDAP, and Nginx.

---

### **Step 4: Verify Services**
After the Docker containers are running:
1. Open a browser and check the following:
   - **SSO Login Page**: [http://sso.example.org](http://sso.example.org)
   - **First Site**: [http://first.example.org](http://first.example.org)
   - **Second Site**: [http://second.example.org](http://second.example.org)

---

### **Step 5: Keycloak Configuration**
1. Import the realm configuration:
   - Access the Keycloak admin interface at [http://sso.example.org/auth](http://sso.example.org/auth).
   - Login with the admin credentials set in the `docker-compose.yml`.
   - Go to **Realm Settings** > **Import Realm** and upload `configs/keycloak/realm-export.json`.

2. Configure users and clients as needed for authentication.

---

### **Step 6: Running the Frontend and Backend**
For **First Site**:
1. The **backend** is handled via `app.py` (Flask) and serves REST APIs.
   - If running locally, navigate to `sites/first.example.site/backend` and run:
     ```bash
     python3 app.py
     ```
2. The **frontend** runs via a Node.js development server.
   - Navigate to `sites/first.example.site/frontend` and start the server:
     ```bash
     npm install
     npm start
     ```

For **Second Site**:
1. The backend (Flask app) can be started similarly:
   - Navigate to `sites/second.example.site` and run:
     ```bash
     python3 app.py
     ```

---

### **Step 7: Test SSO Integration**
1. Open `first.example.org` or `second.example.org` in your browser.
2. Attempt to log in via the SSO login page (`sso.example.org`).
3. Verify that user sessions work correctly across both sites.

---
