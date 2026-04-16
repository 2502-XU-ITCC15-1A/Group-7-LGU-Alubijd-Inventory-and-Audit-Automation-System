# Alubijid Local Inventory & Audit System (ALIAS)


## Setup

### Create Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

- **Windows**:
  ```bash
  venv\Scripts\activate
  ```

- **Linux**:
  ```bash
  source venv/bin/activate
  ```

---

## Install Dependencies

Install Flask:

```bash
pip install flask
```

(Optional requirements) Save installed dependencies:

```bash
pip freeze > requirements.txt

pip install flask-mysqldb

pip show python-dotenv
```

python3 -m venv venv && source venv/bin/activate && pip install reportlab
---

## Run the Application

Start the Flask server:

```bash
python app.py
```