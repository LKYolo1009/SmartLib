#!/usr/bin/env python3
"""
LLM配置管理 (LLM Configuration Management)
管理Llama3.2和其他LLM相关的配置设置
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field
import json

class LLMConfig(BaseSettings):
    """LLM配置类"""
    
    # Ollama/Llama3.2 配置
    llm_endpoint: str = Field(
        default="http://localhost:11434",
        description="Ollama API端点地址"
    )
    
    llm_model_name: str = Field(
        default="llama3.2",
        description="使用的模型名称"
    )
    
    llm_timeout: int = Field(
        default=60,
        description="LLM请求超时时间(秒)"
    )
    
    # LLM功能开关
    enable_llm_nlu: bool = Field(
        default=True,
        description="启用LLM增强的NLU处理"
    )
    
    enable_llm_sql: bool = Field(
        default=True,
        description="启用LLM增强的SQL生成"
    )
    
    enable_fallback: bool = Field(
        default=True,
        description="启用降级到规则系统"
    )
    
    # 性能配置
    max_tokens_nlu: int = Field(
        default=300,
        description="NLU处理的最大token数"
    )
    
    max_tokens_sql: int = Field(
        default=800,
        description="SQL生成的最大token数"
    )
    
    temperature: float = Field(
        default=0.1,
        description="LLM生成的温度参数"
    )
    
    # 批量处理配置
    max_batch_size: int = Field(
        default=10,
        description="批量处理的最大查询数"
    )
    
    batch_timeout: int = Field(
        default=300,
        description="批量处理超时时间(秒)"
    )
    
    # 缓存配置
    enable_result_cache: bool = Field(
        default=True,
        description="启用查询结果缓存"
    )
    
    cache_ttl: int = Field(
        default=3600,
        description="缓存过期时间(秒)"
    )
    
    # 日志配置
    llm_log_level: str = Field(
        default="INFO",
        description="LLM组件日志级别"
    )
    
    log_llm_requests: bool = Field(
        default=False,
        description="是否记录LLM请求详情"
    )
    
    log_llm_responses: bool = Field(
        default=False,
        description="是否记录LLM响应详情"
    )

    class Config:
        env_file = ".env"
        env_prefix = "SMARTLIB_"
        case_sensitive = False

# 全局配置实例
llm_config = LLMConfig()

def get_llm_config() -> LLMConfig:
    """获取LLM配置"""
    return llm_config

def update_llm_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    """更新LLM配置"""
    global llm_config
    
    updated_fields = {}
    for key, value in updates.items():
        if hasattr(llm_config, key):
            setattr(llm_config, key, value)
            updated_fields[key] = value
    
    return updated_fields

def validate_llm_setup() -> Dict[str, Any]:
    """验证LLM设置"""
    import requests
    
    validation_result = {
        "status": "unknown",
        "checks": {},
        "recommendations": []
    }
    
    # 检查Ollama连接
    try:
        response = requests.get(f"{llm_config.llm_endpoint}/api/version", timeout=5)
        if response.status_code == 200:
            validation_result["checks"]["ollama_connection"] = "success"
            validation_result["checks"]["ollama_version"] = response.json()
        else:
            validation_result["checks"]["ollama_connection"] = "failed"
            validation_result["recommendations"].append("检查Ollama服务是否正常运行")
    except Exception as e:
        validation_result["checks"]["ollama_connection"] = f"error: {e}"
        validation_result["recommendations"].append("确保Ollama服务在指定端点运行")
    
    # 检查模型可用性
    try:
        response = requests.get(f"{llm_config.llm_endpoint}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            
            if llm_config.llm_model_name in model_names:
                validation_result["checks"]["model_available"] = "success"
            elif any(llm_config.llm_model_name in name for name in model_names):
                validation_result["checks"]["model_available"] = "partial_match"
                validation_result["recommendations"].append(f"找到相似模型: {model_names}")
            else:
                validation_result["checks"]["model_available"] = "not_found"
                validation_result["recommendations"].append(f"请安装模型: ollama pull {llm_config.llm_model_name}")
            
            validation_result["checks"]["available_models"] = model_names
        else:
            validation_result["checks"]["model_available"] = "api_error"
    except Exception as e:
        validation_result["checks"]["model_available"] = f"error: {e}"
    
    # 检查系统资源
    try:
        import psutil
        
        # 内存检查
        memory = psutil.virtual_memory()
        if memory.available > 4 * 1024 * 1024 * 1024:  # 4GB
            validation_result["checks"]["memory"] = "sufficient"
        else:
            validation_result["checks"]["memory"] = "limited"
            validation_result["recommendations"].append("建议至少4GB可用内存用于LLM处理")
        
        # CPU检查
        cpu_count = psutil.cpu_count()
        validation_result["checks"]["cpu_cores"] = cpu_count
        if cpu_count < 4:
            validation_result["recommendations"].append("建议至少4核CPU以获得更好的LLM性能")
            
    except ImportError:
        validation_result["checks"]["system_resources"] = "unable_to_check"
        validation_result["recommendations"].append("安装psutil以进行系统资源检查")
    
    # 总体状态判断
    if validation_result["checks"].get("ollama_connection") == "success" and \
       validation_result["checks"].get("model_available") == "success":
        validation_result["status"] = "ready"
    elif validation_result["checks"].get("ollama_connection") == "success":
        validation_result["status"] = "partial"
    else:
        validation_result["status"] = "not_ready"
    
    return validation_result

def get_recommended_settings() -> Dict[str, Any]:
    """获取推荐的配置设置"""
    return {
        "development": {
            "llm_timeout": 30,
            "temperature": 0.1,
            "max_tokens_nlu": 200,
            "max_tokens_sql": 500,
            "enable_fallback": True,
            "log_llm_requests": True
        },
        "production": {
            "llm_timeout": 60,
            "temperature": 0.05,
            "max_tokens_nlu": 300,
            "max_tokens_sql": 800,
            "enable_fallback": True,
            "enable_result_cache": True,
            "log_llm_requests": False,
            "log_llm_responses": False
        },
        "performance_optimized": {
            "llm_timeout": 45,
            "temperature": 0.1,
            "max_tokens_nlu": 250,
            "max_tokens_sql": 600,
            "max_batch_size": 5,
            "enable_result_cache": True,
            "cache_ttl": 7200
        }
    }

def create_example_env_file() -> str:
    """创建示例.env文件内容"""
    return """# SmartLib LLM配置示例
# 复制此文件为 .env 并根据您的环境调整配置

# === Ollama/Llama3.2 配置 ===
SMARTLIB_LLM_ENDPOINT=http://localhost:11434
SMARTLIB_LLM_MODEL_NAME=llama3.2
SMARTLIB_LLM_TIMEOUT=60

# === LLM功能开关 ===
SMARTLIB_ENABLE_LLM_NLU=true
SMARTLIB_ENABLE_LLM_SQL=true
SMARTLIB_ENABLE_FALLBACK=true

# === 性能配置 ===
SMARTLIB_MAX_TOKENS_NLU=300
SMARTLIB_MAX_TOKENS_SQL=800
SMARTLIB_TEMPERATURE=0.1

# === 批量处理配置 ===
SMARTLIB_MAX_BATCH_SIZE=10
SMARTLIB_BATCH_TIMEOUT=300

# === 缓存配置 ===
SMARTLIB_ENABLE_RESULT_CACHE=true
SMARTLIB_CACHE_TTL=3600

# === 日志配置 ===
SMARTLIB_LLM_LOG_LEVEL=INFO
SMARTLIB_LOG_LLM_REQUESTS=false
SMARTLIB_LOG_LLM_RESPONSES=false

# === 部署建议 ===
# 开发环境: 启用详细日志，较短超时
# 生产环境: 禁用详细日志，启用缓存
# 性能优化: 调整token限制和批量大小
"""
