import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from utils.db import Database
from utils.auth import check_login, get_current_user
from utils.charts import plot_power_comparison
import time

if not check_login():
    st.switch_page("pages/01_login.py")

user = get_current_user()

st.set_page_config(
    page_title="Advanced Energy Management System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ SIDEBAR ============
with st.sidebar:
    st.title("🎛️ Advanced Controls")
    
    # Navigation
    if user['role'] == 'admin':
        page = st.radio(
            "Navigate",
            ["👨‍💼 All Industries", "📊 Industry Dashboard", "🔍 Analytics", "⚠️ All Anomalies", "📈 Forecasting", "🛠️ Settings"],
            key="nav_page"
        )
    else:
        page = st.radio(
            "Navigate",
            ["📊 Dashboard", "🔍 Analytics", "⚠️ Anomalies", "📈 Forecasting", "🛠️ Settings"],
            key="nav_page"
        )
    
    st.markdown("---")
    
    refresh_rate = st.selectbox(
        "Auto-refresh Rate",
        [5, 10, 15, 30, 60],
        index=2,
        help="Seconds between refreshes"
    )
    
    st.markdown("---")
    
    st.subheader("User Info")
    st.write(f"👤 **{user['name']}**")
    st.write(f"🔑 **Role:** {user['role'].capitalize()}")
    
    if user['role'] == 'industry':
        st.write(f"🏭 **Industry ID:** {user['industry_id']}")
    
    st.markdown("---")
    
    if st.button("🚪 Logout", use_container_width=True):
        from utils.auth import logout
        logout()


# ============ PAGE 1: DASHBOARD ============

if page == "📊 Dashboard" or (page == "📊 Industry Dashboard" and user['role'] == 'industry'):
    st.title("⚡ Advanced Energy Dashboard")
    
    if user['role'] == 'industry':
        industry_id = user['industry_id']
    else:
        st.error("Please select an industry from 'All Industries' page first")
        st.stop()
    
    machines = Database.get_machines(industry_id)
    
    if not machines:
        st.warning("No machines found")
        st.stop()
    
    latest_data = {}
    for machine in machines:
        latest_data[machine['id']] = Database.get_machine_latest_data(machine['id'])
    
    # KPI Section
    st.subheader("📊 Key Performance Indicators")
    
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    total_power = sum(d['power'] for d in latest_data.values() if d)
    active_machines = sum(1 for d in latest_data.values() if d and d['relay_status'] == 1)
    anomalies_24h = sum(1 for d in latest_data.values() if d and d['anomaly'] == 1)
    avg_efficiency = (active_machines / len(machines) * 100) if machines else 0
    
    with kpi1:
        st.metric("⚡ Total Power", f"{total_power:.2f} W", f"{total_power/1000:.2f} kW")
    
    with kpi2:
        st.metric("🟢 Active Machines", f"{active_machines}/{len(machines)}", f"{avg_efficiency:.1f}%")
    
    with kpi3:
        st.metric("⚠️ Anomalies (24h)", anomalies_24h, "Critical" if anomalies_24h > 5 else "Normal")
    
    with kpi4:
        avg_voltage = np.mean([d['voltage'] for d in latest_data.values() if d])
        st.metric("⚡ Avg Voltage", f"{avg_voltage:.2f} V", "Normal" if 220 <= avg_voltage <= 250 else "Out of Range")
    
    with kpi5:
        avg_current = np.mean([d['current'] for d in latest_data.values() if d])
        st.metric("🔌 Avg Current", f"{avg_current:.2f} A")
    
    st.markdown("---")
    
    # Real-time monitoring
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
    
    # Charts
    st.subheader("📈 Advanced Analytics")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        power_data = [d['power'] for d in latest_data.values() if d]
        machine_names = [m['machine_name'] for m in machines if latest_data[m['id']]]
        
        fig = go.Figure(data=[go.Pie(labels=machine_names, values=power_data)])
        fig.update_layout(title="Power Distribution", template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        voltages = [d['voltage'] for d in latest_data.values() if d]
        currents = [d['current'] for d in latest_data.values() if d]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=voltages, name="Voltage (V)", mode='lines+markers'))
        fig.add_trace(go.Scatter(y=currents, name="Current (A)", mode='lines+markers', yaxis="y2"))
        
        fig.update_layout(title="Voltage & Current", template="plotly_dark", height=400, yaxis2=dict(overlaying='y', side='right'))
        st.plotly_chart(fig, use_container_width=True)
    
    time.sleep(refresh_rate)
    st.rerun()


# ============ PAGE 2 ADMIN: ALL INDUSTRIES ============

elif page == "👨‍💼 All Industries":
    st.title("👨‍💼 All Industries Overview")
    
    if user['role'] != 'admin':
        st.error("Only admins can access this page")
        st.stop()
    
    industries = Database.get_all_industries()
    
    if not industries:
        st.warning("No industries found")
        st.stop()
    
    st.subheader(f"📊 Total Industries: {len(industries)}")
    
    cols = st.columns(3)
    
    for idx, industry in enumerate(industries):
        with cols[idx % 3]:
            machines = Database.get_machines(industry['id'])
            
            total_power = 0
            active_machines = 0
            anomalies = 0
            
            for machine in machines:
                latest = Database.get_machine_latest_data(machine['id'])
                if latest:
                    total_power += latest['power']
                    if latest['relay_status'] == 1:
                        active_machines += 1
                    if latest['anomaly'] == 1:
                        anomalies += 1
            
            with st.container(border=True):
                st.markdown(f"### 🏭 {industry['industry_name']}")
                st.write(f"📍 **Location:** {industry['location']}")
                st.write(f"👤 **Contact:** {industry['contact_person']}")
                st.write(f"📧 **Email:** {industry['contact_email']}")
                
                st.markdown("---")
                
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.metric("🔧 Machines", len(machines))
                
                with col_b:
                    st.metric("⚡ Power", f"{total_power:.0f} W")
                
                with col_c:
                    st.metric("⚠️ Anomalies", anomalies)
                
                st.markdown("---")
                
                if st.button(f"📊 View Dashboard", key=f"industry_{industry['id']}"):
                    st.session_state.selected_industry_id = industry['id']
                    st.session_state.selected_industry_name = industry['industry_name']
                    st.switch_page("pages/02_industry_dashboard.py")


# ============ PAGE 3 ADMIN: INDUSTRY DASHBOARD ============

elif page == "📊 Industry Dashboard" and user['role'] == 'admin':
    st.title("📊 Industry Dashboard (Admin View)")
    
    industries = Database.get_all_industries()
    industry_names = [ind['industry_name'] for ind in industries]
    industry_ids = [ind['id'] for ind in industries]
    
    selected_industry_name = st.selectbox(
        "🏭 Select Industry:",
        industry_names,
        key="admin_industry_select"
    )
    
    industry_id = industry_ids[industry_names.index(selected_industry_name)]
    
    st.markdown("---")
    
    machines = Database.get_machines(industry_id)
    
    if not machines:
        st.warning("No machines found for this industry")
        st.stop()
    
    latest_data = {}
    for machine in machines:
        latest_data[machine['id']] = Database.get_machine_latest_data(machine['id'])
    
    # KPI Section
    st.subheader("📊 Key Performance Indicators")
    
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    total_power = sum(d['power'] for d in latest_data.values() if d)
    active_machines = sum(1 for d in latest_data.values() if d and d['relay_status'] == 1)
    anomalies_24h = sum(1 for d in latest_data.values() if d and d['anomaly'] == 1)
    avg_efficiency = (active_machines / len(machines) * 100) if machines else 0
    
    with kpi1:
        st.metric("⚡ Total Power", f"{total_power:.2f} W", f"{total_power/1000:.2f} kW")
    
    with kpi2:
        st.metric("🟢 Active Machines", f"{active_machines}/{len(machines)}", f"{avg_efficiency:.1f}%")
    
    with kpi3:
        st.metric("⚠️ Anomalies (24h)", anomalies_24h, "Critical" if anomalies_24h > 5 else "Normal")
    
    with kpi4:
        avg_voltage = np.mean([d['voltage'] for d in latest_data.values() if d])
        st.metric("⚡ Avg Voltage", f"{avg_voltage:.2f} V", "Normal" if 220 <= avg_voltage <= 250 else "Out of Range")
    
    with kpi5:
        avg_current = np.mean([d['current'] for d in latest_data.values() if d])
        st.metric("🔌 Avg Current", f"{avg_current:.2f} A")
    
    st.markdown("---")
    
    # Real-time monitoring
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


# ============ PAGE 4: ANALYTICS ============

elif page == "🔍 Analytics":
    st.title("🔍 Advanced Analytics & Insights")
    
    if user['role'] == 'industry':
        industry_id = user['industry_id']
    else:
        industries = Database.get_all_industries()
        industry_names = [ind['industry_name'] for ind in industries]
        industry_ids = [ind['id'] for ind in industries]
        
        selected_industry_name = st.selectbox("🏭 Select Industry:", industry_names, key="analytics_industry")
        industry_id = industry_ids[industry_names.index(selected_industry_name)]
    
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
    
    st.subheader("📊 Statistical Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Mean Power", f"{history['power'].mean():.2f} W", f"Std Dev: {history['power'].std():.2f}")
    
    with col2:
        st.metric("Power Range", f"{history['power'].max() - history['power'].min():.2f} W", f"Min: {history['power'].min():.2f} W")
    
    with col3:
        from scipy import stats as sp_stats
        skewness_val = sp_stats.skew(history['power'])
        st.metric("Distribution Skewness", f"{skewness_val:.2f}", "Normal" if -0.5 <= skewness_val <= 0.5 else "Skewed")
    
    st.markdown("---")
    st.subheader("📈 Distribution Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.histogram(history, x='power', nbins=30, title='Power Distribution', template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = go.Figure(data=[go.Box(y=history['power'], name='Power (W)', marker_color='rgba(102, 126, 234, 0.7)')])
        fig.update_layout(title='Power Boxplot', template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)


# ============ PAGE 5: ANOMALIES ============

elif page == "⚠️ Anomalies":
    st.title("⚠️ Advanced Anomaly Detection")
    
    if user['role'] == 'industry':
        industry_id = user['industry_id']
        anomalies = Database.get_anomalies(industry_id, limit=500)
    else:
        st.error("Use 'All Anomalies' from sidebar")
        st.stop()
    
    if anomalies.empty:
        st.success("✅ No anomalies detected!")
    else:
        st.warning(f"⚠️ Found {len(anomalies)} anomalies")
        st.dataframe(anomalies[['timestamp', 'machine_name', 'voltage', 'current', 'power', 'energy']], use_container_width=True, hide_index=True)


# ============ PAGE 6 ADMIN: ALL ANOMALIES ============

elif page == "⚠️ All Anomalies":
    st.title("⚠️ All Anomalies (Admin View)")
    
    if user['role'] != 'admin':
        st.error("Only admins can access this page")
        st.stop()
    
    anomalies = Database.get_all_anomalies(limit=500)
    
    if anomalies.empty:
        st.success("✅ No anomalies detected across all industries!")
    else:
        st.warning(f"⚠️ Found {len(anomalies)} anomalies")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Anomalies", len(anomalies))
        
        with col2:
            affected_industries = anomalies['industry_name'].nunique()
            st.metric("Affected Industries", affected_industries)
        
        with col3:
            affected_machines = anomalies['machine_name'].nunique()
            st.metric("Affected Machines", affected_machines)
        
        st.markdown("---")
        st.dataframe(anomalies[['timestamp', 'industry_name', 'machine_name', 'voltage', 'current', 'power', 'energy']], use_container_width=True, hide_index=True)


# ============ PAGE 7: FORECASTING ============

elif page == "📈 Forecasting":
    st.title("📈 Power Forecasting & Predictions")
    
    if user['role'] == 'industry':
        industry_id = user['industry_id']
    else:
        industries = Database.get_all_industries()
        industry_names = [ind['industry_name'] for ind in industries]
        industry_ids = [ind['id'] for ind in industries]
        
        selected_industry_name = st.selectbox("🏭 Select Industry:", industry_names, key="forecast_industry")
        industry_id = industry_ids[industry_names.index(selected_industry_name)]
    
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
    
    st.subheader("📊 Power Forecast (Next 7 Days)")
    
    history['date'] = pd.to_datetime(history['timestamp']).dt.date
    daily_power = history.groupby('date')['power'].mean()
    
    alpha = 0.3
    forecast = [daily_power.iloc[-1]]
    
    for i in range(7):
        forecast.append(alpha * daily_power.iloc[-1] + (1 - alpha) * forecast[-1])
    
    forecast_dates = pd.date_range(start=daily_power.index[-1], periods=8, freq='D')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily_power.index, y=daily_power.values, name='Historical', mode='lines+markers'))
    fig.add_trace(go.Scatter(x=forecast_dates, y=forecast, name='Forecast', mode='lines+markers', line=dict(dash='dash')))
    fig.update_layout(title='7-Day Power Consumption Forecast', template='plotly_dark', xaxis_title='Date', yaxis_title='Power (W)')
    
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
        st.metric("Expected Change", f"{change:.1f}%")


# ============ PAGE 8: SETTINGS ============

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
                    st.download_button("📥 Download CSV", csv, "energy_data_export.csv", "text/csv")
                else:
                    st.warning("No data to export")
            else:
                st.info("Admin export feature coming soon")
    
    with col2:
        if st.button("📊 Generate Report", use_container_width=True):
            st.session_state.generate_report = True
    
    with col3:
        if st.button("🔄 Refresh All Data", use_container_width=True):
            st.rerun()
    
    # ========== REPORT GENERATION ============
    if st.session_state.get('generate_report', False):
        st.markdown("---")
        st.subheader("📄 Generating Report...")
        
        with st.spinner("⏳ Generating comprehensive report..."):
            
            if user['role'] == 'industry':
                industry_id = user['industry_id']
                industry = Database.get_industry_data(industry_id)
                machines = Database.get_machines(industry_id)
            else:
                st.error("Please select an industry first")
                st.stop()
            
            # ========== REPORT CONTENT ============
            report_data = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'industry': industry['industry_name'],
                'location': industry['location'],
                'contact': industry['contact_person'],
                'email': industry['contact_email'],
                'total_machines': len(machines),
                'report_period': '30 Days',
                'machines': []
            }
            
            total_energy = 0
            total_power_avg = 0
            total_anomalies = 0
            
            # Get stats for each machine
            for machine in machines:
                stats = Database.get_machine_stats(machine['id'], hours=720)  # 30 days
                history = Database.get_machine_history(machine['id'], hours=720)
                
                if stats and not history.empty:
                    machine_report = {
                        'name': machine['machine_name'],
                        'type': machine['machine_type'],
                        'avg_power': float(stats['avg_power']) if stats['avg_power'] else 0,
                        'max_power': float(stats['max_power']) if stats['max_power'] else 0,
                        'min_power': float(stats['min_power']) if stats['min_power'] else 0,
                        'avg_voltage': float(stats['avg_voltage']) if stats['avg_voltage'] else 0,
                        'avg_current': float(stats['avg_current']) if stats['avg_current'] else 0,
                        'total_energy': float(stats['total_energy']) if stats['total_energy'] else 0,
                        'anomaly_count': int(stats['anomaly_count']) if stats['anomaly_count'] else 0,
                        'uptime_percentage': (len(history[history['relay_status'] == 1]) / len(history) * 100) if len(history) > 0 else 0
                    }
                    
                    report_data['machines'].append(machine_report)
                    total_energy += machine_report['total_energy']
                    total_power_avg += machine_report['avg_power']
                    total_anomalies += machine_report['anomaly_count']
            
            report_data['total_energy'] = total_energy
            report_data['avg_power'] = total_power_avg / len(machines) if machines else 0
            report_data['total_anomalies'] = total_anomalies
            
            # ========== DISPLAY REPORT ============
            st.success("✅ Report Generated Successfully!")
            
            # Display tabs for different report views
            tab1, tab2, tab3 = st.tabs(["📋 Summary", "📊 Detailed Data", "💾 Download"])
            
            with tab1:
                st.subheader("📋 Executive Summary")
                
                summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
                
                with summary_col1:
                    st.metric("🏭 Industry", report_data['industry'])
                
                with summary_col2:
                    st.metric("📍 Location", report_data['location'])
                
                with summary_col3:
                    st.metric("📅 Report Date", report_data['timestamp'][:10])
                
                with summary_col4:
                    st.metric("📊 Period", report_data['report_period'])
                
                st.markdown("---")
                
                st.subheader("📈 Key Metrics (30 Days)")
                
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.metric(
                        "🔧 Total Machines",
                        report_data['total_machines'],
                        delta=f"Running machines"
                    )
                
                with metric_col2:
                    st.metric(
                        "⚡ Avg Power",
                        f"{report_data['avg_power']:.2f} W",
                        delta=f"{report_data['avg_power']/1000:.2f} kW"
                    )
                
                with metric_col3:
                    st.metric(
                        "🔋 Total Energy",
                        f"{report_data['total_energy']:.2f} kWh",
                        delta=f"Consumed"
                    )
                
                with metric_col4:
                    st.metric(
                        "⚠️ Total Anomalies",
                        report_data['total_anomalies'],
                        delta="Critical" if report_data['total_anomalies'] > 10 else "Normal"
                    )
                
                st.markdown("---")
                
                st.subheader("💡 Insights & Recommendations")
                
                # Generate insights
                if report_data['total_anomalies'] > 10:
                    st.warning(f"⚠️ **High anomaly rate detected**: {report_data['total_anomalies']} anomalies in 30 days. Consider maintenance.")
                else:
                    st.info(f"✅ **System healthy**: {report_data['total_anomalies']} anomalies detected. Good performance!")
                
                # Find highest consuming machine
                if report_data['machines']:
                    highest = max(report_data['machines'], key=lambda x: x['total_energy'])
                    st.info(f"📊 **Highest consumer**: {highest['name']} with {highest['total_energy']:.2f} kWh")
                    
                    # Find machine with most anomalies
                    most_issues = max(report_data['machines'], key=lambda x: x['anomaly_count'])
                    if most_issues['anomaly_count'] > 0:
                        st.warning(f"🔧 **Requires attention**: {most_issues['name']} had {most_issues['anomaly_count']} anomalies")
            
            with tab2:
                st.subheader("📊 Detailed Machine Performance")
                
                # Create detailed dataframe
                machines_df = pd.DataFrame(report_data['machines'])
                
                st.dataframe(
                    machines_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                st.markdown("---")
                
                # Machine comparison charts
                st.subheader("📈 Machine Comparison")
                
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    # Energy consumption chart
                    fig = px.bar(
                        machines_df,
                        x='name',
                        y='total_energy',
                        title='Total Energy Consumption by Machine',
                        labels={'name': 'Machine', 'total_energy': 'Energy (kWh)'},
                        template='plotly_dark'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with chart_col2:
                    # Anomalies chart
                    fig = px.bar(
                        machines_df,
                        x='name',
                        y='anomaly_count',
                        title='Anomalies by Machine',
                        labels={'name': 'Machine', 'anomaly_count': 'Count'},
                        template='plotly_dark',
                        color='anomaly_count',
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Uptime chart
                fig = px.bar(
                    machines_df,
                    x='name',
                    y='uptime_percentage',
                    title='Machine Uptime %',
                    labels={'name': 'Machine', 'uptime_percentage': 'Uptime (%)'},
                    template='plotly_dark'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                st.subheader("💾 Download Report")
                
                # Generate PDF-like report
                from datetime import datetime
                
                report_text = f"""
ENERGY MANAGEMENT SYSTEM - COMPREHENSIVE REPORT
{'='*80}

Report Generated: {report_data['timestamp']}
Report Period: {report_data['report_period']}

INDUSTRY DETAILS
{'='*80}
Industry Name: {report_data['industry']}
Location: {report_data['location']}
Contact Person: {report_data['contact']}
Contact Email: {report_data['email']}

EXECUTIVE SUMMARY
{'='*80}
Total Machines: {report_data['total_machines']}
Average Power Consumption: {report_data['avg_power']:.2f} W ({report_data['avg_power']/1000:.2f} kW)
Total Energy Consumed: {report_data['total_energy']:.2f} kWh
Total Anomalies: {report_data['total_anomalies']}

DETAILED MACHINE PERFORMANCE
{'='*80}
"""
                
                for idx, machine in enumerate(report_data['machines'], 1):
                    report_text += f"""
Machine {idx}: {machine['name']}
Type: {machine['type']}
Average Power: {machine['avg_power']:.2f} W
Peak Power: {machine['max_power']:.2f} W
Minimum Power: {machine['min_power']:.2f} W
Average Voltage: {machine['avg_voltage']:.2f} V
Average Current: {machine['avg_current']:.2f} A
Total Energy: {machine['total_energy']:.2f} kWh
Anomalies: {machine['anomaly_count']}
Uptime: {machine['uptime_percentage']:.2f}%
{'-'*80}
"""
                
                report_text += f"""
{'='*80}
RECOMMENDATIONS
{'='*80}

1. Energy Optimization:
   - Review high-consuming machines for efficiency improvements
   - Consider load balancing across machines

2. Maintenance:
   - Address machines with high anomaly counts
   - Schedule preventive maintenance

3. Monitoring:
   - Continue real-time monitoring of all machines
   - Set up alerts for anomalies

{'='*80}
End of Report
"""
                
                # Download as text
                st.download_button(
                    label="📄 Download Report (TXT)",
                    data=report_text,
                    file_name=f"energy_report_{report_data['industry']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
                
                # Download as CSV (detailed data)
                machines_df = pd.DataFrame(report_data['machines'])
                csv = machines_df.to_csv(index=False)
                
                st.download_button(
                    label="📊 Download Data (CSV)",
                    data=csv,
                    file_name=f"energy_data_{report_data['industry']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                st.success("✅ Reports ready for download!")
            
            st.markdown("---")
            
            if st.button("Clear Report"):
                st.session_state.generate_report = False
                st.rerun()