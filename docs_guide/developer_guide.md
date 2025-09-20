# Guide to run this documentation locally

## 1. Create a Virtual Environment

Run the following command in your project directory:

```bash
python -m venv venv
```

This will create a folder named **`venv`** containing the virtual environment.

---

## 2. Activate the Virtual Environment

To start using the virtual environment:

* **On macOS/Linux:**

  ```bash
  source venv/bin/activate
  ```

* **On Windows (Git Bash):**

  ```bash
  source venv/Scripts/activate
  ```

---

## 3. Install Dependencies

If you have a `requirements.txt` file in your project:

```bash
pip install -r requirements.txt
```

---

## 4. Serve the Mkdocs locally

```
mkdocs serve
```
This will start the mkdocs server

## 5 ( Optional ). Deactivate the Virtual Environment

When finished working, you can exit the environment with:

```bash
deactivate
```