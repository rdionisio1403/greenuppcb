# GreenUpPCB LIS — Deployment Instructions

## 1. Overview

GreenUpPCB LIS is deployed on an Ubuntu/Linux server using the following architecture:

- Frontend: React + Vite
- Backend: Python + FastAPI
- Application server: Uvicorn
- Process management: systemd
- Reverse proxy and static file server: Nginx
- Database: PostgreSQL
- Database migrations: Alembic
- Version control: Git

Production project directory:

    /opt/greenupcb/

Production domain:

    https://greenuppcb.ipcb.pt

Main application:

    https://greenuppcb.ipcb.pt/

Administrator-only endpoints:

    https://greenuppcb.ipcb.pt/docs
    https://greenuppcb.ipcb.pt/redoc
    https://greenuppcb.ipcb.pt/openapi.json
    https://greenuppcb.ipcb.pt/view-table

---

## 2. Server Requirements

The deployment requires:

- Ubuntu/Linux
- Python 3
- Python virtual environment support
- Node.js
- npm
- PostgreSQL
- Nginx
- Git
- systemd

The production database is PostgreSQL.

---

## 3. Project Structure

The main project structure is:

    /opt/greenupcb/
    ├── backend/
    │   ├── app/
    │   ├── alembic/
    │   ├── alembic.ini
    │   ├── requirements.txt
    │   ├── .env
    │   └── .venv/
    ├── frontend/
    │   ├── src/
    │   ├── public/
    │   ├── package.json
    │   ├── package-lock.json
    │   └── dist/
    ├── database/
    ├── documentation/
    ├── images/
    ├── reports/
    ├── .gitignore
    ├── README.md
    └── DEPLOYMENT.md

---

## 4. Repository Setup

The source code repository is:

    https://github.com/rdionisio1403/greenuppcb

To clone the repository on a new server:

    cd /opt
    sudo git clone https://github.com/rdionisio1403/greenuppcb.git greenupcb
    cd /opt/greenupcb

The production deployment uses the development branch:

    git checkout development

To update the local repository:

    cd /opt/greenupcb
    git pull origin development

---

## 5. Backend Setup

The FastAPI backend is located at:

    /opt/greenupcb/backend

Move to the backend directory:

    cd /opt/greenupcb/backend

Create the Python virtual environment:

    python3 -m venv .venv

Activate the virtual environment:

    source .venv/bin/activate

Install backend dependencies:

    pip install -r requirements.txt

The production virtual environment is:

    /opt/greenupcb/backend/.venv

---

## 6. Environment Variables

Production-specific configuration is stored in:

    /opt/greenupcb/backend/.env

The `.env` file contains environment-specific settings such as:

- Database connection information
- Application secrets
- Authentication configuration
- Other production-specific variables

The `.env` file must not be committed to GitHub.

Actual production secret values are intentionally excluded from this documentation.

---

## 7. Database Configuration

GreenUpPCB LIS uses PostgreSQL as its production database.

Check the PostgreSQL service:

    sudo systemctl status postgresql --no-pager

Database credentials and connection settings are provided through the backend environment configuration.

The application should only be started after confirming that the database is available and the configured connection is valid.

---

## 8. Database Migrations

Database schema changes are managed with Alembic.

Alembic configuration:

    /opt/greenupcb/backend/alembic.ini

Migration directory:

    /opt/greenupcb/backend/alembic/

Migration versions:

    /opt/greenupcb/backend/alembic/versions/

Activate the backend environment:

    cd /opt/greenupcb/backend
    source .venv/bin/activate

Check the current migration:

    alembic current

View migration history:

    alembic history

Apply pending migrations:

    alembic upgrade head

To create a new migration after modifying the SQLAlchemy models:

    alembic revision --autogenerate -m "describe change"

Review the generated migration file before applying it:

    alembic upgrade head

Migration files are part of the source code and must be committed to version control.

---

## 9. Backend Application Server

The backend is a FastAPI application served by Uvicorn.

Application entry point:

    app.main:app

Production Uvicorn command:

    /opt/greenupcb/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

The application listens on port:

    8000

Nginx forwards public API requests to the backend service.

---

## 10. systemd Service

The backend is managed by:

    greenuppcb-backend.service

The service configuration uses:

    WorkingDirectory=/opt/greenupcb/backend
    EnvironmentFile=/opt/greenupcb/backend/.env
    ExecStart=/opt/greenupcb/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

Check the service status:

    sudo systemctl status greenuppcb-backend --no-pager

Start the backend:

    sudo systemctl start greenuppcb-backend

Stop the backend:

    sudo systemctl stop greenuppcb-backend

Restart the backend:

    sudo systemctl restart greenuppcb-backend

Enable the backend at system startup:

    sudo systemctl enable greenuppcb-backend

View recent backend logs:

    sudo journalctl -u greenuppcb-backend -n 100 --no-pager

Follow backend logs in real time:

    sudo journalctl -u greenuppcb-backend -f

---

## 11. Backend Verification

The backend is available internally through port 8000.

Test the Swagger endpoint locally:

    curl http://127.0.0.1:8000/docs

Test the OpenAPI endpoint locally:

    curl http://127.0.0.1:8000/openapi.json

Check whether Uvicorn is listening on port 8000:

    sudo ss -ltnp | grep 8000

---

## 12. Frontend Setup

The frontend is a React application built with Vite.

Frontend directory:

    /opt/greenupcb/frontend

Move to the frontend directory:

    cd /opt/greenupcb/frontend

Install frontend dependencies:

    npm install

Create the production build:

    npm run build

The production build is generated in:

    /opt/greenupcb/frontend/dist

Nginx serves the production files from the `dist` directory.

---

## 13. Nginx Configuration

Nginx is the public-facing web server and reverse proxy.

Production hostname:

    greenuppcb.ipcb.pt

Frontend root:

    /opt/greenupcb/frontend/dist

Backend proxy target:

    http://127.0.0.1:8000

The active configuration contains HTTP and HTTPS server blocks. The HTTPS
server listens on port 443, uses the configured certificate and private key,
and sends an HSTS header. The HTTP server listens on port 80.

The Nginx configuration provides routes for:

    /auth/
    /pcbs
    /users
    /customers
    /docs
    /redoc
    /openapi.json
    /view-table
    /dashboard/summary
    /uploads/

Inspect the active Nginx configuration:

    sudo grep -nE 'server_name|listen|location|proxy_pass|root' /etc/nginx/sites-enabled/greenuppcb

Inspect the effective security headers:

    sudo nginx -T 2>/dev/null | grep -nEi 'Content-Security-Policy|Strict-Transport-Security|X-Content-Type-Options|X-Frame-Options|Referrer-Policy'

Test the Nginx configuration:

    sudo nginx -t

Reload Nginx after approved configuration changes:

    sudo systemctl reload nginx

Check the Nginx service:

    sudo systemctl status nginx --no-pager

Do not change TLS certificates, HTTPS settings, or security headers without
the required authorization and a reviewed configuration change.

---

## 14. Production Endpoints

Main application:

    https://greenuppcb.ipcb.pt/

The following API documentation and database-view endpoints require
administrator authentication:

    https://greenuppcb.ipcb.pt/docs
    https://greenuppcb.ipcb.pt/redoc
    https://greenuppcb.ipcb.pt/openapi.json
    https://greenuppcb.ipcb.pt/view-table

An unauthenticated request to an administrator-only endpoint is expected
to be rejected. Do not make these endpoints public to simplify access.

---

## 15. Authentication

The application provides authentication endpoints under:

    /auth/

Protected API endpoints require a valid authenticated session. The session is
maintained using the `__Host-session_id` cookie.

Session cookie security settings:

- `HttpOnly`: JavaScript cannot read the session cookie.
- `Secure`: The browser sends the cookie only over HTTPS.
- `SameSite=Lax`: Provides an additional cross-site request restriction.
- Cookie prefix: `__Host-`, which requires HTTPS, the root path, and no Domain
  attribute in a compliant browser.
- Maximum session duration: 1 hour.
- Idle timeout: 30 minutes without activity.

Write operations protected by CSRF validation must include the expected
CSRF token. Do not disable authentication or CSRF checks to resolve access
problems.

After deployment, verify the following in the deployed environment:

- Login and logout.
- Access to protected endpoints while authenticated.
- Rejection of unauthenticated requests.
- Session expiration after the configured duration or idle timeout.
- CSRF validation for protected write operations.
- Admin-only access to user-management and API documentation endpoints.
- Session-cookie clearing after logout and password change.

Password and account security status:

- Authenticated password changes and `PASSWORD_CHANGED` audit events are
  implemented in the application code.
- Password-reset request and confirmation endpoints exist, but email delivery
  is disabled because an approved delivery provider is not configured.
- MFA/2FA and re-authentication for sensitive actions have not been verified.
- A concurrent-session limit has not been verified.

Do not describe unverified controls as operational. If a session expires,
sign in again and retry the request. Never make protected endpoints public as
a workaround.

---

## 16. File Uploads

Uploaded PCB-related files are stored under:

    /opt/greenupcb/backend/uploads/

The uploads directory is exposed through the Nginx `/uploads/` route.

Uploaded files should be included in server backup procedures when required.

---

## 17. Backup and Recovery

Database backups are maintained separately from the Git repository.

A PostgreSQL backup file may be stored on the production server, for example:

    /opt/greenupcb/backend/greenupcb_lis_2026-09-23.backup

Database backup files must not be committed to GitHub.

Backups may contain application data and must therefore be stored securely with appropriate access permissions.

A PostgreSQL backup can be created with:

    pg_dump -Fc DATABASE_NAME > greenupcb_backup.backup

A backup can be restored with:

    pg_restore -d DATABASE_NAME greenupcb_backup.backup

The exact database name, username, host, and authentication method depend on the production environment configuration.

---

## 18. Files That Must Not Be Committed

The following files and directories are environment-specific, sensitive, generated, or temporary and should not be committed to GitHub:

    backend/.env
    backend/.venv/
    backend/uploads/
    frontend/.env
    frontend/node_modules/
    frontend/dist/
    database backup files
    generated log files
    temporary server files

Production database backups must remain outside the Git repository.

---

## 19. Git and Version Control

The repository should contain:

- Source code
- Documentation
- README
- Deployment instructions
- Database migration files
- `.gitignore`

The deployment documentation file is:

    DEPLOYMENT.md

Before committing changes, review the repository status:

    cd /opt/greenupcb
    git status

Review changed files:

    git diff

Check tracked files:

    git ls-files

---

## 20. Production Update Procedure

Update the source code:

    cd /opt/greenupcb
    git pull origin development

Update backend dependencies when necessary:

    cd /opt/greenupcb/backend
    source .venv/bin/activate
    pip install -r requirements.txt

Apply database migrations:

    alembic upgrade head

Restart the backend:

    sudo systemctl restart greenuppcb-backend

Build the frontend:

    cd /opt/greenupcb/frontend
    npm install
    npm run build

Reload Nginx:

    sudo systemctl reload nginx

Verify the backend:

    sudo systemctl status greenuppcb-backend --no-pager

Verify Nginx:

    sudo nginx -t

---

## 21. New Server Deployment Procedure

For a new Ubuntu/Linux server, the general deployment sequence is:

### Step 1 — Clone the repository

    cd /opt
    sudo git clone https://github.com/rdionisio1403/greenuppcb.git greenupcb
    cd /opt/greenupcb
    git checkout development

### Step 2 — Configure the backend

    cd /opt/greenupcb/backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Create the production environment file:

    /opt/greenupcb/backend/.env

### Step 3 — Configure the database

Verify PostgreSQL:

    sudo systemctl status postgresql --no-pager

Verify the database connection settings in:

    /opt/greenupcb/backend/.env

### Step 4 — Apply migrations

    cd /opt/greenupcb/backend
    source .venv/bin/activate
    alembic upgrade head

### Step 5 — Configure the backend service

Install and enable the `greenuppcb-backend.service` systemd service.

Start the service:

    sudo systemctl start greenuppcb-backend

Enable it at boot:

    sudo systemctl enable greenuppcb-backend

### Step 6 — Build the frontend

    cd /opt/greenupcb/frontend
    npm install
    npm run build

### Step 7 — Configure Nginx

Set the production hostname:

    greenuppcb.ipcb.pt

Configure the frontend root:

    /opt/greenupcb/frontend/dist

Configure the backend proxy target:

    http://127.0.0.1:8000

Test the configuration:

    sudo nginx -t

Reload Nginx:

    sudo systemctl reload nginx

### Step 8 — Verify the deployment

Open the application over HTTPS:

    https://greenuppcb.ipcb.pt/

Verify Swagger and OpenAPI while authenticated as an administrator:

    https://greenuppcb.ipcb.pt/docs
    https://greenuppcb.ipcb.pt/openapi.json

Unauthenticated requests to these administrator-only endpoints should be rejected.

---

## 22. Troubleshooting

### Backend Is Not Running

Check service status:

    sudo systemctl status greenuppcb-backend --no-pager

Check recent logs:

    sudo journalctl -u greenuppcb-backend -n 100 --no-pager

Follow live logs:

    sudo journalctl -u greenuppcb-backend -f

### Nginx Is Not Working

Test the configuration:

    sudo nginx -t

Check the service:

    sudo systemctl status nginx --no-pager

Reload the service:

    sudo systemctl reload nginx

### API Is Not Reachable

Check port 8000:

    sudo ss -ltnp | grep 8000

Test the backend locally:

    curl http://127.0.0.1:8000/docs

Check the backend service:

    sudo systemctl status greenuppcb-backend --no-pager

### Frontend Changes Are Not Visible

Rebuild the frontend:

    cd /opt/greenupcb/frontend
    npm run build

Reload Nginx:

    sudo systemctl reload nginx

### Database Migration Problems

Check the current revision:

    cd /opt/greenupcb/backend
    source .venv/bin/activate
    alembic current

View migration heads:

    alembic heads

View migration history:

    alembic history

Apply migrations:

    alembic upgrade head

---

## 23. Security Notes

Production secrets must be stored in environment files or another secure
secret-management system.

Do not commit:

- Database passwords
- API keys
- Authentication secrets
- Production `.env` files
- PostgreSQL backup files
- Sensitive production data
- Generated server logs

Database backups must be stored separately from the source code repository.

### Verified by Code Review

- The session cookie is named `__Host-session_id`.
- Login sets the cookie with `HttpOnly`, `Secure`, and `SameSite=Lax`.
- The application defines a one-hour maximum session duration and a
  30-minute idle timeout.
- CSRF validation is required for protected write operations.
- Authenticated password changes are implemented.
- Password changes generate a `PASSWORD_CHANGED` audit event.
- Password-reset request and confirmation endpoints exist.
- API documentation and the database view require administrator access.
- Logout, password change, and password-reset confirmation clear the session
  cookie using `Secure` and `Path=/` settings.

These findings reflect code review and configuration inspection. They do not
replace runtime verification of every security behavior.

### Known Limitations and Unverified Controls

- Password-reset email delivery is disabled. An approved email provider has
  not been configured; email-based password reset is not operational.
- The effective Nginx configuration search did not show a
  `Content-Security-Policy` header. CSP must not be considered deployed until
  it is configured and verified.
- Multi-factor authentication (MFA/2FA) has not been verified as implemented.
- Re-authentication for sensitive actions has not been verified.
- A concurrent-session limit has not been verified.
- Automated tests have not specifically verified cookie-clearing behavior
  for logout and authenticated password changes.
- Password-reset token security tests passed, but this does not establish that
  every password-reset endpoint behavior has been tested in production.

Only required production services and ports should be publicly accessible.
Do not expose administrator-only endpoints or disable security checks to
work around authentication or session-expiration issues.

## 24. Deployment Architecture

The GreenUpPCB LIS production architecture is:

    React + Vite
          |
          v
        Nginx
          |
          v
    FastAPI / Uvicorn
          |
          v
      PostgreSQL

The backend application is managed by:

    systemd

Database schema changes are managed by:

    Alembic

The frontend production build is generated with:

    npm run build

---

## 25. Deployment Checklist

Before considering a deployment complete, verify:

- Repository source code is available
- README is available
- DEPLOYMENT.md reflects the current implementation and deployment
- Alembic migration files are available
- `.gitignore` is configured
- Backend virtual environment is configured
- Production environment variables are configured without exposing secrets
- PostgreSQL is running
- Database migrations are applied
- FastAPI backend is running
- systemd service is active
- Frontend production build exists
- Nginx configuration is valid and Nginx is running
- HTTPS certificate and HTTPS endpoint are verified
- HSTS is present in the effective HTTPS configuration
- CSP is configured and verified; otherwise record it as not enabled
- Frontend is accessible
- Login, logout, session expiration, and CSRF protection are tested
- Session-cookie clearing is tested after logout and password change
- Administrator-only endpoints reject unauthenticated requests
- API documentation and database view work for an authorized administrator
- Password-reset email delivery is not described as operational while disabled
- Database backup is stored separately from Git

Track MFA/2FA, sensitive-action re-authentication, and concurrent-session
limits as open items until their implementation is verified.

---

## 26. Summary

GreenUpPCB LIS is deployed on an Ubuntu/Linux server using React, Vite, FastAPI, Uvicorn, systemd, Nginx, PostgreSQL, Alembic, and Git.

The production project directory is:

    /opt/greenupcb

The main production application is available at:

    https://greenuppcb.ipcb.pt/

Administrator-only API documentation is available at:

    https://greenuppcb.ipcb.pt/docs

The project repository is:

    https://github.com/rdionisio1403/greenuppcb

Database backups are maintained separately from the Git repository and must not be committed to GitHub.
