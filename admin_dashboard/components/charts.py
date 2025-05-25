# components/charts.py
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Union
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CHART_CONFIG, DASHBOARD_CONFIG

def create_empty_chart(message: str = "No data available", height: int = None) -> go.Figure:
    """Create an empty chart with a message"""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="#666666"),
        align="center"
    )
    fig.update_layout(
        height=height or CHART_CONFIG["height"],
        template=CHART_CONFIG["template"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=20)
    )
    return fig

def create_loading_chart(message: str = "Loading data...") -> go.Figure:
    """Create a loading chart with spinner animation"""
    fig = go.Figure()
    fig.add_annotation(
        text=f"🔄 {message}",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=18, color="#667eea")
    )
    fig.update_layout(
        height=CHART_CONFIG["height"],
        template=CHART_CONFIG["template"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def create_kpi_card(title: str, value: float, change: float = None, color: str = None) -> go.Figure:
    """Create a KPI card with optional change indicator"""
    fig = go.Figure()
    
    # Add value text
    fig.add_annotation(
        text=f"{value:,.0f}",
        x=0.5,
        y=0.6,
        showarrow=False,
        font=dict(size=24, color=color or DASHBOARD_CONFIG["theme"]["primary_color"])
    )
    
    # Add title
    fig.add_annotation(
        text=title,
        x=0.5,
        y=0.3,
        showarrow=False,
        font=dict(size=14)
    )
    
    # Add change indicator if provided
    if change is not None:
        change_color = DASHBOARD_CONFIG["theme"]["success_color"] if change >= 0 else DASHBOARD_CONFIG["theme"]["warning_color"]
        change_text = f"{'+' if change > 0 else ''}{change:.1f}%"
        fig.add_annotation(
            text=change_text,
            x=0.5,
            y=0.1,
            showarrow=False,
            font=dict(size=12, color=change_color)
        )
    
    fig.update_layout(
        height=150,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    
    return fig

def create_borrowing_trend_chart(data: Union[List[Dict], pd.DataFrame]) -> go.Figure:
    """Create enhanced borrowing trends line chart with tooltips and interactions"""
    # Convert to DataFrame if needed
    if isinstance(data, list):
        if not data:
            return create_empty_chart("暂无借阅趋势数据<br><br>请检查数据源连接或稍后重试")
        df = pd.DataFrame(data)
    else:
        df = data
    
    if df.empty or 'date' not in df.columns:
        return create_empty_chart("借阅趋势数据格式错误<br><br>缺少必要的日期字段")
    
    # Convert date column to datetime if needed
    if df['date'].dtype == 'object':
        df['date'] = pd.to_datetime(df['date'])
    
    # Create figure with enhanced styling
    fig = go.Figure()
    
    # Add borrowings line with enhanced tooltips
    if 'borrowings' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['borrowings'],
            name='📚 借出图书',
            line=dict(
                color=CHART_CONFIG['colors']['primary'],
                width=3,
                shape='spline'  # Smooth line
            ),
            mode='lines+markers',
            marker=dict(size=6, symbol='circle'),
            hovertemplate='<b>📚 借出图书</b><br>' +
                         '日期: %{x|%Y-%m-%d}<br>' +
                         '数量: %{y} 本<br>' +
                         '<extra></extra>',
            showlegend=True
        ))
    
    # Add returns line with enhanced tooltips
    if 'returns' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['returns'],
            name='📖 归还图书',
            line=dict(
                color=CHART_CONFIG['colors']['secondary'],
                width=3,
                shape='spline'  # Smooth line
            ),
            mode='lines+markers',
            marker=dict(size=6, symbol='diamond'),
            hovertemplate='<b>📖 归还图书</b><br>' +
                         '日期: %{x|%Y-%m-%d}<br>' +
                         '数量: %{y} 本<br>' +
                         '<extra></extra>',
            showlegend=True
        ))
    
    # Calculate and add trend line for borrowings
    if 'borrowings' in df.columns and len(df) > 1:
        z = np.polyfit(range(len(df)), df['borrowings'], 1)
        trend_line = np.poly1d(z)(range(len(df)))
        
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=trend_line,
            name='📈 借阅趋势',
            line=dict(color='rgba(255,0,0,0.5)', width=2, dash='dot'),
            hovertemplate='<b>📈 趋势线</b><br>' +
                         '日期: %{x|%Y-%m-%d}<br>' +
                         '趋势值: %{y:.1f}<br>' +
                         '<extra></extra>',
            showlegend=True
        ))
    
    fig.update_layout(
        title=dict(
            text="📊 图书借阅趋势分析",
            font=dict(size=18, color="#2c3e50"),
            x=0.5,
            xanchor='center'
        ),
        template=CHART_CONFIG["template"],
        height=CHART_CONFIG["height"],
        xaxis=dict(
            title="日期",
            title_font=dict(size=14),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        yaxis=dict(
            title="图书数量",
            title_font=dict(size=14),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(128,128,128,0.5)",
            borderwidth=1
        ),
        hovermode='x unified',  # Show all values at the same x-coordinate
        margin=dict(l=60, r=60, t=80, b=60)
    )
    
    return fig

def create_category_pie_chart(data: Union[List[Dict], pd.DataFrame]) -> go.Figure:
    """Create enhanced category distribution pie chart with better data handling"""
    # Convert to DataFrame if needed
    if isinstance(data, list):
        if not data:
            return create_empty_chart("暂无分类数据<br><br>请检查图书分类信息是否已正确配置", height=400)
        df = pd.DataFrame(data)
    else:
        df = data
    
    if df.empty:
        return create_empty_chart("暂无分类数据<br><br>请检查图书分类信息是否已正确配置", height=400)
    
    print(f"Category data received: {df.head()}")  # Debug info
    print(f"Columns: {df.columns.tolist()}")  # Debug info
    
    # Auto-detect value field with more options
    value_field = None
    possible_fields = ["total_books", "count", "borrowed_books", "available_books", "book_count", "num_books"]
    
    for candidate in possible_fields:
        if candidate in df.columns:
            value_field = candidate
            break
    
    # Check for category field
    category_field = None
    possible_category_fields = ["category", "category_name", "name", "type"]
    
    for candidate in possible_category_fields:
        if candidate in df.columns:
            category_field = candidate
            break
    
    if value_field is None or category_field is None:
        missing_fields = []
        if value_field is None:
            missing_fields.append("数量字段")
        if category_field is None:
            missing_fields.append("分类字段")
        
        return create_empty_chart(
            f"分类数据格式错误<br><br>缺少: {', '.join(missing_fields)}<br>" +
            f"当前字段: {', '.join(df.columns.tolist())}", 
            height=400
        )
    
    # Check if all values are zero
    if df[value_field].sum() == 0:
        return create_empty_chart(
            "所有分类图书数量为 0<br><br>请检查图书数据是否正确录入",
            height=400
        )
    
    # Filter out zero values
    df_filtered = df[df[value_field] > 0].copy()
    
    if df_filtered.empty:
        return create_empty_chart(
            "所有分类图书数量为 0<br><br>请检查图书数据是否正确录入",
            height=400
        )
    
    # Create enhanced pie chart
    fig = px.pie(
        df_filtered,
        values=value_field,
        names=category_field,
        title="📚 图书分类分布",
        template=CHART_CONFIG["template"],
        color_discrete_sequence=px.colors.qualitative.Set3,
        hover_data=[value_field]
    )
    
    # Update traces for better tooltips
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>' +
                     '数量: %{value} 本<br>' +
                     '占比: %{percent}<br>' +
                     '<extra></extra>',
        textfont_size=12,
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )

    fig.update_layout(
        height=400,
        title=dict(
            font=dict(size=18, color="#2c3e50"),
            x=0.5,
            xanchor='center'
        ),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(128,128,128,0.5)",
            borderwidth=1
        ),
        margin=dict(l=20, r=120, t=80, b=20)
    )
    
    return fig

def create_popular_books_chart(data: Union[List[Dict], pd.DataFrame]) -> go.Figure:
    """Create popular books bar chart"""
    # Convert to DataFrame if needed
    if isinstance(data, list):
        if not data:
            return create_empty_chart("暂无热门图书数据")
        df = pd.DataFrame(data)
    else:
        df = data
    
    if df.empty or 'title' not in df.columns or 'borrow_count' not in df.columns:
        return create_empty_chart("热门图书数据格式错误<br><br>缺少标题或借阅次数字段")
    
    # Limit to top 10 and sort by borrow_count
    df_sorted = df.nlargest(10, 'borrow_count')
    
    fig = px.bar(
        df_sorted,
        x="borrow_count",
        y="title",
        orientation='h',  # Horizontal bar chart for better title readability
        title="🔥 热门图书排行榜",
        template=CHART_CONFIG["template"],
        color="borrow_count",
        color_continuous_scale="viridis"
    )
    
    fig.update_layout(
        height=CHART_CONFIG["height"],
        title=dict(
            font=dict(size=18, color="#2c3e50"),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="借阅次数",
        yaxis_title="图书标题",
        showlegend=False,
        margin=dict(l=150, r=60, t=80, b=60)
    )
    
    # Update traces for better tooltips
    fig.update_traces(
        hovertemplate='<b>%{y}</b><br>' +
                     '借阅次数: %{x} 次<br>' +
                     '<extra></extra>'
    )
    
    return fig

def create_student_activity_chart(data: Union[List[Dict], pd.DataFrame]) -> go.Figure:
    """Create student activity bar chart"""
    # Convert to DataFrame if needed
    if isinstance(data, list):
        if not data:
            return create_empty_chart("暂无学生活动数据")
        df = pd.DataFrame(data)
    else:
        df = data
    
    if df.empty or 'student_name' not in df.columns or 'borrow_count' not in df.columns:
        return create_empty_chart("学生活动数据格式错误")
    
    # Limit to top 10 and sort by borrow_count
    df_sorted = df.nlargest(10, 'borrow_count')
    
    fig = px.bar(
        df_sorted,
        x="borrow_count",
        y="student_name",
        orientation='h',  # Horizontal for better name readability
        title="👨‍🎓 活跃学生排行榜",
        template=CHART_CONFIG["template"],
        color="borrow_count",
        color_continuous_scale="plasma"
    )
    
    fig.update_layout(
        height=CHART_CONFIG["height"],
        title=dict(
            font=dict(size=18, color="#2c3e50"),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="借阅次数",
        yaxis_title="学生姓名",
        showlegend=False,
        margin=dict(l=100, r=60, t=80, b=60)
    )
    
    # Update traces for better tooltips
    fig.update_traces(
        hovertemplate='<b>%{y}</b><br>' +
                     '借阅次数: %{x} 次<br>' +
                     '<extra></extra>'
    )
    
    return fig

def create_overdue_analysis_chart(data: Union[List[Dict], pd.DataFrame]) -> go.Figure:
    """Create overdue analysis chart from overdue books list"""
    # Convert to DataFrame if needed
    if isinstance(data, list):
        if not data:
            return create_empty_chart("No overdue data available")
        df = pd.DataFrame(data)
    else:
        df = data

    if df.empty or 'days_overdue' not in df.columns:
        return create_empty_chart("Overdue data format error")

    # 强制转换为数值型，无法转换的设为NaN
    df['days_overdue'] = pd.to_numeric(df['days_overdue'], errors='coerce')
    df = df.dropna(subset=['days_overdue'])

    if df.empty:
        return create_empty_chart("No valid overdue data")

    # 统计逾期天数区间
    bins = [0, 3, 7, 14, 9999]
    labels = ["1-3 days", "4-7 days", "8-14 days", "15+ days"]
    df['overdue_range'] = pd.cut(df['days_overdue'], bins=bins, labels=labels, right=True)
    count_by_range = df['overdue_range'].value_counts().sort_index()
    chart_df = pd.DataFrame({
        "days_overdue": count_by_range.index,
        "count": count_by_range.values
    })

    fig = px.bar(
        chart_df,
        x="days_overdue",
        y="count",
        title="⚠️ Overdue Books Analysis",
        template=CHART_CONFIG["template"],
        color="count",
        color_continuous_scale="reds"
    )

    fig.update_layout(
        height=CHART_CONFIG["height"],
        title=dict(
            font=dict(size=18, color="#2c3e50"),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Overdue Days",
        yaxis_title="Number of Books",
        showlegend=False,
        margin=dict(l=60, r=60, t=80, b=60)
    )

    return fig

def create_utilization_chart(data: Union[List[Dict], pd.DataFrame]) -> go.Figure:
    """Create library utilization time series chart"""
    # Convert to DataFrame if needed
    if isinstance(data, list):
        if not data:
            return create_empty_chart("暂无利用率数据")
        df = pd.DataFrame(data)
    else:
        df = data
    
    if df.empty or 'date' not in df.columns or 'utilization_rate' not in df.columns:
        return create_empty_chart("利用率数据格式错误")
    
    # Convert date column to datetime if it's not already
    if df['date'].dtype == 'object':
        df['date'] = pd.to_datetime(df['date'])
    
    fig = px.line(
        df,
        x="date",
        y="utilization_rate",
        title="📊 图书馆利用率趋势",
        template=CHART_CONFIG["template"],
        line_shape="spline"  # Smooth line
    )
    
    # Add average line
    avg_utilization = df['utilization_rate'].mean()
    fig.add_hline(
        y=avg_utilization,
        line_dash="dash",
        line_color="red",
        annotation_text=f"平均利用率: {avg_utilization:.1f}%",
        annotation_position="top right"
    )
    
    fig.update_layout(
        height=CHART_CONFIG["height"],
        title=dict(
            font=dict(size=18, color="#2c3e50"),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="日期",
        yaxis_title="利用率 (%)",
        showlegend=False,
        margin=dict(l=60, r=60, t=80, b=60)
    )
    
    return fig

# Import numpy for trend calculation
try:
    import numpy as np
except ImportError:
    # Fallback if numpy is not available
    def create_borrowing_trend_chart(data: Union[List[Dict], pd.DataFrame]) -> go.Figure:
        """Fallback version without trend line"""
        # ... (same as above but without trend line calculation)
        pass