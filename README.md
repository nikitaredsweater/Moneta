# 🚀 FastAPI Starter Project

Welcome to this FastAPI project! This guide will walk you through setting up everything from scratch — perfect for beginners.

---

## 📦 What is FastAPI?

[FastAPI](https://fastapi.tiangolo.com/) is a modern Python web framework for building APIs quickly and efficiently. It has built-in support for automatic documentation and is one of the fastest Python frameworks available.

---

## 🛠️ Getting Started

### ✅ Requirements

- Python 3.8 or later
- Terminal / Command Line
- (Optional but recommended) Code editor like VS Code

---

## 🐍 Step 1: Set Up a Virtual Environment (venv)

A **virtual environment** keeps your project's dependencies isolated from other Python projects on your computer.

### 💡 Create and activate the environment:

```bash
# Create venv folder
python3 -m venv venv

# Activate it
source venv/bin/activate
```

```bash
# Create venv folder
python -m venv venv

# Activate it
venv\Scripts\activate
```

> ✅ When activated, your terminal prompt will show `(venv)`.

---

## 📥 Step 2: Install Project Dependencies

### Option 1: Using requirements.txt (Basic)

```bash
pip install -r requirements.txt
```

### Option 2: Using pip-tools (Recommended)

[pip-tools](https://github.com/jazzband/pip-tools) helps manage dependency versions cleanly by separating abstract requirements from pinned versions.

#### Step 2.1: Install pip-tools

```bash
pip install pip-tools
```

#### Step 2.2: Create a `requirements.in` file

This is where you list top-level dependencies, e.g.

```txt
fastapi
uvicorn[standard]
```

#### Step 2.3: Compile to requirements.txt

```bash
pip-compile requirements.in
```

This generates a fully pinned `requirements.txt`.

#### Step 2.4: Install from compiled file

```bash
pip install -r requirements.txt
```

> 💡 Update `requirements.in` when adding/removing dependencies, and re-run `pip-compile`.

---

## 🚀 Step 3: Run the FastAPI App

If your app's entry point is called `main.py` and it contains a FastAPI instance named `app`, use:

```bash
fastapi dev src/main.py
```

---

## 📚 Step 4: View the API Documentation

FastAPI automatically provides interactive documentation!

After running the app, open your browser and go to:

### Swagger UI:

```
http://127.0.0.1:8000/docs
```

### ReDoc:

```
http://127.0.0.1:8000/redoc
```

These pages let you explore and test your API directly from the browser.

---

## 🔍 Step 5: Set Up Automated Code Quality Checks

This project includes automated code quality checks and formatting tools to ensure consistent, high-quality code.

### ✅ What's Included

- **Code Formatting**: `black` and `isort` for consistent code style
- **Linting**: `flake8` and `pylint` for code quality checks
- **Security**: `bandit` for security vulnerability scanning
- **Type Checking**: `mypy` for static type analysis
- **File Checks**: Various pre-commit hooks for file consistency

### 🛠️ Setting Up Pre-commit Hooks

Pre-commit hooks automatically run these checks before each git commit, ensuring code quality.

#### Step 5.1: Install Pre-commit Hooks

```bash
pre-commit install
```

#### Step 5.2: Run Checks on All Files (Optional)

To run all checks on your entire codebase:

```bash
pre-commit run --all-files
```

Note: These checks will also run automatically whenever you run

```bash
git commit -m "...."
```

Note: It is not recommended, but if you need to force no pre-commit checks when committing, add the flag `--no-verify`:

```bash
git commit -m "...." --no-verify
```

### 🚦 How It Works

Once installed, pre-commit will automatically run these checks every time you try to commit code:

- **Automatic Formatting**: Code will be automatically formatted with `black` and `isort`
- **Quality Checks**: `flake8`, `pylint`, and other tools will check for issues
- **File Consistency**: Trailing whitespace, end-of-file issues, and other file problems will be fixed

If any check fails, the commit will be blocked until you fix the issues.

### 🔧 Manual Code Quality Checks

You can also run individual tools manually:

```bash
# Format code with black
black src/

# Sort imports with isort
isort src/

# Run linting with flake8
flake8 src/

# Run pylint
pylint src/

# Check types with mypy
mypy src/

# Security scan with bandit
bandit -r src/
```

### 📝 Configuration Files

The project includes configuration files for all tools:

- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `.pylintrc` - Pylint configuration
- `setup.cfg` - Configuration for flake8, bandit, and other tools

### 💡 Tips

- **First-time setup**: The first run of pre-commit may take a few minutes as it downloads and installs the tools
- **Skipping hooks**: If you need to commit without running hooks (not recommended), use `git commit --no-verify`
- **Updating hooks**: Run `pre-commit autoupdate` to update hook versions

---

## 🫼 How to Deactivate the Virtual Environment

When you're done working, simply type:

```bash
deactivate
```

---

## 🧠 Tips for Beginners

- Don't forget to activate your virtual environment every time you come back to the project.
- If you install a new package (e.g. `pip install somepackage`), update dependencies using:

```bash
pip-compile requirements.in
```

- Or if you're not using pip-tools:

```bash
pip freeze > requirements.txt
```

- Pre-commit hooks will help you maintain code quality automatically - don't bypass them unless absolutely necessary!

---

## 📁 Project Structure (example)

```
my-fastapi-app/
├── src/
│   └── main.py
├── requirements.in
├── requirements.txt
├── .pre-commit-config.yaml
├── .pylintrc
├── setup.cfg
├── venv/
└── README.md
```

---

## 💬 Need Help?

Check out the [FastAPI Docs](https://fastapi.tiangolo.com/) or feel free to ask!

---

Happy coding! 🐍🚀
