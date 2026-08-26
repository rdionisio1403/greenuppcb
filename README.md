# GreenUpPCB LIS (Laboratory Information System)

A lightweight, robust web-based Laboratory Information System designed for PCB diagnostic, repair, and lifecycle tracking at the **GreenUp PCB Laboratory** (Instituto Politécnico de Castelo Branco).

---

## 🎯 Project Goal
To replace manual or unstructured lab tracking with a structured, single-source-of-truth system that records incoming circuit boards, tracks diagnostic and repair actions, stores photographic evidence, and automatically generates standardized PDF service reports.

---

## 🛠 Tech Stack
* **Backend:** Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16
* **Frontend:** React 18, Vite, Lucide Icons, Vanilla/Modern CSS
* **Reporting & Storage:** ReportLab (PDF Generation), Pillow (Image Processing), Local File Storage
* **Deployment & Infrastructure:** Linux/Ubuntu Server, Nginx, Docker Compose, Git

---

## 📂 Repository Structure
```text
/opt/greenupcb/
├── backend/                 # FastAPI + SQLAlchemy API
│   ├── app/
│   │   ├── models/          # Database entity models
│   │   ├── schemas/         # Pydantic validation schemas
│   │   ├── routers/         # REST API endpoints
│   │   └── services/        # PDF generation and business logic
│   ├── alembic/             # Migration scripts
│   └── tests/               # Backend automated tests
├── frontend/                # React + Vite client app
├── documentation/           # Process workflow & MVP specifications
│   ├── requirements.md      # Screen list & user stories
│   └── workflow.md          # Full PCB lifecycle mapping
└── README.md                # Project documentation root

