import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# Initialize session state
if 'fleet' not in st.session_state:
    st.session_state.fleet = pd.DataFrame(columns=[
        'registration', 'msn', 'manufactured_date', 'lease_type',
        'ac_type', 'ac_variant', 'fleet_in_date', 'fleet_out_date',
        'next_c_check_date', 'ownership_change_date'
    ])

# Helper function to calculate age
def calculate_age(row, scenario_date):
    if pd.isnull(row['manufactured_date']):
        return None
    delta = scenario_date - row['manufactured_date']
    return round(delta.days / 365.25, 2)

# Helper function to determine lease type at scenario date
def lease_type_at(row, scenario_date):
    if row['lease_type'] == 'finance' and pd.notnull(row['ownership_change_date']):
        return 'own' if scenario_date >= row['ownership_change_date'] else 'finance'
    return row['lease_type']

# Sidebar: Scenario Date
st.sidebar.markdown("### Scenario Date")
scenario_date = st.sidebar.date_input("Select scenario date", datetime.date.today())

# Tabs
tab1, tab2, tab3 = st.tabs(["Add Aircraft", "Remove Aircraft", "Overview"])

with tab1:
    st.subheader("Add Aircraft to Fleet")

    col1, col2, col3 = st.columns(3)
    with col1:
        registration = st.text_input("Registration")
        msn = st.text_input("MSN")
        manufactured_date = st.date_input("Manufactured Date")
    with col2:
        lease_type = st.selectbox("Lease Type", ["financial", "operational", "own"])
        ac_type = st.selectbox("Aircraft Type", ["Boeing 737", "Airbus 320", "Airbus 321", "Others"])
        if ac_type == "Boeing 737":
            variants = ["B737-800NG", "B737-8", "B737-9", "B737-10", "Others"]
        elif ac_type == "Airbus 320":
            variants = ["A320ceo", "A320neo", "Others"]
        elif ac_type == "Airbus 321":
            variants = ["A321ceo", "A321neo", "Others"]
        else:
            variants = ["Others"]
        ac_variant = st.selectbox("Variant", variants)
    with col3:
        fleet_in_date = st.date_input("Fleet-In Date")
        fleet_out_date = st.date_input("Fleet-Out Date", value=None)
        next_c_check_date = st.date_input("Next C-Check Date")

    if st.button("Add Aircraft"):
        ownership_change_date = None
        if lease_type == "financial":
            ownership_change_date = manufactured_date + datetime.timedelta(days=365*10)
        new_row = pd.DataFrame([{
            'registration': registration,
            'msn': msn,
            'manufactured_date': manufactured_date,
            'lease_type': lease_type,
            'ac_type': ac_type,
            'ac_variant': ac_variant,
            'fleet_in_date': fleet_in_date,
            'fleet_out_date': fleet_out_date,
            'next_c_check_date': next_c_check_date,
            'ownership_change_date': ownership_change_date
        }])
        st.session_state.fleet = pd.concat([st.session_state.fleet, new_row], ignore_index=True)
        st.success(f"Aircraft {registration} added to fleet.")

with tab2:
    st.subheader("Remove Aircraft from Fleet")
    if st.session_state.fleet.empty:
        st.info("Fleet is empty.")
    else:
        active_fleet = st.session_state.fleet[st.session_state.fleet['fleet_out_date'].isnull()]
        if active_fleet.empty:
            st.info("No active aircraft to remove.")
        else:
            selected_reg = st.selectbox("Select aircraft to remove", active_fleet['registration'])
            removal_date = st.date_input("Fleet-Out Date for removal")
            if st.button("Remove Aircraft"):
                idx = st.session_state.fleet[st.session_state.fleet['registration'] == selected_reg].index[0]
                st.session_state.fleet.at[idx, 'fleet_out_date'] = removal_date
                st.success(f"Aircraft {selected_reg} removed from fleet on {removal_date}.")

with tab3:
    st.subheader("Fleet Overview")

    if st.session_state.fleet.empty:
        st.info("Fleet is empty.")
    else:
        df = st.session_state.fleet.copy()
        df['lease_type_at_t'] = df.apply(lambda row: lease_type_at(row, scenario_date), axis=1)
        df['age_at_t'] = df.apply(lambda row: calculate_age(row, scenario_date), axis=1)
        df['active_at_t'] = df.apply(lambda row: row['fleet_in_date'] <= scenario_date and (pd.isnull(row['fleet_out_date']) or row['fleet_out_date'] > scenario_date), axis=1)
        active_df = df[df['active_at_t']]

        # Line chart: 10-year projection
        st.markdown("#### 10-Year Average Age Projection")
        projection_years = list(range(scenario_date.year, scenario_date.year + 11))
        avg_ages = []
        for year in projection_years:
            date = datetime.date(year, scenario_date.month, scenario_date.day)
            df['age_proj'] = df.apply(lambda row: calculate_age(row, date), axis=1)
            df['active_proj'] = df.apply(lambda row: row['fleet_in_date'] <= date and (pd.isnull(row['fleet_out_date']) or row['fleet_out_date'] > date), axis=1)
            avg_age = df[df['active_proj']]['age_proj'].mean()
            avg_ages.append(avg_age)

        fig, ax = plt.subplots()
        ax.plot(projection_years, avg_ages, marker='o', label='Projected Avg Age')
        ax.set_ylabel("Average Age (years)")
        ax.set_xlabel("Year")
        ax.set_title("Fleet Age Projection")
        ax.legend()
        st.pyplot(fig)

        # Pie chart: Lease type distribution
        st.markdown("#### Lease Type Distribution")
        lease_counts = active_df['lease_type_at_t'].value_counts()
        fig1, ax1 = plt.subplots()
        ax1.pie(lease_counts, labels=lease_counts.index, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        st.pyplot(fig1)

        # Pie chart: Type + Variant distribution
        st.markdown("#### Aircraft Type + Variant Distribution")
        type_variant = active_df['ac_type'] + " / " + active_df['ac_variant']
        type_variant_counts = type_variant.value_counts()
        fig2, ax2 = plt.subplots()
        ax2.pie(type_variant_counts, labels=type_variant_counts.index, autopct='%1.1f%%', startangle=90)
        ax2.axis('equal')
        st.pyplot(fig2)

