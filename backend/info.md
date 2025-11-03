# Creating a Virtual Environment and Installing Python Libraries on Windows

## Prerequisites

- Python must be installed on your system (download from python.org if needed)
- Command Prompt or PowerShell access

## Step 1: Create a Virtual Environment

Open Command Prompt or PowerShell and navigate to your project directory:

```cmd
cd path\to\your\project
```

Create a virtual environment named `venv`:

```cmd
python -m venv venv
```

**Note:** You can replace the second `venv` with any name you prefer for your virtual environment.

## Step 2: Activate the Virtual Environment

To activate the virtual environment:

**Using Command Prompt:**

```cmd
venv\Scripts\activate
```

**Using PowerShell:**

```powershell
venv\Scripts\Activate.ps1
```

**Troubleshooting PowerShell:** If you get an execution policy error, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Once activated, you should see `(venv)` at the beginning of your command line.

## Step 3: Install Python Libraries

With the virtual environment activated, install packages using pip:

**Install a single package:**

```cmd
pip install package-name
```

**Install multiple packages:**

```cmd
pip install package1 package2 package3
```

**Install from a requirements file:**

```cmd
pip install -r requirements.txt
```

**Install a specific version:**

```cmd
pip install package-name==1.2.3
```

## Step 4: Verify Installation

Check installed packages:

```cmd
pip list
```

Check a specific package:

```cmd
pip show package-name
```

## Step 5: Deactivate the Virtual Environment

When you're done working:

```cmd
deactivate
```

## Creating a Requirements File

To save your installed packages for sharing or deployment:

```cmd
pip freeze > requirements.txt
```

## Common Commands Summary

| Action                | Command                         |
| --------------------- | ------------------------------- |
| Create venv           | `python -m venv venv`           |
| Activate (CMD)        | `venv\Scripts\activate`         |
| Activate (PowerShell) | `venv\Scripts\Activate.ps1`     |
| Install package       | `pip install package-name`      |
| List packages         | `pip list`                      |
| Save requirements     | `pip freeze > requirements.txt` |
| Deactivate            | `deactivate`                    |

## Example Workflow

```cmd
# Navigate to project
cd C:\Users\YourName\myproject

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install packages
pip install numpy pandas matplotlib

# Work on your project...

# Deactivate when done
deactivate
```

## Tips

- Always activate your virtual environment before installing packages
- Keep your `requirements.txt` file updated for collaboration
- Use descriptive names for virtual environments if managing multiple projects
- Add `venv/` to your `.gitignore` file to avoid committing it to version control
