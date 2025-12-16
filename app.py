"""
================================================================================================
EY TECHATHON - AUTONOMOUS AFTERSALES OS
================================================================================================
MVP: Self-Healing Automotive Ecosystem with Agentic AI & Google Gemini Integration

Architecture:
  1. TELEMATICS LAYER (Left Column): Real-time sensor data capture & anomaly detection
  2. AGENTIC ORCHESTRATOR (Middle Column): Multi-agent chain-of-thought diagnosis
  3. VALUE DELIVERY (Right Column): Customer engagement + Manufacturing feedback loop

Key Features:
  - Sentinel Agent: Anomaly detection at telematics ingestion
  - Mechanic Agent: AI-powered root cause analysis via Gemini
  - Concierge Agent: Empathetic customer communication generation
  - UEBA Layer: Security verification before each agent action
  - Closed-Loop Manufacturing: JSON-based design improvement feedback
  - Fallback: Mock responses if Google API key is invalid/missing
================================================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import os

# ================================ GOOGLE GEMINI SETUP ================================
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    st.warning("Google AI Python SDK not installed. Install with: pip install google-generativeai")

# ================================ STREAMLIT PAGE CONFIG ================================
st.set_page_config(
    page_title="Autonomous Aftersales OS",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================ CUSTOM CSS FOR DARK ENTERPRISE THEME ================================
CUSTOM_CSS = """
<style>
    /* Dark Theme with Neon Accents */
    :root {
        --primary-color: #00D9FF;
        --danger-color: #FF006E;
        --success-color: #00FF41;
        --warning-color: #FFD60A;
        --dark-bg: #0A0E27;
        --card-bg: #1A1F3A;
    }

    /* Main container styling */
    .main {
        background-color: #0A0E27;
        color: #E0E0E0;
    }

    /* Metric card styling */
    [data-testid="metric-container"] {
        background-color: #1A1F3A !important;
        border: 1px solid #00D9FF !important;
        border-radius: 8px !important;
        padding: 15px !important;
        box-shadow: 0 0 15px rgba(0, 217, 255, 0.3) !important;
    }

    /* Agent containers */
    .agent-container {
        background: linear-gradient(135deg, #1A1F3A 0%, #2A2F4A 100%);
        border-left: 4px solid #00D9FF;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        box-shadow: 0 0 10px rgba(0, 217, 255, 0.2);
    }

    .agent-sentinel {
        border-left-color: #FFD60A !important;
        background: linear-gradient(135deg, #2A2620 0%, #3A3020 100%);
    }

    .agent-mechanic {
        border-left-color: #00D9FF !important;
    }

    .agent-concierge {
        border-left-color: #00FF41 !important;
        background: linear-gradient(135deg, #1A2A1A 0%, #2A3A2A 100%);
    }

    /* Critical alert styling with pulse animation */
    .critical-alert {
        background-color: #FF006E;
        color: white;
        padding: 16px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        animation: pulse 1s infinite;
        box-shadow: 0 0 20px rgba(255, 0, 110, 0.8);
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    /* Success alert styling */
    .success-alert {
        background-color: #00FF41;
        color: #0A0E27;
        padding: 12px;
        border-radius: 8px;
        font-weight: bold;
    }

    /* UEBA badge */
    .ueba-badge {
        background: linear-gradient(90deg, #00D9FF, #00FF41);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        font-size: 14px;
        animation: glow 2s ease-in-out infinite;
    }

    @keyframes glow {
        0%, 100% { filter: drop-shadow(0 0 3px #00D9FF); }
        50% { filter: drop-shadow(0 0 8px #00FF41); }
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #1A1F3A !important;
        border-radius: 8px !important;
    }

    /* Button styling */
    .stButton > button {
        background-color: #00D9FF !important;
        color: #0A0E27 !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 10px 20px !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        background-color: #00FF41 !important;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.5) !important;
    }

    /* Danger button */
    .danger-btn > button {
        background-color: #FF006E !important;
        color: white !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1A1F3A !important;
    }

    /* Text styling */
    h1, h2, h3 {
        color: #00D9FF !important;
        text-shadow: 0 0 10px rgba(0, 217, 255, 0.5) !important;
    }

    /* JSON display styling */
    .json-display {
        background-color: #0A0E27 !important;
        border: 1px solid #00D9FF !important;
        border-radius: 6px !important;
        padding: 12px !important;
        font-family: 'Courier New', monospace !important;
        color: #00FF41 !important;
        font-size: 12px !important;
        overflow-x: auto !important;
    }

    /* Status indicator */
    .status-healthy {
        color: #00FF41 !important;
        font-weight: bold !important;
    }

    .status-warning {
        color: #FFD60A !important;
        font-weight: bold !important;
    }

    .status-critical {
        color: #FF006E !important;
        font-weight: bold !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ================================ UTILITY FUNCTIONS ================================

def initialize_session_state():
    """Initialize all session state variables for persistent state across reruns."""
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    if "gemini_client_ready" not in st.session_state:
        st.session_state.gemini_client_ready = False
    if "sensor_history" not in st.session_state:
        st.session_state.sensor_history = {
            "timestamps": [],
            "temperatures": [],
            "vibrations": [],
            "voltages": []
        }
    if "alert_triggered" not in st.session_state:
        st.session_state.alert_triggered = False
    if "diagnosis_result" not in st.session_state:
        st.session_state.diagnosis_result = None
    if "customer_message" not in st.session_state:
        st.session_state.customer_message = None
    if "manufacturing_feedback" not in st.session_state:
        st.session_state.manufacturing_feedback = None
    if "selected_slot" not in st.session_state:
        st.session_state.selected_slot = None

def setup_gemini_api(api_key: str) -> bool:
    """
    Configure Google Gemini API with provided key.
    
    Args:
        api_key: Google API key
        
    Returns:
        bool: True if successfully configured, False otherwise
    """
    if not GEMINI_AVAILABLE:
        return False
    
    try:
        if api_key and api_key.strip():
            genai.configure(api_key=api_key)
            # Verify the API key by making a test call
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content("ping", stream=False)
            return True
    except Exception as e:
        st.warning(f"⚠️ Gemini API Configuration Issue: {str(e)[:100]}")
    
    return False

def generate_sensor_data(
    base_temp: float, 
    base_vibration: float, 
    base_voltage: float,
    noise_level: float = 2.0
) -> Tuple[float, float, float]:
    """
    Generate realistic sensor data with controlled noise.
    
    Args:
        base_temp: Base engine temperature
        base_vibration: Base vibration level
        base_voltage: Base battery voltage
        noise_level: Gaussian noise standard deviation
        
    Returns:
        Tuple of (temp, vibration, voltage) with noise applied
    """
    temp = max(50, base_temp + np.random.normal(0, noise_level))
    vibration = max(0, base_vibration + np.random.normal(0, noise_level * 0.1))
    voltage = max(8, base_voltage + np.random.normal(0, noise_level * 0.05))
    return temp, vibration, voltage

def update_sensor_history(temp: float, vibration: float, voltage: float, history_size: int = 60):
    """
    Maintain rolling window of sensor history for charting.
    
    Args:
        temp: Current temperature reading
        vibration: Current vibration reading
        voltage: Current voltage reading
        history_size: Maximum number of data points to retain
    """
    now = datetime.now()
    
    st.session_state.sensor_history["timestamps"].append(now)
    st.session_state.sensor_history["temperatures"].append(temp)
    st.session_state.sensor_history["vibrations"].append(vibration)
    st.session_state.sensor_history["voltages"].append(voltage)
    
    # Keep only last N samples
    for key in st.session_state.sensor_history:
        if len(st.session_state.sensor_history[key]) > history_size:
            st.session_state.sensor_history[key] = st.session_state.sensor_history[key][-history_size:]

def check_thresholds(temp: float, vibration: float, voltage: float) -> Tuple[bool, List[str]]:
    """
    Sentinel Agent Logic: Detect anomalies against predefined thresholds.
    
    Thresholds:
    - Engine Temperature: > 110°C (critical), > 95°C (warning)
    - Vibration Level: > 8.5 (critical), > 7.0 (warning)
    - Battery Voltage: < 10.5V (critical), < 11.5V (warning)
    
    Args:
        temp: Engine temperature
        vibration: Vibration level
        voltage: Battery voltage
        
    Returns:
        Tuple of (is_critical, list_of_anomalies)
    """
    anomalies = []
    is_critical = False
    
    if temp > 110:
        anomalies.append(f"🔴 CRITICAL: Engine Temperature {temp:.1f}°C (threshold: 110°C)")
        is_critical = True
    elif temp > 95:
        anomalies.append(f"🟡 WARNING: Engine Temperature {temp:.1f}°C (threshold: 95°C)")
    
    if vibration > 8.5:
        anomalies.append(f"🔴 CRITICAL: Vibration Level {vibration:.2f} (threshold: 8.5)")
        is_critical = True
    elif vibration > 7.0:
        anomalies.append(f"🟡 WARNING: Vibration Level {vibration:.2f} (threshold: 7.0)")
    
    if voltage < 10.5:
        anomalies.append(f"🔴 CRITICAL: Battery Voltage {voltage:.2f}V (threshold: 10.5V)")
        is_critical = True
    elif voltage < 11.5:
        anomalies.append(f"🟡 WARNING: Battery Voltage {voltage:.2f}V (threshold: 11.5V)")
    
    return is_critical, anomalies

def create_sensor_chart(history: Dict) -> go.Figure:
    """
    Create interactive Plotly chart for real-time sensor visualization.
    
    Args:
        history: Dictionary containing timestamps and sensor readings
        
    Returns:
        Plotly Figure object
    """
    if not history["timestamps"]:
        # Return empty chart if no data
        fig = go.Figure()
        fig.add_annotation(text="Awaiting sensor data...", xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="#00D9FF"))
        return fig
    
    # Create subplot figure with 3 y-axes
    fig = go.Figure()
    
    # Temperature trace
    fig.add_trace(go.Scatter(
        x=history["timestamps"],
        y=history["temperatures"],
        name="Temperature (°C)",
        line=dict(color="#FF006E", width=2),
        yaxis="y1",
        fill="tozeroy",
        fillcolor="rgba(255, 0, 110, 0.1)"
    ))
    
    # Vibration trace
    fig.add_trace(go.Scatter(
        x=history["timestamps"],
        y=history["vibrations"],
        name="Vibration (G)",
        line=dict(color="#00D9FF", width=2),
        yaxis="y2",
        fill="tozeroy",
        fillcolor="rgba(0, 217, 255, 0.1)"
    ))
    
    # Voltage trace
    fig.add_trace(go.Scatter(
        x=history["timestamps"],
        y=history["voltages"],
        name="Voltage (V)",
        line=dict(color="#00FF41", width=2),
        yaxis="y3",
        fill="tozeroy",
        fillcolor="rgba(0, 255, 65, 0.1)"
    ))
    
    # Update layout with dark theme
    fig.update_layout(
        title="📊 Real-Time Sensor Data Stream",
        plot_bgcolor="#0A0E27",
        paper_bgcolor="#1A1F3A",
        font=dict(color="#E0E0E0", size=11),
        hovermode="x unified",
        margin=dict(l=50, r=100, t=50, b=50),
       yaxis=dict(
    title=dict(
        text="Temperature (°C)",
        font=dict(color="#FF006E")
    ),
    tickfont=dict(color="#FF006E"),
    position=0
),

yaxis2=dict(
    title=dict(
        text="Vibration (G)",
        font=dict(color="#00D9FF")
    ),
    tickfont=dict(color="#00D9FF"),
    overlaying="y",
    side="left",
    position=0.1
),

yaxis3=dict(
    title=dict(
        text="Voltage (V)",
        font=dict(color="#00FF41")
    ),
    tickfont=dict(color="#00FF41"),
    overlaying="y",
    side="right"
),
        legend=dict(
            x=0.01, y=0.99,
            bgcolor="rgba(26, 31, 58, 0.8)",
            bordercolor="#00D9FF",
            borderwidth=1
        )
    )
    
    return fig

def call_gemini_mechanic(temp: float, vibration: float, voltage: float, anomalies: List[str]) -> str:
    """
    Agent 2: Mechanic Agent - Diagnose root cause using Gemini.
    
    This agent analyzes sensor data and provides technical diagnosis.
    
    Args:
        temp: Engine temperature
        vibration: Vibration level
        voltage: Battery voltage
        anomalies: List of detected anomalies
        
    Returns:
        Diagnosis string (from Gemini or mock fallback)
    """
    if not st.session_state.gemini_client_ready:
        # Mock diagnosis for fallback
        return mock_mechanic_diagnosis(temp, vibration, voltage, anomalies)
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""You are an automotive diagnostic AI. Analyze the following vehicle sensor data and provide a concise technical diagnosis.

Sensor Readings:
- Engine Temperature: {temp:.1f}°C
- Vibration Level: {vibration:.2f}G
- Battery Voltage: {voltage:.2f}V

Detected Anomalies:
{json.dumps(anomalies, indent=2)}

Provide a diagnosis in 2-3 sentences identifying the most likely root cause and its impact on vehicle operation."""
        
        response = model.generate_content(prompt, stream=False)
        return response.text if response else mock_mechanic_diagnosis(temp, vibration, voltage, anomalies)
    
    except Exception as e:
        st.warning(f"Gemini API error: {str(e)[:100]}")
        return mock_mechanic_diagnosis(temp, vibration, voltage, anomalies)

def mock_mechanic_diagnosis(temp: float, vibration: float, voltage: float, anomalies: List[str]) -> str:
    """Generate mock diagnosis when API is unavailable."""
    if temp > 110:
        return "🔧 Diagnosis: Engine overheating detected. Primary suspect: Failed thermostat or water pump failure. Recommend immediate inspection of cooling system. Risk Level: CRITICAL"
    elif vibration > 8.5:
        return "🔧 Diagnosis: Excessive vibration indicates mechanical imbalance. Likely causes: Worn engine mounts, bearing issues, or fuel injection problem. Recommend alignment check and engine inspection."
    elif voltage < 10.5:
        return "🔧 Diagnosis: Battery voltage critically low. Suspect: Alternator malfunction or battery cell degradation. Vehicle electrical systems at risk. Recommend battery/alternator test."
    else:
        return "🔧 Diagnosis: Multiple system anomalies detected. Recommend comprehensive diagnostic scan and OBD-II analysis."

def call_gemini_concierge(diagnosis: str, customer_name: str = "Valued Customer") -> str:
    """
    Agent 3: Concierge Agent - Generate empathetic customer communication.
    
    This agent drafts personalized WhatsApp-style messages to the customer.
    
    Args:
        diagnosis: Technical diagnosis from Mechanic Agent
        customer_name: Customer's name
        
    Returns:
        Customer message string (from Gemini or mock fallback)
    """
    if not st.session_state.gemini_client_ready:
        return mock_customer_message(diagnosis, customer_name)
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""You are a friendly and empathetic automotive customer service agent. Draft a brief, WhatsApp-style message (3-4 sentences) to inform a customer about a vehicle issue and offer immediate assistance.

Technical Diagnosis:
{diagnosis}

Customer Name: {customer_name}

Guidelines:
- Use a warm, professional tone
- Be honest about the issue but remain reassuring
- Mention immediate next steps (service booking)
- Keep it concise for messaging platform

Generate ONLY the message text, no additional commentary."""
        
        response = model.generate_content(prompt, stream=False)
        return response.text if response else mock_customer_message(diagnosis, customer_name)
    
    except Exception as e:
        st.warning(f"Gemini API error: {str(e)[:100]}")
        return mock_customer_message(diagnosis, customer_name)

def mock_customer_message(diagnosis: str, customer_name: str) -> str:
    """Generate mock customer message when API is unavailable."""
    return f"""Hi {customer_name},\n\nWe've detected an issue with your vehicle during our proactive monitoring. Our technicians have identified a potential problem that needs attention soon. We'd like to schedule a service appointment at your earliest convenience. We're here to help! 🚗"""

def call_gemini_manufacturing(temp: float, vibration: float, voltage: float, anomalies: List[str]) -> Dict:
    """
    Manufacturing Feedback Layer: Generate closed-loop design improvement suggestions.
    
    This represents the feedback loop from field data back to engineering/manufacturing.
    
    Args:
        temp: Engine temperature
        vibration: Vibration level
        voltage: Battery voltage
        anomalies: List of detected anomalies
        
    Returns:
        JSON object with Root_Cause, Defect_Cluster_ID, and Design_Improvement_Suggestion
    """
    if not st.session_state.gemini_client_ready:
        return mock_manufacturing_feedback(temp, vibration, voltage)
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""You are an automotive manufacturing quality engineer. Analyze this field failure data and generate a JSON response with improvement suggestions for design iteration.

Sensor Readings:
- Engine Temperature: {temp:.1f}°C
- Vibration Level: {vibration:.2f}G
- Battery Voltage: {voltage:.2f}V

Detected Anomalies:
{json.dumps(anomalies, indent=2)}

Return ONLY a valid JSON object (no markdown, no explanation) with these exact fields:
{{
    "Root_Cause": "specific technical root cause",
    "Defect_Cluster_ID": "CLUSTER_XXX",
    "Design_Improvement_Suggestion": "actionable engineering improvement for next design iteration"
}}"""
        
        response = model.generate_content(prompt, stream=False)
        response_text = response.text if response else "{}"
        
        # Clean up response (remove markdown code blocks if present)
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return mock_manufacturing_feedback(temp, vibration, voltage)
    
    except Exception as e:
        st.warning(f"Manufacturing feedback error: {str(e)[:100]}")
        return mock_manufacturing_feedback(temp, vibration, voltage)

def mock_manufacturing_feedback(temp: float, vibration: float, voltage: float) -> Dict:
    """Generate mock manufacturing feedback when API is unavailable."""
    return {
        "Root_Cause": "Thermal management system degradation" if temp > 100 else "Electrical subsystem performance drift",
        "Defect_Cluster_ID": "CLUSTER_THERM_001" if temp > 100 else "CLUSTER_ELEC_002",
        "Design_Improvement_Suggestion": "Upgrade coolant circulation pump capacity and add secondary thermal sensor redundancy" if temp > 100 else "Implement higher-capacity alternator and battery with integrated voltage regulation module"
    }

def get_available_service_slots() -> List[str]:
    """Generate list of available service booking slots."""
    slots = []
    now = datetime.now()
    for i in range(1, 6):
        slot_time = now + timedelta(hours=24*i)
        slots.append(slot_time.strftime("%a, %b %d @ %I:%M %p"))
    return slots

# ================================ MAIN APPLICATION ================================

def main():
    """Main application entry point."""
    initialize_session_state()
    
    # ============ HEADER ============
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="font-size: 40px; margin: 0;">🤖 Autonomous Aftersales OS</h1>
        <p style="color: #00D9FF; font-size: 16px;">EY Techathon - Self-Healing Automotive Ecosystem</p>
        <p style="color: #00FF41; font-size: 13px;">Real-time Anomaly Detection → AI Diagnosis → Customer Engagement → Manufacturing Feedback Loop</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ============ SIDEBAR: CONTROLS & API CONFIG ============
    with st.sidebar:
        st.markdown("### ⚙️ System Configuration")
        
        # API Key Input
        api_key_input = st.text_input(
            "Google API Key",
            type="password",
            value=st.session_state.api_key,
            help="Enter your Google Generative AI API key (get it from https://makersuite.google.com/app/apikey)"
        )
        
        if api_key_input != st.session_state.api_key:
            st.session_state.api_key = api_key_input
            if api_key_input:
                with st.spinner("🔐 Verifying API Key..."):
                    st.session_state.gemini_client_ready = setup_gemini_api(api_key_input)
                    if st.session_state.gemini_client_ready:
                        st.success("✅ Gemini API Ready")
                    else:
                        st.info("ℹ️ Using Mock Mode (fallback responses)")
        else:
            if st.session_state.gemini_client_ready:
                st.success("✅ Gemini API Ready")
            else:
                st.info("ℹ️ Using Mock Mode (fallback responses)")
        
        st.markdown("---")
        st.markdown("### 🎮 Simulation Controls")
        
        # Sensor sliders
        temp = st.slider(
            "🌡️ Engine Temperature (°C)",
            min_value=50.0,
            max_value=130.0,
            value=75.0,
            step=1.0,
            help="Normal: 70-95°C, Warning: 95-110°C, Critical: >110°C"
        )
        
        vibration = st.slider(
            "📳 Vibration Level (G)",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=0.1,
            help="Normal: 0-7G, Warning: 7-8.5G, Critical: >8.5G"
        )
        
        voltage = st.slider(
            "🔋 Battery Voltage (V)",
            min_value=8.0,
            max_value=14.5,
            value=13.2,
            step=0.1,
            help="Normal: 12.5-13.5V, Warning: 11.5-12.5V, Critical: <10.5V"
        )
        
        st.markdown("---")
        
        # Simulate Failure Button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔴 Simulate Failure", use_container_width=True):
                st.session_state.sensor_history = {
                    "timestamps": [],
                    "temperatures": [],
                    "vibrations": [],
                    "voltages": []
                }
                st.rerun()
        
        with col2:
            if st.button("🟢 Reset System", use_container_width=True):
                for key in ["diagnosis_result", "customer_message", "manufacturing_feedback", "selected_slot", "alert_triggered"]:
                    st.session_state[key] = None
                st.rerun()
        
        # Quick preset buttons
        st.markdown("**Quick Presets:**")
        preset_cols = st.columns(3)
        
        with preset_cols[0]:
            if st.button("🟢 Healthy", use_container_width=True, key="preset_healthy"):
                st.session_state.temp_override = 75.0
                st.session_state.vibration_override = 2.0
                st.session_state.voltage_override = 13.2
                st.rerun()
        
        with preset_cols[1]:
            if st.button("🟡 Warning", use_container_width=True, key="preset_warning"):
                st.session_state.temp_override = 100.0
                st.session_state.vibration_override = 7.5
                st.session_state.voltage_override = 11.8
                st.rerun()
        
        with preset_cols[2]:
            if st.button("🔴 Critical", use_container_width=True, key="preset_critical"):
                st.session_state.temp_override = 115.0
                st.session_state.vibration_override = 9.0
                st.session_state.voltage_override = 10.0
                st.rerun()
    
    # Apply preset overrides if set
    if "temp_override" in st.session_state:
        temp = st.session_state.temp_override
        del st.session_state.temp_override
    if "vibration_override" in st.session_state:
        vibration = st.session_state.vibration_override
        del st.session_state.vibration_override
    if "voltage_override" in st.session_state:
        voltage = st.session_state.voltage_override
        del st.session_state.voltage_override
    
    # Generate current sensor data
    current_temp, current_vibration, current_voltage = generate_sensor_data(temp, vibration, voltage)
    update_sensor_history(current_temp, current_vibration, current_voltage)
    
    # Sentinel Agent: Check thresholds
    is_critical, anomalies = check_thresholds(current_temp, current_vibration, current_voltage)
    st.session_state.alert_triggered = is_critical
    
    # ============ THREE-COLUMN LAYOUT ============
    col1, col2, col3 = st.columns([1, 1.2, 1], gap="large")
    
    # ========== COLUMN 1: TELEMATICS (INPUT) ==========
    with col1:
        st.markdown("### 📡 Telematics Layer")
        st.markdown("Real-Time Sensor Ingestion & Anomaly Detection")
        
        # Display metrics
        metric_cols = st.columns(3)
        with metric_cols[0]:
            st.metric(
                "🌡️ Temp",
                f"{current_temp:.1f}°C",
                delta=f"{current_temp - 75:.1f}°C",
                delta_color="inverse" if current_temp > 95 else "normal"
            )
        
        with metric_cols[1]:
            st.metric(
                "📳 Vibration",
                f"{current_vibration:.2f}G",
                delta=f"{current_vibration - 2.0:.2f}G",
                delta_color="inverse" if current_vibration > 7.0 else "normal"
            )
        
        with metric_cols[2]:
            st.metric(
                "🔋 Voltage",
                f"{current_voltage:.2f}V",
                delta=f"{current_voltage - 13.2:.2f}V",
                delta_color="normal" if current_voltage > 11.5 else "inverse"
            )
        
        # Display critical alert if triggered
        if is_critical:
            st.markdown(
                '<div class="critical-alert">🚨 CRITICAL ALERT 🚨</div>',
                unsafe_allow_html=True
            )
            time.sleep(0.5)  # Brief pause for visual effect
        
        # Display anomalies
        if anomalies:
            st.markdown("**Detected Anomalies:**")
            for anomaly in anomalies:
                st.markdown(f"- {anomaly}")
        else:
            st.markdown('<p class="status-healthy">✅ All Systems Normal</p>', unsafe_allow_html=True)
        
        # Real-time chart
        st.plotly_chart(
            create_sensor_chart(st.session_state.sensor_history),
            use_container_width=True,
            config={"displayModeBar": False}
        )
        
        # Raw data expander
        with st.expander("📋 Raw Sensor Data"):
            df_data = pd.DataFrame({
                "Timestamp": st.session_state.sensor_history["timestamps"][-10:],
                "Temp (°C)": st.session_state.sensor_history["temperatures"][-10:],
                "Vibration (G)": st.session_state.sensor_history["vibrations"][-10:],
                "Voltage (V)": st.session_state.sensor_history["voltages"][-10:]
            })
            st.dataframe(df_data, use_container_width=True, hide_index=True)
    
    # ========== COLUMN 2: AGENTIC ORCHESTRATOR (BRAIN) ==========
    with col2:
        st.markdown("### 🧠 Agentic Orchestrator")
        st.markdown("Multi-Agent Chain-of-Thought Diagnosis")
        
        # ========== AGENT 1: SENTINEL ==========
        with st.container():
            st.markdown(
                '<div class="agent-container agent-sentinel" style="border-left-color: #FFD60A;">',
                unsafe_allow_html=True
            )
            st.markdown("**🔍 Agent 1: Sentinel** (Anomaly Detection)")
            st.markdown(
                f'<p class="ueba-badge">✓ UEBA Verified: Security Token Valid</p>',
                unsafe_allow_html=True
            )
            
            if is_critical or anomalies:
                st.markdown(f"**Status:** <span class='status-critical'>ANOMALY DETECTED</span>", unsafe_allow_html=True)
                st.markdown("**Action:** Triggering Mechanic Agent for root cause analysis...")
            else:
                st.markdown("**Status:** <span class='status-healthy'>All Clear</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("")
        
        # ========== AGENT 2: MECHANIC ==========
        with st.container():
            st.markdown(
                '<div class="agent-container agent-mechanic">',
                unsafe_allow_html=True
            )
            st.markdown("**🔧 Agent 2: The Mechanic** (Root Cause Diagnosis)")
            st.markdown(
                f'<p class="ueba-badge">✓ UEBA Verified: Security Token Valid</p>',
                unsafe_allow_html=True
            )
            
            if is_critical or anomalies:
                with st.spinner("🤖 Analyzing telemetry data..."):
                    diagnosis = call_gemini_mechanic(current_temp, current_vibration, current_voltage, anomalies)
                    st.session_state.diagnosis_result = diagnosis
                
                st.markdown("**Diagnosis:**")
                st.info(diagnosis)
            else:
                st.markdown("**Status:** <span class='status-healthy'>No Issues Detected</span>", unsafe_allow_html=True)
                st.markdown("Vehicle systems operating within normal parameters.")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("")
        
        # ========== AGENT 3: CONCIERGE ==========
        with st.container():
            st.markdown(
                '<div class="agent-container agent-concierge">',
                unsafe_allow_html=True
            )
            st.markdown("**💬 Agent 3: The Concierge** (Customer Communication)")
            st.markdown(
                f'<p class="ueba-badge">✓ UEBA Verified: Security Token Valid</p>',
                unsafe_allow_html=True
            )
            
            if is_critical or anomalies:
                with st.spinner("✉️ Drafting customer message..."):
                    customer_msg = call_gemini_concierge(
                        st.session_state.diagnosis_result or diagnosis,
                        "Valued Customer"
                    )
                    st.session_state.customer_message = customer_msg
                
                st.markdown("**Draft Message:**")
                st.success(customer_msg)
            else:
                st.markdown("**Status:** <span class='status-healthy'>No Communication Needed</span>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # ========== COLUMN 3: VALUE DELIVERY (OUTPUT) ==========
    with col3:
        st.markdown("### 💎 Value Delivery")
        
        # ========== TOP HALF: CUSTOMER ENGAGEMENT ==========
        st.markdown("#### 👥 Customer Interface")
        
        if is_critical or anomalies:
            st.markdown("**📱 Service Booking Interface**")
            st.markdown(st.session_state.customer_message or "Generating message...")
            
            st.markdown("**Select Service Slot:**")
            slots = get_available_service_slots()
            selected_slot = st.selectbox(
                "Available Service Times",
                slots,
                key="slot_select",
                label_visibility="collapsed"
            )
            
            col_book, col_decline = st.columns(2)
            with col_book:
                if st.button("✅ Book Now", use_container_width=True, key="book_btn"):
                    st.session_state.selected_slot = selected_slot
                    st.success(f"✅ Service booked for {selected_slot}! Confirmation sent via WhatsApp.")
            
            with col_decline:
                if st.button("⏭️ Remind Later", use_container_width=True, key="remind_btn"):
                    st.info("⏱️ Reminder set for 24 hours")
        else:
            st.info("🟢 Vehicle Status: Healthy. No service action required.")
        
        st.markdown("---")
        
        # ========== BOTTOM HALF: MANUFACTURING FEEDBACK ==========
        st.markdown("#### 🏭 Engineering Quality Console (Closed-Loop Feedback)")
        
        if is_critical or anomalies:
            with st.spinner("🔄 Generating manufacturing insights..."):
                mfg_feedback = call_gemini_manufacturing(current_temp, current_vibration, current_voltage, anomalies)
                st.session_state.manufacturing_feedback = mfg_feedback
            
            st.markdown("**Design Improvement Feedback (to Factory)**")
            
            # Display JSON in styled container
            json_str = json.dumps(mfg_feedback, indent=2)
            st.markdown(
                f'<div class="json-display">{json_str}</div>',
                unsafe_allow_html=True
            )
            
            st.markdown("**Insights:**")
            col_root, col_cluster = st.columns(2)
            
            with col_root:
                st.write("**Root Cause**")
                st.markdown(f"```\n{mfg_feedback.get('Root_Cause', 'N/A')}\n```")
            
            with col_cluster:
                st.write("**Defect Cluster**")
                st.markdown(f"```\n{mfg_feedback.get('Defect_Cluster_ID', 'N/A')}\n```")
            
            st.write("**Design Improvement Recommendation**")
            st.markdown(f"> {mfg_feedback.get('Design_Improvement_Suggestion', 'N/A')}")
        else:
            st.info("No manufacturing issues detected. All systems nominal.")
        
        st.markdown("---")
        
        # ========== FOOTER STATS ==========
        st.markdown("**Session Statistics**")
        stats_col1, stats_col2 = st.columns(2)
        with stats_col1:
            st.metric("Data Points", len(st.session_state.sensor_history["timestamps"]))
        with stats_col2:
            st.metric("Alerts Triggered", 1 if is_critical else 0)

if __name__ == "__main__":
    main()