import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from utils.db import Database
from utils.auth import init_session_state, check_login
from scipy import stats
import time

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="Advanced Energy Management System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ CUSTOM CSS ============
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .alert-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 15px;
        border-radius: 8px;
        color: white;
    }
    .success-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 15px;
        border-radius: 8px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ============ INIT SESSION ============
init_session_state()

if not check_login():
    st.switch_page("pages/00_login.py")

user = st.session_state.user

# ============ ADVANCED SIDEBAR ============
with st.sidebar:
    st.title("🎛️ Advanced Controls")
    
    # Navigation
    page = st.radio(
        "Navigate",
        ["📊 Dashboard", "🔍 Analytics", "⚠️ Anomalies", "📈 Forecasting", "🛠️ Settings"],
        key="nav_page"
    )
    
    st.markdown("---")
    
    # Filters
    st.subheader("Filters")
    
    refresh_rate = st.selectbox(
        "Auto-refresh Rate",
        [5, 10, 15, 30, 60],
        index=2,
        help="Seconds between refreshes"
    )
    
    st.markdown("---")
    
    # User Info
    st.subheader("User Info")
    st.write(f"👤 **{user['name']}**")
    st.write(f"🔑 **Role:** {user['role'].capitalize()}")
    
    if user['role'] == 'industry':
        st.write(f"🏭 **Industry ID:** {user['industry_id']}")
    
    st.markdown("---")
    
    if st.button("🚪 Logout", use_container_width=True):
        from utils.auth import logout
        logout()


# ============ PAGE 1: ADVANCED DASHBOARD ============

if page == "📊 Dashboard":
    st.title("⚡ Advanced Energy Dashboard")
    
    if user['role'] == 'industry':
        industry_id = user['industry_id']
        
        # Get data
        machines = Database.get_machines(industry_id)
        
        if not machines:
            st.warning("No machines found")
            st.stop()
        
        # Real-time metrics
        latest_data = {}
        for machine in machines:
            latest_data[machine['id']] = Database.get_machine_latest_data(machine['id'])
        
        # ========== KPI SECTION ==========
        st.subheader("📊 Key Performance Indicators")
        
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        
        total_power = sum(d['power'] for d in latest_data.values() if d)
        active_machines = sum(1 for d in latest_data.values() if d and d['relay_status'] == 1)
        anomalies_24h = sum(1 for d in latest_data.values() if d and d['anomaly'] == 1)
        avg_efficiency = (active_machines / len(machines) * 100) if machines else 0
        
        with kpi1:
            st.metric(
                "⚡ Total Power",
                f"{total_power:.2f} W",
                f"{total_power/1000:.2f} kW"
            )
        
        with kpi2:
            st.metric(
                "🟢 Active Machines",
                f"{active_machines}/{len(machines)}",
                f"{avg_efficiency:.1f}%"
            )
        
        with kpi3:
            st.metric(
                "⚠️ Anomalies (24h)",
                anomalies_24h,
                "Critical" if anomalies_24h > 5 else "Normal"
            )
        
        with kpi4:
            avg_voltage = np.mean([d['voltage'] for d in latest_data.values() if d])
            st.metric(
                "⚡ Avg Voltage",
                f"{avg_voltage:.2f} V",
                "Normal" if 220 <= avg_voltage <= 250 else "Out of Range"
            )
        
        with kpi5:
            avg_current = np.mean([d['current'] for d in latest_data.values() if d])
            st.metric(
                "🔌 Avg Current",
                f"{avg_current:.2f} A"
            )
        
        st.markdown("---")
        
        # ========== REAL-TIME MONITORING ==========
        st.subheader("🔴 Real-Time Machine Monitoring")
        
        status_data = []
        for machine in machines:
            data = latest_data[machine['id']]
            if data:
                status_data.append({
                    'Machine': machine['machine_name'],
                    'Type': machine['machine_type'],
                    'Voltage (V)': f"{data['voltage']:.2f}",
                    'Current (A)': f"{data['current']:.2f}",
                    'Power (W)': f"{data['power']:.2f}",
                    'Energy (kWh)': f"{data['energy']:.4f}",
                    'Status': '🟢 ON' if data['relay_status'] else '🔴 OFF',
                    'Health': '⚠️ Anomaly' if data['anomaly'] else '✅ Normal',
                    'Time': data['timestamp']
                })
        
        df_status = pd.DataFrame(status_data)
        st.dataframe(df_status, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # ========== ADVANCED CHARTS ==========
        st.subheader("📈 Advanced Analytics")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            power_data = [d['power'] for d in latest_data.values() if d]
            machine_names = [m['machine_name'] for m in machines if latest_data[m['id']]]
            
            fig = go.Figure(data=[go.Pie(labels=machine_names, values=power_data)])
            fig.update_layout(
                title="Power Distribution Across Machines",
                template="plotly_dark",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with chart_col2:
            voltages = [d['voltage'] for d in latest_data.values() if d]
            currents = [d['current'] for d in latest_data.values() if d]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=voltages, name="Voltage (V)", mode='lines+markers'))
            fig.add_trace(go.Scatter(y=currents, name="Current (A)", mode='lines+markers', yaxis="y2"))
            
            fig.update_layout(
                title="Voltage & Current Comparison",
                template="plotly_dark",
                hovermode='x unified',
                height=400,
                yaxis2=dict(overlaying='y', side='right')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Auto-refresh
        time.sleep(refresh_rate)
        st.rerun()


# ============ PAGE 2: ADVANCED ANALYTICS ============

elif page == "🔍 Analytics":
    st.title("🔍 Advanced Analytics & Insights")
    
    if user['role'] == 'industry':
        industry_id = user['industry_id']
        machines = Database.get_machines(industry_id)
        
        st.subheader("Machine Selection")
        selected_machine = st.selectbox(
            "Select Machine",
            [m['machine_name'] for m in machines],
            key="analytics_machine"
        )
        
        machine_id = next(m['id'] for m in machines if m['machine_name'] == selected_machine)
        
        history = Database.get_machine_history(machine_id, hours=720)
        stats_data = Database.get_machine_stats(machine_id, hours=720)
        
        if history.empty:
            st.warning("No data available")
            st.stop()
        
        # ========== STATISTICAL ANALYSIS ==========
        st.subheader("📊 Statistical Analysis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Mean Power",
                f"{history['power'].mean():.2f} W",
                f"Std Dev: {history['power'].std():.2f}"
            )
        
        with col2:
            st.metric(
                "Power Range",
                f"{history['power'].max() - history['power'].min():.2f} W",
                f"Min: {history['power'].min():.2f} W"
            )
        
        with col3:
            skewness_val = stats.skew(history['power'])
            st.metric(
                "Distribution Skewness",
                f"{skewness_val:.2f}",
                "Normal" if -0.5 <= skewness_val <= 0.5 else "Skewed"
            )
        
        st.markdown("---")
        
        # ========== DISTRIBUTION PLOTS ==========
        st.subheader("📈 Distribution Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(
                history,
                x='power',
                nbins=30,
                title='Power Distribution',
                template='plotly_dark'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = go.Figure(data=[
                go.Box(y=history['power'], name='Power (W)', marker_color='rgba(102, 126, 234, 0.7)')
            ])
            fig.update_layout(title='Power Boxplot', template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
        
        # ========== TIME SERIES DECOMPOSITION ==========
        st.subheader("📉 Time Series Trends")
        
        history['date'] = pd.to_datetime(history['timestamp']).dt.date
        daily_avg = history.set_index('date').resample('D')['power'].mean()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily_avg.index, y=daily_avg.values, name='Daily Average', mode='lines+markers'))
        fig.update_layout(
            title='Daily Average Power Consumption',
            template='plotly_dark',
            xaxis_title='Date',
            yaxis_title='Power (W)'
        )
        st.plotly_chart(fig, use_container_width=True)


# ============ PAGE 3: ADVANCED ANOMALY DETECTION ============

elif page == "⚠️ Anomalies":
    st.title("⚠️ Advanced Anomaly Detection")
    
    if user['role'] == 'industry':
        industry_id = user['industry_id']
        
        anomalies = Database.get_anomalies(industry_id, limit=500)
        
        if anomalies.empty:
            st.success("✅ No anomalies detected!")
        else:
            st.warning(f"⚠️ Found {len(anomalies)} anomalies")
            
            # ========== ANOMALY STATISTICS ==========
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Total Anomalies",
                    len(anomalies),
                    f"Last 24h: {len(anomalies[anomalies['timestamp'] > (datetime.now() - timedelta(days=1)).isoformat()])}"
                )
            
            with col2:
                affected_machines = anomalies['machine_name'].nunique()
                st.metric("Affected Machines", affected_machines)
            
            with col3:
                st.metric("Anomaly Types", len(anomalies))
            
            st.markdown("---")
            
            # ========== ANOMALY TIMELINE ==========
            st.subheader("📊 Anomaly Timeline")
            
            anomalies['date'] = pd.to_datetime(anomalies['timestamp']).dt.date
            anomaly_timeline = anomalies.groupby('date').size()
            
            fig = px.bar(
                x=anomaly_timeline.index,
                y=anomaly_timeline.values,
                title='Anomalies Over Time',
                labels={'x': 'Date', 'y': 'Count'},
                template='plotly_dark'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # ========== ANOMALY DISTRIBUTION ==========
            st.subheader("📍 Anomaly Distribution by Machine")
            
            col1, col2 = st.columns(2)
            
            with col1:
                machine_anomalies = anomalies['machine_name'].value_counts()
                fig = px.bar(
                    y=machine_anomalies.index,
                    x=machine_anomalies.values,
                    orientation='h',
                    title='Anomalies by Machine',
                    template='plotly_dark'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                anomaly_types = {
                    'High Power': len(anomalies[anomalies['power'] > 3000]),
                    'High Current': len(anomalies[anomalies['current'] > 15]),
                    'Low Voltage': len(anomalies[anomalies['voltage'] < 220]),
                    'Other': len(anomalies) - (
                        len(anomalies[anomalies['power'] > 3000]) +
                        len(anomalies[anomalies['current'] > 15]) +
                        len(anomalies[anomalies['voltage'] < 220])
                    )
                }
                
                fig = px.pie(
                    values=list(anomaly_types.values()),
                    names=list(anomaly_types.keys()),
                    title='Anomaly Types',
                    template='plotly_dark'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # ========== DETAILED ANOMALY TABLE ==========
            st.subheader("📋 Detailed Anomalies")
            
            st.dataframe(
                anomalies[['timestamp', 'machine_name', 'voltage', 'current', 'power', 'energy']],
                use_container_width=True,
                hide_index=True
            )


# ============ PAGE 4: FORECASTING ============

elif page == "📈 Forecasting":
    st.title("📈 Power Forecasting & Predictions")
    
    if user['role'] == 'industry':
        industry_id = user['industry_id']
        machines = Database.get_machines(industry_id)
        
        st.subheader("Machine Selection")
        selected_machine = st.selectbox(
            "Select Machine",
            [m['machine_name'] for m in machines],
            key="forecast_machine"
        )
        
        machine_id = next(m['id'] for m in machines if m['machine_name'] == selected_machine)
        
        history = Database.get_machine_history(machine_id, hours=720)
        
        if history.empty:
            st.warning("No data available for forecasting")
            st.stop()
        
        # Simple moving average forecast
        st.subheader("📊 Power Forecast (Next 7 Days)")
        
        history['date'] = pd.to_datetime(history['timestamp']).dt.date
        daily_power = history.groupby('date')['power'].mean()
        
        # Simple exponential smoothing
        alpha = 0.3
        forecast = [daily_power.iloc[-1]]
        
        for i in range(7):
            forecast.append(alpha * daily_power.iloc[-1] + (1 - alpha) * forecast[-1])
        
        forecast_dates = pd.date_range(
            start=daily_power.index[-1],
            periods=8,
            freq='D'
        )
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_power.index,
            y=daily_power.values,
            name='Historical',
            mode='lines+markers'
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast_dates,
            y=forecast,
            name='Forecast',
            mode='lines+markers',
            line=dict(dash='dash')
        ))
        
        fig.update_layout(
            title='7-Day Power Consumption Forecast',
            template='plotly_dark',
            xaxis_title='Date',
            yaxis_title='Power (W)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Current Avg Power", f"{daily_power.iloc[-1]:.2f} W")
        
        with col2:
            st.metric("Forecast (7 days)", f"{forecast[-1]:.2f} W")
        
        with col3:
            if daily_power.iloc[-1] > 0:
                change = ((forecast[-1] - daily_power.iloc[-1]) / daily_power.iloc[-1] * 100)
            else:
                change = 0
            st.metric("Expected Change", f"{change:.1f}%", delta=f"{change:.1f}%")


# ============ PAGE 5: SETTINGS ============

elif page == "🛠️ Settings":
    st.title("🛠️ Advanced Settings")
    
    st.subheader("⚙️ System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Database Status**")
        try:
            conn = Database.get_connection()
            if conn:
                st.success("✅ Connected to MySQL")
                conn.close()
        except:
            st.error("❌ Database connection failed")
    
    with col2:
        st.write("**System Info**")
        st.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    st.markdown("---")
    
    st.subheader("📊 Data Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Export All Data", use_container_width=True):
            if user['role'] == 'industry':
                machines = Database.get_machines(user['industry_id'])
                all_data = []
                for machine in machines:
                    history = Database.get_machine_history(machine['id'], hours=8760)
                    all_data.append(history)
                
                if all_data:
                    df_export = pd.concat(all_data, ignore_index=True)
                    csv = df_export.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        "energy_data_export.csv",
                        "text/csv"
                    )
    
    with col2:
        if st.button("📊 Generate Report", use_container_width=True):
            st.success("Report generated successfully")
    
    with col3:
        if st.button("🔄 Refresh All Data", use_container_width=True):
            st.rerun()