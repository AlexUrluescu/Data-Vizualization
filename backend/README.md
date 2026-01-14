# Urban Bike

A Flask-based server application that triggers a Panel web app build. This project uses uv for fast and reliable Python package management.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

1. Python 3.8+: Download Python
2. uv: This project relies on uv to manage dependencies and the virtual environment.

macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
Windows (PowerShell): `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

## 🚀 Installation & Setup

1. Clone the repository:
   `git clone https://github.com/your-username/your-repo-name.git`
   `cd your-repo-name`

2. Install dependencies: uv will automatically create a virtual environment and sync dependencies based on the lock file:
   uv sync

## 🏃‍♂️ How to Run the Application

You can start the server using either the universal uv command or the provided shell script.

### Option 1: Universal Method (Recommended for Windows & macOS)

This is the most reliable method as uv handles the virtual environment execution automatically.
`uv run app.py`

### Option 2: Using the Shell Script

If you prefer using the provided helper script:

1. macOS / Linux: Make sure the script is executable first:
   `chmod +x start.sh`
   `./start.sh`

2. Windows: You can run the .sh file if you are using Git Bash or WSL
   sh start.sh

Note: If you are using standard Command Prompt or PowerShell, please use Option 1.

## 🛠️ Development Notes

Virtual Environment: This project uses a virtual environment located in .venv. You usually do not need to activate it manually if you use uv run, but if you need to activate it for your IDE:

1. macOS/Linux: `source .venv/bin/activate`
2. Windows: `.venv\Scripts\activate`z

### Adding new packages: To add a new library to the project, run:

uv add <package_name>
