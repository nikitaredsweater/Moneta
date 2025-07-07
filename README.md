# 🚀 FastAPI Starter Project

Welcome to this FastAPI project! This guide will walk you through setting up everything from scratch — perfect for beginners.

## 📋 Table of Contents

- [📦 What is FastAPI?](#-what-is-fastapi)
- [🛠️ Getting Started](#️-getting-started)
  - [✅ Requirements](#-requirements)
- [🐍 Step 1: Set Up a Virtual Environment](#-step-1-set-up-a-virtual-environment-venv)
- [📥 Step 2: Install Project Dependencies](#-step-2-install-project-dependencies)
  - [Option 1: Using requirements.txt](#option-1-using-requirementstxt-basic)
  - [Option 2: Using pip-tools](#option-2-using-pip-tools-recommended)
- [🚀 Step 3: Run the FastAPI App](#-step-3-run-the-fastapi-app)
- [📚 Step 4: View the API Documentation](#-step-4-view-the-api-documentation)
- [🔍 Step 5: Set Up Automated Code Quality Checks](#-step-5-set-up-automated-code-quality-checks)
  - [Setting Up Pre-commit Hooks](#️-setting-up-pre-commit-hooks)
  - [Manual Code Quality Checks](#-manual-code-quality-checks)
  - [Configuration Files](#-configuration-files)
- [🌳 Step 6: Git Workflow and Branching Strategy](#-step-6-git-workflow-and-branching-strategy)
  - [Branch Structure](#-branch-structure)
  - [Standard Development Workflow](#-standard-development-workflow)
  - [Commit Message Convention](#-commit-message-convention)
  - [Pull Request Guidelines](#-pull-request-guidelines)
  - [Best Practices](#-best-practices)
- [🫼 How to Deactivate the Virtual Environment](#-how-to-deactivate-the-virtual-environment)
- [🧠 Tips for Beginners](#-tips-for-beginners)
- [📁 Project Structure](#-project-structure-example)
- [💬 Need Help?](#-need-help)

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

## 🌳 Step 6: Git Workflow and Branching Strategy

This project follows a structured branching strategy to ensure code quality and smooth deployments.

### 🔀 Branch Structure

Our repository uses the following branch hierarchy:

- **`main`** - Production branch (always deployable, protected)
- **`dev`** - Development branch (integration branch for new features)
- **`feature/*`** - Feature development branches
- **`fix/*`** - Bug fix branches
- **`hotfix/*`** - Critical production fixes
- **`release/*`** - Release preparation branches

### 🚀 Branch Descriptions

#### 🏭 `main` Branch

- **Purpose**: Production-ready code that's currently deployed
- **Protection**: Protected branch, no direct pushes allowed
- **Updates**: Only receives updates from `dev` via pull requests
- **Deployment**: Automatically deployed to production

#### 🔧 `dev` Branch

- **Purpose**: Main integration branch for development
- **Target**: Default branch for all feature pull requests
- **Testing**: All features are tested here before merging to `main`
- **Stability**: Should always be in a working state

#### 🎯 Feature Branches (`feature/*`)

- **Purpose**: Development of new features
- **Naming**: `feature/ticket-name` or `feature/description`
- **Source**: Created from `dev` branch
- **Target**: Merged back to `dev` via pull request

#### 🐛 Fix Branches (`fix/*`)

- **Purpose**: Bug fixes and minor improvements
- **Naming**: `fix/ticket-name` or `fix/description`
- **Source**: Created from `dev` branch
- **Target**: Merged back to `dev` via pull request

#### 🚨 Hotfix Branches (`hotfix/*`)

- **Purpose**: Critical production issues requiring immediate fix
- **Naming**: `hotfix/ticket-name` or `hotfix/description`
- **Source**: Created from `main` branch
- **Target**: Merged to both `main` and `dev`

#### 📦 Release Branches (`release/*`)

- **Purpose**: Prepare releases, final testing, and version bumping
- **Naming**: `release/v1.2.3` or `release/sprint-name`
- **Source**: Created from `dev` branch
- **Target**: Merged to both `main` and `dev`

### 🔄 Standard Development Workflow

Follow these steps to contribute new code:

#### Step 6.1: Start from Dev Branch

```bash
# Switch to dev branch
git checkout dev

# Pull latest changes
git pull origin dev
```

#### Step 6.2: Create a New Branch

Use the following naming convention:

```bash
# For new features
git checkout -b feature/user-authentication
git checkout -b feature/API-123-payment-integration

# For bug fixes
git checkout -b fix/login-validation-error
git checkout -b fix/BUG-456-memory-leak

# For hotfixes (from main branch)
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-patch
```

#### Step 6.3: Develop and Commit

```bash
# Make your changes
# ... code development ...

# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add user authentication endpoint"
```

#### Step 6.4: Push and Create Pull Request

```bash
# Push your branch
git push origin feature/user-authentication

# Create pull request via GitHub/GitLab interface
```

### 📝 Commit Message Convention

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Commit Types:

- **`feat`**: New feature
- **`fix`**: Bug fix
- **`docs`**: Documentation changes
- **`style`**: Code style changes (formatting, missing semicolons, etc.)
- **`refactor`**: Code refactoring without changing functionality
- **`test`**: Adding or updating tests
- **`chore`**: Maintenance tasks, dependency updates

#### Examples:

```bash
git commit -m "feat: add user registration endpoint"
git commit -m "fix: resolve validation error in login form"
git commit -m "docs: update API documentation for auth endpoints"
git commit -m "refactor: optimize database query performance"
git commit -m "test: add unit tests for payment processing"
git commit -m "chore: update dependencies to latest versions"
```

### 🔄 Pull Request Guidelines

#### 🚧 Work in Progress (WIP)

For incomplete work, prefix your pull request title with `[WIP]`:

```
[WIP] feature/user-authentication - Add OAuth integration
```

#### ✅ Ready for Review

When your work is complete:

1. **Remove `[WIP]` prefix**
2. **Ensure all tests pass**
3. **Update documentation if needed**
4. **Request review from team members**

#### 📋 Pull Request Template

Include in your PR description:

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing

- [ ] All tests pass
- [ ] New tests added (if applicable)
- [ ] Manual testing completed

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated (if needed)
```

### 🔒 Branch Protection Rules

The following branches have protection rules:

- **`main`**: Requires PR review, passing CI/CD, up-to-date with base branch
- **`dev`**: Requires passing CI/CD checks

### 💡 Best Practices

- **Keep branches small**: Focus on one feature/fix per branch
- **Regular updates**: Sync with `dev` regularly to avoid conflicts
- **Descriptive names**: Use clear, descriptive branch names
- **Clean history**: Use interactive rebase to clean up commits before merging
- **Delete merged branches**: Clean up merged branches to keep repository tidy

```bash
# Delete local branch after merge
git branch -d feature/user-authentication

# Delete remote branch
git push origin --delete feature/user-authentication
```

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
