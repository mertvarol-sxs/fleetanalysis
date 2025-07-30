
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Initialize session state for fleet data
if 'fleet' not in st.session_state:
    st.session_state.fleet = pd.DataFrame(columns=[
        'registration', 'MSN', 'manufactured_date', 'lease_type',
        'ac_type', 'ac_variant', 'fleet_in_date', 'fleet_out_date',
        'next_c_check_date', 'ownership_change_date'
    ])

# Helper function to calculate lease type at a given date
def get_lease_type_at_t(row, t_date):
    if row['lease_type'] == 'finance' and pd.notnull(row['ownership_change_date']) and row['ownership_change_date'] <= t_date:
        return 'own'
    return row['lease_type']

# Helper function to calculate age at a given date
def get_age_at_t(row, t_date):
    if pd.isnull(row['manufactured_date']):
        return None
    return round((t_date - row['manufactured_date']).days / 365.25, 2)

# Title
st.title("Fleet Scenario Management App")

# Sidebar for scenario date
scenario_date = st.sidebar.date_input("Select Scenario Date", value=datetime.today())

# Section: Add Aircraft
st.header("➕ Add Aircraft to Fleet")
with st.form("add_aircraft_form"):
    registration = st.text_input("Registration")
    msn = st.text_input("MSN")
    manufactured_date = st.date_input("Manufactured Date")
    lease_type = st.selectbox("Lease Type", ["own", "finance", "operating"])
    ac_type = st.text_input("Aircraft Type (e.g. A320)")
    ac_variant = st.text_input("Aircraft Variant (e.g. A320-200)")
    fleet_in_date = st.date_input("Fleet-In Date")
    fleet_out_date = st.date_input("Fleet-Out Date (optional)", value=None)
    next_c_check_date = st.date_input("Next C-Check Date (optional)", value=None)
    submitted = st.form_submit_button("Add Aircraft")

    if submitted:
        ownership_change_date = None
        if lease_type == 'finance':
            ownership_change_date = manufactured_date + timedelta(days=int(365.25 * 10))
        new_row = {
            'registration': registration,
            'MSN': msn,
            'manufactured_date': manufactured_date,
            'lease_type': lease_type,
            'ac_type': ac_type,
            'ac_variant': ac_variant,
            'fleet_in_date': fleet_in_date,
            'fleet_out_date': fleet_out_date,
            'next_c_check_date': next_c_check_date,
            'ownership_change_date': ownership_change_date
        }
        st.session_state.fleet = pd.concat([st.session_state.fleet, pd.DataFrame([new_row])], ignore_index=True)
        st.success(f"Aircraft {registration} added to fleet.")

# Section: Remove Aircraft
st.header("➖ Remove Aircraft from Fleet")
if not st.session_state.fleet.empty:
    reg_to_remove = st.selectbox("Select Aircraft to Remove", st.session_state.fleet['registration'])
    if st.button("Remove Aircraft"):
        st.session_state.fleet = st.session_state.fleet[st.session_state.fleet['registration'] != reg_to_remove]
        st.success(f"Aircraft {reg_to_remove} removed from fleet.")

# Section: Fleet Status at Scenario Date
st.header(f"📊 Fleet Status on {scenario_date}")
if not st.session_state.fleet.empty:
    fleet = st.session_state.fleet.copy()
    fleet['lease_type_at_t'] = fleet.apply(lambda row: get_lease_type_at_t(row, scenario_date), axis=1)
    fleet['age_at_t'] = fleet.apply(lambda row: get_age_at_t(row, scenario_date), axis=1)
    fleet_active = fleet[(fleet['fleet_in_date'] <= scenario_date) & 
                         ((fleet['fleet_out_date'].isnull()) | (fleet['fleet_out_date'] > scenario_date))]
    avg_age = round(fleet_active['age_at_t'].mean(), 2) if not fleet_active.empty else 0.0

    st.subheader(f"Average Age of Active Fleet: {avg_age} years")
    st.dataframe(fleet_active[['registration', 'ac_type', 'ac_variant', 'lease_type_at_t', 'age_at_t']])
else:
    st.info("Fleet is currently empty. Please add aircraft to begin.")

