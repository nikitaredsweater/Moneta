# 🚀 FastAPI Starter Project

Welcome to this FastAPI project! This guide will walk you through setting up everything from scratch — perfect for beginners.

---

## 📦 What is FastAPI?

[FastAPI](https://fastapi.tiangolo.com/) is a modern Python web framework for building APIs quickly and efficiently. It has built-in support for automatic documentation and is one of the fastest Python frameworks available.

---

## 🛠️ Getting Started

### ✅ Requirements

* Python 3.8 or later
* Terminal / Command Line
* (Optional but recommended) Code editor like VS Code

---

## 🐍 Step 1: Set Up a Virtual Environment (venv)

A **virtual environment** keeps your project’s dependencies isolated from other Python projects on your computer.

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

If your app’s entry point is called `main.py` and it contains a FastAPI instance named `app`, use:

```bash
uvicorn main:app --reload
```

### Explanation:

* `main` = filename (`main.py`)
* `app` = FastAPI app instance (`app = FastAPI()`)
* `--reload` = auto-reloads when you make code changes

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

## 🫼 How to Deactivate the Virtual Environment

When you’re done working, simply type:

```bash
deactivate
```

---

## 🧠 Tips for Beginners

* Don’t forget to activate your virtual environment every time you come back to the project.
* If you install a new package (e.g. `pip install somepackage`), update dependencies using:

```bash
pip-compile requirements.in
```

* Or if you're not using pip-tools:

```bash
pip freeze > requirements.txt
```

---

## 📁 Project Structure (example)

```
my-fastapi-app/
├── main.py
├── requirements.in
├── requirements.txt
├── venv/
└── README.md
```

---

## 💬 Need Help?

Check out the [FastAPI Docs](https://fastapi.tiangolo.com/) or feel free to ask!

---

Happy coding! 🐍🚀
