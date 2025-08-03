# Smart Library Management System


## Tech Stack

- **Backend**: Python 3.13, FastAPI, PostgreSQL
- **AI/ML**: Llama3.2 (via Ollama), Local LLM Inference
- **Frontend**: Streamlit (Admin Dashboard)
- **Cache**: Redis (Conversation Context)
- **Deployment**: Docker Support

## Quick Start

### 1. Environment Preparation

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```
> Note: if we want to fully test the working code of the Streamlit dashboard in the virtual environment, we need to create the virtual environment in Python 3.12 because we are using **Streamlit.Page()** which is not supported by Python 3.13 yet.
To create the virtual environment in Python 3.12, firstly make sure your computer has Python 3.12 installed and then use the following command instead: 

```bash
python3.12 -m venv venv # indicating the version number is the only change from the previous instruction.
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. **Initialize the database** (optional, for first-time setup or reset):
```bash
# Complete reset (for first-time installation)
python scripts/db_init.py reset
```
- Clean data only: `python scripts/db_init.py clean`
- Initialize only: `python scripts/db_init.py init`

4. **Start the FastAPI backend service:**
```bash
uvicorn app.main:app --reload
```
The service will start at: http://localhost:8000

5. **Start the Streamlit dashboard:**
```bash
# Start the dashboard
streamlit run admin_dashboard/main.py
```


## API Documentation

After starting the service, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc




## Dashboard Screenshots

The Streamlit dashboard looks like this:

![Dashboard Example 1](assets/dashboard2.png)
![Dashboard Example 2](assets/dashboard1.png)

---
