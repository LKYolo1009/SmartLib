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

# 安装依赖
pip install -r requirements.txt
```

### 2. LLM设置 (可选，推荐)

```bash
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下载Llama3.2模型
ollama pull llama3.2

# 启动Ollama服务
ollama serve
```

### 3. 数据库初始化

```bash
# 完整重置 (首次安装)
python scripts/db_init.py reset

# 仅清理数据
python scripts/db_init.py clean

# 仅初始化结构
python scripts/db_init.py init
```

### 4. 启动服务

```bash
# 启动FastAPI后端
uvicorn app.main:app --reload --port 8000

# 启动Streamlit管理看板
streamlit run admin_dashboard/main.py
```

### 5. 验证服务

- **API文档**: http://localhost:8000/docs
- **管理看板**: http://localhost:8501
- **LLM状态**: http://localhost:8000/api/v1/llm-query/llm-status

## 🧠 智能查询系统

### 双模式运行

| 模式 | 特点 | 响应时间 | 适用场景 |
|------|------|----------|----------|
| **LLM增强** | 智能理解、复杂查询 | 2-8s | 复杂语义、模糊表达 |
| **规则基础** | 快速匹配、稳定可靠 | 100-300ms | 标准查询、高频操作 |

### 支持的查询类型

- **图书查询**: "查找《三体》"、"鲁迅的作品有哪些？"
- **库存管理**: "查询图书库存"、"哪些书可以借阅？"
- **借阅记录**: "张三的借阅记录"、"最近30天的借阅情况"
- **统计分析**: "最热门的10本书"、"借阅量最高的图书"
- **逾期管理**: "有哪些逾期的书？"、"超期未还的书籍"

### 复杂查询示例

```bash
# LLM增强查询
curl -X POST "http://localhost:8000/api/v1/llm-query/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "帮我找找适合计算机专业学生的Python编程书籍",
    "use_llm": true
  }'

# 复杂分析查询
curl -X POST "http://localhost:8000/api/v1/llm-query/complex-query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "统计本月借阅量最高的科技类图书，显示作者和库存状态"
  }'
```

## 📊 管理员看板

### 核心功能

- **实时KPI监控**: 图书总量、借阅量、逾期警报、活跃用户
- **趋势分析**: 借阅趋势、类别分布、热门排行
- **QR码标签生成**: 批量生成图书标签，支持PDF导出
- **交互式图表**: 可缩放、筛选、排序的数据可视化

### 快速访问

```bash
# 启动看板
streamlit run admin_dashboard/main.py

# 访问地址
http://localhost:8501
```

## 🔧 配置说明

### 环境变量 (.env)

```env
# LLM配置
SMARTLIB_LLM_ENDPOINT=http://localhost:11434
SMARTLIB_LLM_MODEL_NAME=llama3.2
SMARTLIB_LLM_TIMEOUT=60

# 功能开关
SMARTLIB_ENABLE_LLM_NLU=true
SMARTLIB_ENABLE_LLM_SQL=true
SMARTLIB_ENABLE_FALLBACK=true

# Redis配置 (可选)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 🧪 测试和演示

### 快速演示

```bash
# NLU功能演示
python demo_nlu.py

# 完整查询流程演示
python demo_query_generator.py

# 多轮对话演示
python demo_dialog_context.py

# LLM集成演示
python demo_llm_integration.py
```

### 运行测试

```bash
# 单元测试
python test_nlu.py
python test_query_generator.py
python test_dialog_context.py

# 端点测试
python test_endpoints.py
```

## 📈 性能指标

- **规则系统**: 100-300ms响应时间
- **LLM增强**: 2-8s (首次) → 1-3s (后续)
- **自动降级**: 500ms内完成切换
- **并发支持**: 支持多用户同时查询

## 🚨 故障排除

### 常见问题

1. **LLM服务不可用**
   ```bash
   ollama ps  # 检查状态
   ollama serve  # 重启服务
   ```

2. **响应时间过长**
   - 使用量化模型: `ollama pull llama3.2:8b-instruct-q4_0`
   - 启用缓存: `SMARTLIB_ENABLE_RESULT_CACHE=true`

3. **Redis连接失败**
   - 系统自动降级到内存存储
   - 不影响基本功能


## 🖼️ 系统截图

![Dashboard Example 1](assets/dashboard2.png)
![Dashboard Example 2](assets/dashboard1.png)

---
