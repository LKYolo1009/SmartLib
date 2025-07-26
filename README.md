# Smart Library Management System

一个集成了LLM增强功能的智能图书馆管理系统，支持自然语言查询、智能分析和可视化管理。

## 🚀 核心特性

- **🤖 LLM增强查询**: 集成本地Llama3.2模型，提供智能自然语言理解
- **📊 实时数据可视化**: 基于Streamlit的管理员看板
- **💬 多轮对话支持**: Redis驱动的上下文管理和智能补全
- **🌐 双语支持**: 中英文自然语言查询
- **🛡️ 自动降级**: LLM不可用时自动切换到规则系统

## Tech Stack

- **Backend**: Python 3.13, FastAPI, PostgreSQL
- **AI/ML**: Llama3.2 (via Ollama), 本地LLM推理
- **Frontend**: Streamlit (Admin Dashboard)
- **Cache**: Redis (对话上下文)
- **Deployment**: Docker支持

## Quick Start

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```
> Note: if we want to fully test the working code of streamlit dashboard in the virtual environment, we need to create the virtual environment in python 3.12 because we are using **streamlit.Page()** which is not supported by python 3.13 yet.
To create the virtual environment in python 3.12, firstly make sure your computer has python 3.12 installed and then use the following command instead: 

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
# 完整重置 (首次安装)
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
# 启动看板
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
