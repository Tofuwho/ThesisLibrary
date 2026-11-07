# TCU Theses Library Archiver 📚🎓

[![GitHub Pages Live Demo](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-maroon?style=for-the-badge&logo=github)](https://tofuwho.github.io/ThesisLibrary/)
[![Open in GitHub Codespaces](https://img.shields.io/badge/1--Click%20Demo-GitHub%20Codespaces-blue?style=for-the-badge&logo=github)](https://codespaces.new/Tofuwho/ThesisLibrary)
[![Django](https://img.shields.io/badge/Django-4.2-green?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Deploy to Render](https://img.shields.io/badge/Deploy%20to-Render-46E3B7?style=for-the-badge&logo=render)](https://render.com/deploy?repo=https://github.com/Tofuwho/ThesisLibrary)

> **Official Digital Academic Repository for Taguig City University (TCU).**  
> Preserving, cataloging, and disseminating capstone projects, undergraduate theses, and graduate dissertations across all collegiate departments.

---

## 🚀 Live Demo Options for GitHub

You can test and explore the TCU Thesis Library directly from GitHub without installing anything locally:

### 1. 🌐 Interactive Browser Demo (GitHub Pages)
👉 **[Launch GitHub Pages Live Demo](https://tofuwho.github.io/ThesisLibrary/)**
* **Instant access** directly from any web browser or mobile device.
* Browse the full thesis catalog with **real-time live search** and department filters (CICT, CAS, CBA, CED, COE, CCJ, GS).
* Explore the manuscript viewer with protected **view-only watermarking**.
* Preview the **Admin Analytics Dashboard** with interactive Chart.js graphs.
* Switch between simulated user roles (**Admin, Student, Librarian, Faculty**).

---

### 2. 💻 Full Dynamic Backend Demo (GitHub Codespaces)
👉 [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Tofuwho/ThesisLibrary)

Launch the **complete live Django backend** in GitHub Codespaces with **1 click**:
* Automatically provisions a Python 3.11 cloud container.
* Automatically initializes SQLite database with sample theses and accounts.
* Starts the Django development server on port `8000`.
* Forwards the port and opens the live web app in your browser!

---

## 🔑 Demo Account Credentials

When using GitHub Codespaces, Docker, or local setup, use these pre-seeded demo accounts:

| Role | Username | Password | Access Scope |
|---|---|---|---|
| 🛡️ **Administrator** | `admin` | `admin12345` | Full system oversight, admin dashboard, user management, and audit logs |
| 📖 **Librarian** | `librarian` | `librarian12345` | Archival moderation, Library of Congress (LC) classification, accessioning |
| 👨‍🏫 **Professor / Faculty** | `professor` | `professor12345` | Research guidance, advisee oversight, faculty research portal |
| 🎓 **Student** | `student` | `student12345` | Multi-step submission portal, tracking submissions, thesis search |

---

## ✨ Key Features

* **Multi-Department Scholarly Search**: Filter research by college (CICT, CAS, CBA, CED, COE, CCJ, CHTM, GS), degree course, category, and publication year.
* **Anti-Leak & View-Only Protection**: PDF manuscripts are rendered with watermarking; direct downloads are disabled to protect student intellectual property.
* **Interactive Submission Portal**: Multi-step wizard with auto-save, co-author tagging, supervisor linking, and file upload validation.
* **Admin Analytics & Moderation Dashboard**: Real-time charts for submission volumes by college, monthly trend analysis, approval/rejection queue, and audit logs.
* **Zero-Dependency SQLite Fallback**: Runs immediately on SQLite out-of-the-box, with optional MariaDB/MySQL support for production environments.
* **Responsive Mobile & Desktop UI**: Designed with TCU's official university maroon and gold aesthetic, animated canvas hero, and accessible typography.

---

## 🛠️ Local Installation & Setup

### Prerequisites
* **Python 3.11+** installed ([python.org](https://www.python.org/))
* **Git** installed ([git-scm.com](https://git-scm.com/))

### Quick Start (Plug & Play SQLite Mode)

```bash
# 1. Clone the repository
git clone https://github.com/Tofuwho/ThesisLibrary.git
cd ThesisLibrary

# 2. (Optional) Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Migrate database and seed demo data
python seed_demo_data.py

# 5. Start the development server
python manage.py runserver
```

Open your browser at **`http://localhost:8000`** to access the library.

---

### Using MySQL / MariaDB (XAMPP Setup)

If you prefer using MySQL/MariaDB (e.g. through XAMPP):

1. Start **Apache** and **MySQL** in your XAMPP Control Panel.
2. Create a `.env` file in the root directory:
   ```env
   DB_ENGINE=mysql
   DB_NAME=thesis_library
   DB_USER=root
   DB_PASSWORD=
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DJANGO_DEBUG=True
   ```
3. Run migrations and start the server:
   ```bash
   python seed_demo_data.py
   python manage.py runserver
   ```
   *(Or double-click `StartLibraryServer.bat` on Windows)*

---

## 🐳 Docker Deployment

To run the application using Docker:

```bash
# Build and start container
docker-compose up --build
```

Access the app at **`http://localhost:8000`**.

---

## ☁️ 1-Click Cloud Deployment (Render / Railway)

This repository includes a `render.yaml` blueprint and `Procfile`.

1. Fork or push this repository to GitHub.
2. Sign in to [Render](https://render.com).
3. Click **New +** -> **Blueprint** and select your repository.
4. Render will automatically build the app, apply migrations, seed demo accounts, and deploy the live web service!

---

## 📂 Project Structure

```
ThesisLibrary/
├── .devcontainer/            # GitHub Codespaces 1-click cloud environment config
│   ├── devcontainer.json
│   └── setup.sh
├── .github/
│   └── workflows/
│       ├── deploy-pages.yml  # Automated GitHub Pages live demo deployment
│       └── main.yml          # Automated CI test suite
├── assets/                   # CSS, JavaScript modules, fonts, and university images
├── authapp/                  # User authentication, roles, and profiles
├── docs/                     # GitHub Pages static interactive live demo
│   ├── index.html            # Landing page with interactive particle hero
│   ├── categories.html       # Real-time searchable thesis catalog
│   ├── thesis_detail.html    # Detailed manuscript view with protected reader
│   ├── admin_preview.html    # Admin analytics charts & queue preview
│   └── about.html            # University archive policies and info
├── main/                     # Core Django app: models, views, templates, middleware
├── thesis_site/              # Django project settings and WSGI/ASGI configuration
├── seed_demo_data.py         # Database seeder for demo accounts and research papers
├── Dockerfile                # Docker container definition
├── docker-compose.yml        # Docker compose configuration
├── Procfile                  # Process file for Render / Railway / Heroku
├── render.yaml               # Render Infrastructure-as-Code blueprint
└── requirements.txt          # Python dependencies
```

---

## 🏛️ Academic Departments & Colleges

* **CICT** – College of Information and Communications Technology
* **CAS** – College of Arts and Sciences
* **CBA** – College of Business and Administration
* **CED** – College of Education
* **COE** – College of Engineering and Technology
* **CCJ** – College of Criminology
* **CHTM** – College of Hospitality and Tourism Management
* **GS** – Graduate Studies

---

## 📄 License & Attribution

Developed for **Taguig City University (TCU)**.  
Repository maintained by [Tofuwho](https://github.com/Tofuwho).
