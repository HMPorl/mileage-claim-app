"""
Mileage Claim Application
A Streamlit web application for employees to submit mileage claims for reimbursement
Built using established patterns from the Net Rates Calculator
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional
import uuid

# -------------------------------
# Configuration Management
# -------------------------------
CONFIG_FILE = "config.json"

def load_config() -> Dict:
    """Load configuration from JSON file with default HMRC rates"""
    default_config = {
        "rates": {
            "car_rate_per_mile": 0.45,  # HMRC approved rate 2024/25
            "motorcycle_rate_per_mile": 0.24,
            "bicycle_rate_per_mile": 0.20
        },
        "business": {
            "company_name": "The Hireman",
            "finance_email": "finance@thehireman.co.uk",
            "currency_symbol": "£"
        }
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
    except Exception as e:
        st.warning(f"Error loading config, using defaults: {e}")
    
    return default_config

def save_config(config: Dict) -> bool:
    """Save configuration to JSON file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving config: {e}")
        return False

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(
    page_title="Mileage Claim App",
    page_icon="🚗",
    layout="wide"
)

# -------------------------------
# Security: PIN Authentication
# -------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Mileage Claim App - Access Required")
    st.markdown("### Please enter your credentials to access the application")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username_input = st.text_input("Username:", max_chars=10, placeholder="Enter username")
        pin_input = st.text_input("Enter PIN:", type="password", max_chars=4, placeholder="****")
        
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            if st.button("🔓 Access Application", type="primary", use_container_width=True):
                if username_input == "HM" and pin_input == "1985":
                    st.session_state.authenticated = True
                    st.session_state.current_user = username_input
                    st.success("✅ Access granted! Redirecting...")
                    st.rerun()
                else:
                    if username_input != "HM":
                        st.error("❌ Incorrect username. Please try again.")
                    elif pin_input != "1985":
                        st.error("❌ Incorrect PIN. Please try again.")
                    else:
                        st.error("❌ Incorrect credentials. Please try again.")
    
    st.markdown("---")
    st.info("💡 **Need access?** Contact your system administrator for the username and PIN.")
    st.stop()

# -------------------------------
# Initialize Session State
# -------------------------------
if "mileage_entries" not in st.session_state:
    st.session_state.mileage_entries = []

if "config" not in st.session_state:
    st.session_state.config = load_config()

# -------------------------------
# Main Application Header
# -------------------------------
st.title("🚗 Mileage Claim Application")
st.markdown("Submit your business mileage for reimbursement")

# -------------------------------
# Basic Mileage Entry Form
# -------------------------------
st.header("📝 Add New Mileage Claim")

config = st.session_state.config

with st.form("mileage_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        claim_date = st.date_input(
            "Date of Journey:",
            value=date.today(),
            max_value=date.today(),
            help="Select the date you made the journey"
        )
        
        from_location = st.text_input(
            "From Location:",
            placeholder="e.g., Home, Office, Client Site",
            help="Starting location of your journey"
        )
        
        miles = st.number_input(
            "Miles Traveled:",
            min_value=0.1,
            max_value=500.0,
            step=0.1,
            format="%.1f",
            help="Enter total miles for the journey"
        )
    
    with col2:
        vehicle_type = st.selectbox(
            "Vehicle Type:",
            options=["car", "motorcycle", "bicycle"],
            format_func=lambda x: {
                "car": f"🚗 Car (£{config['rates']['car_rate_per_mile']}/mile)",
                "motorcycle": f"🏍️ Motorcycle (£{config['rates']['motorcycle_rate_per_mile']}/mile)",
                "bicycle": f"🚴 Bicycle (£{config['rates']['bicycle_rate_per_mile']}/mile)"
            }[x],
            help="Select your vehicle type for correct rate calculation"
        )
        
        to_location = st.text_input(
            "To Location:",
            placeholder="e.g., Client Office, Meeting Venue",
            help="Destination of your journey"
        )
        
        purpose = st.text_area(
            "Business Purpose:",
            placeholder="e.g., Client meeting, Site visit, Training",
            help="Brief description of the business purpose"
        )
    
    # Calculate and display reimbursement
    if miles > 0:
        rate_key = f"{vehicle_type}_rate_per_mile"
        rate = config["rates"][rate_key]
        reimbursement = miles * rate
        
        st.info(f"💰 **Estimated Reimbursement:** {config['business']['currency_symbol']}{reimbursement:.2f} "
               f"({miles:.1f} miles × {config['business']['currency_symbol']}{rate:.2f}/mile)")
    
    submitted = st.form_submit_button("➕ Add Mileage Claim", type="primary")
    
    if submitted:
        if from_location and to_location and purpose and miles > 0:
            # Create new mileage entry
            entry = {
                "id": str(uuid.uuid4()),
                "date": claim_date.isoformat(),
                "from_location": from_location,
                "to_location": to_location,
                "miles": miles,
                "purpose": purpose,
                "vehicle_type": vehicle_type,
                "rate": rate,
                "reimbursement": reimbursement,
                "created_at": datetime.now().isoformat()
            }
            
            st.session_state.mileage_entries.append(entry)
            st.success(f"✅ Mileage claim added successfully! Reimbursement: {config['business']['currency_symbol']}{reimbursement:.2f}")
            st.rerun()
        else:
            st.error("❌ Please fill in all required fields and ensure miles is greater than 0")

# -------------------------------
# Display Existing Claims
# -------------------------------
if st.session_state.mileage_entries:
    st.header("📊 Your Mileage Claims")
    
    # Convert to DataFrame for display
    claims_data = []
    total_miles = 0
    total_reimbursement = 0
    
    for entry in st.session_state.mileage_entries:
        total_miles += entry["miles"]
        total_reimbursement += entry["reimbursement"]
        
        claims_data.append({
            "Date": entry["date"],
            "From": entry["from_location"],
            "To": entry["to_location"],
            "Miles": f"{entry['miles']:.1f}",
            "Vehicle": entry["vehicle_type"].title(),
            "Purpose": entry["purpose"],
            "Rate": f"{config['business']['currency_symbol']}{entry['rate']:.2f}",
            "Amount": f"{config['business']['currency_symbol']}{entry['reimbursement']:.2f}"
        })
    
    if claims_data:
        df = pd.DataFrame(claims_data)
        st.dataframe(df, use_container_width=True)
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Claims", len(claims_data))
        with col2:
            st.metric("Total Miles", f"{total_miles:.1f}")
        with col3:
            st.metric("Total Reimbursement", f"{config['business']['currency_symbol']}{total_reimbursement:.2f}")
        
        # Clear all claims button
        if st.button("🗑️ Clear All Claims", type="secondary"):
            st.session_state.mileage_entries = []
            st.success("✅ All claims cleared")
            st.rerun()

else:
    st.info("📝 No mileage claims yet. Add your first claim above!")

# -------------------------------
# Basic Help Section
# -------------------------------
with st.expander("📞 Help & Current Rates"):
    st.markdown(f"""
    ## Current Reimbursement Rates (HMRC Approved)
    - 🚗 **Car:** £{config['rates']['car_rate_per_mile']:.2f} per mile
    - 🏍️ **Motorcycle:** £{config['rates']['motorcycle_rate_per_mile']:.2f} per mile  
    - 🚴 **Bicycle:** £{config['rates']['bicycle_rate_per_mile']:.2f} per mile
    
    ## How to Use
    1. Enter the date of your business journey
    2. Specify start and end locations
    3. Input total miles traveled
    4. Select your vehicle type
    5. Describe the business purpose
    6. Submit to add to your claims
    
    ## Support
    📧 **Finance Team:** {config['business']['finance_email']}
    """)