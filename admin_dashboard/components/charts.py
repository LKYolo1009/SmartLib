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
            return create_empty_chart("No borrowing trend data available<br><br>Please check data source connection or try again later")
        df = pd.DataFrame(data)
    else:
        df = data
    
    if df.empty or 'date' not in df.columns:
        return create_empty_chart("Invalid borrowing trend data format<br><br>Missing required date field")
    
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
            name='📚 Books Borrowed',
            line=dict(
                color=CHART_CONFIG['colors']['primary'],
                width=3,
                shape='spline'  # Smooth line
            ),
            mode='lines+markers',
            marker=dict(size=6, symbol='circle'),
            hovertemplate='<b>📚 Books Borrowed</b><br>' +
                         'Date: %{x|%Y-%m-%d}<br>' +
                         'Count: %{y} books<br>' +
                         '<extra></extra>',
            showlegend=True
        ))
    
    # Add returns line with enhanced tooltips
    if 'returns' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['returns'],
            name='📖 Books Returned',
            line=dict(
                color=CHART_CONFIG['colors']['secondary'],
                width=3,
                shape='spline'  # Smooth line
            ),
            mode='lines+markers',
            marker=dict(size=6, symbol='diamond'),
            hovertemplate='<b>📖 Books Returned</b><br>' +
                         'Date: %{x|%Y-%m-%d}<br>' +
                         'Count: %{y} books<br>' +
                         '<extra></extra>',
            showlegend=True
        ))
    
    # Calculate and add trend line for borrowings
    if 'borrowings' in df.columns and len(df) > 1:
        try:
            import numpy as np
            z = np.polyfit(range(len(df)), df['borrowings'], 1)
            trend_line = np.poly1d(z)(range(len(df)))
            
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=trend_line,
                name='📈 Borrowing Trend',
                line=dict(color='rgba(255,0,0,0.5)', width=2, dash='dot'),
                hovertemplate='<b>📈 Trend Line</b><br>' +
                             'Date: %{x|%Y-%m-%d}<br>' +
                             'Trend Value: %{y:.1f}<br>' +
                             '<extra></extra>',
                showlegend=True
            ))
        except ImportError:
            # Skip trend line if numpy is not available
            pass
    
    fig.update_layout(
        title=dict(
            text="📊 Book Borrowing Trend Analysis",
            font=dict(size=18, color="#2c3e50"),
            x=0.5,
            xanchor='center'
        ),
        template=CHART_CONFIG["template"],
        height=CHART_CONFIG["height"],
        xaxis=dict(
            title="Date",
            title_font=dict(size=14),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        yaxis=dict(
            title="Number of Books",
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
            return create_empty_chart("No category data available<br><br>Please check if book categories are properly configured", height=400)
        df = pd.DataFrame(data)
    else:
        df = data
    
    if df.empty:
        return create_empty_chart("No category data available<br><br>Please check if book categories are properly configured", height=400)
    
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
            missing_fields.append("Count field")
        if category_field is None:
            missing_fields.append("Category field")
        
        return create_empty_chart(
            f"Invalid category data format<br><br>Missing: {', '.join(missing_fields)}<br>" +
            f"Current fields: {', '.join(df.columns.tolist())}", 
            height=400
        )
    
    # Check if all values are zero
    if df[value_field].sum() == 0:
        return create_empty_chart(
            "All category book counts are 0<br><br>Please check if book data is correctly entered",
            height=400
        )
    
    # Filter out zero values
    df_filtered = df[df[value_field] > 0].copy()
    
    if df_filtered.empty:
        return create_empty_chart(
            "All category book counts are 0<br><br>Please check if book data is correctly entered",
            height=400
        )
    
    # Create enhanced pie chart
    fig = px.pie(
        df_filtered,
        values=value_field,
        names=category_field,
        title="📚 Book Category Distribution",
        template=CHART_CONFIG["template"],
        color_discrete_sequence=px.colors.qualitative.Set3,
        hover_data=[value_field]
    )
    
    # Update traces for better tooltips
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>' +
                     'Count: %{value} books<br>' +
                     'Percentage: %{percent}<br>' +
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
            return create_empty_chart("No popular books data available")
        df = pd.DataFrame(data)
    else:
        df = data
    
    if df.empty or 'title' not in df.columns or 'borrow_count' not in df.columns:
        return create_empty_chart("Invalid popular books data format<br><br>Missing title or borrow count field")
    
    # Limit to top 10 and sort by borrow_count
    df_sorted = df.nlargest(10, 'borrow_count')
    
    fig = px.bar(
        df_sorted,
        x="borrow_count",
        y="title",
        orientation='h',  # Horizontal bar chart for better title readability
        title="🔥 Popular Books Ranking",
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
        xaxis_title="Borrow Count",
        yaxis_title="Book Title",
        showlegend=False,
        margin=dict(l=150, r=60, t=80, b=60)
    )
    
    # Update traces for better tooltips
    fig.update_traces(
        hovertemplate='<b>%{y}</b><br>' +
                     'Borrow Count: %{x} times<br>' +
                     '<extra></extra>'
    )
    
    return fig

def create_student_activity_chart(data: Union[List[Dict], pd.DataFrame]) -> go.Figure:
    """Create student activity bar chart"""
    # Convert to DataFrame if needed
    if isinstance(data, list):
        if not data:
            return create_empty_chart("No student activity data available")
        df = pd.DataFrame(data)
    else:
        df = data
    
    if df.empty or 'student_name' not in df.columns or 'borrow_count' not in df.columns:
        return create_empty_chart("Invalid student activity data format")
    
    # Limit to top 10 and sort by borrow_count
    df_sorted = df.nlargest(10, 'borrow_count')
    
    fig = px.bar(
        df_sorted,
        x="borrow_count",
        y="student_name",
        orientation='h',  # Horizontal for better name readability
        title="👨‍🎓 Active Students Ranking",
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
        xaxis_title="Borrow Count",
        yaxis_title="Student Name",
        showlegend=False,
        margin=dict(l=100, r=60, t=80, b=60)
    )
    
    # Update traces for better tooltips
    fig.update_traces(
        hovertemplate='<b>%{y}</b><br>' +
                     'Borrow Count: %{x} times<br>' +
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

    # 强制转换 不然一直又格式问题
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

def create_utilization_chart(data: Union[List[Dict], pd.DataFrame, Dict]) -> go.Figure:
    """Create library utilization time series chart"""
    # Handle dictionary format input
    if isinstance(data, dict):
        if 'daily_utilization' in data:
            # Convert daily_utilization dictionary to DataFrame
            daily_data = []
            for date, count in data['daily_utilization'].items():
                daily_data.append({
                    'date': date,
                    'utilization_rate': count
                })
            df = pd.DataFrame(daily_data)
        else:
            return create_empty_chart("Invalid utilization data format: missing daily_utilization")
    # Handle list format input
    elif isinstance(data, list):
        if not data:
            return create_empty_chart("No utilization data available")
        df = pd.DataFrame(data)
    # Handle DataFrame format input
    elif isinstance(data, pd.DataFrame):
        df = data
    else:
        return create_empty_chart("Invalid utilization data format")
    
    if df.empty or 'date' not in df.columns or 'utilization_rate' not in df.columns:
        return create_empty_chart("Invalid utilization data format: missing required columns")
    
    # Convert date column to datetime
    if df['date'].dtype == 'object':
        df['date'] = pd.to_datetime(df['date'])
    
    # Create chart
    fig = px.line(
        df,
        x="date",
        y="utilization_rate",
        title="📈 Library Utilization Trend",
        template=CHART_CONFIG["template"],
        line_shape="spline"
    )
    
    # Add average line
    avg_utilization = df['utilization_rate'].mean()
    fig.add_hline(
        y=avg_utilization,
        line_dash="dash",
        line_color=CHART_CONFIG['colors']['primary'],
        annotation_text=f"Average: {avg_utilization:.1f}%",
        annotation_position="top right",
        annotation_font=dict(
            size=12,
            color="#2c3e50" 
        )
    )
    
    # Update layout
    fig.update_layout(
        height=CHART_CONFIG["height"],
        title=dict(
            font=dict(
                size=18,
                color="#2c3e50"  
            ),
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Date",
        yaxis_title="Utilization Rate (%)",
        showlegend=False,
        margin=dict(l=60, r=60, t=80, b=60),
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)" 
    )
    
    # Update traces
    fig.update_traces(
        line=dict(
            color=CHART_CONFIG['colors']['primary'],
            width=3
        ),
        hovertemplate='<b>Date: %{x|%Y-%m-%d}</b><br>' +
                     'Utilization Rate: %{y:.1f}%<br>' +
                     '<extra></extra>'
    )
    
    return fig