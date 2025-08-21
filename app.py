import streamlit as st
import pandas as pd
import altair as alt

# --- Page Setup ---

st.set_page_config(page_title="Food Wastage Management Dashboard", page_icon="🍽️", layout="wide")
st.markdown(
    """
    <h1 style='font-size:56px; color:#FFA500;'>🍽️ Food Wastage Management Dashboard</h1>
    <p style='font-size:20px; margin-left:20px; color:#CCCCCC;'>Interactive dashboard powered by CSV + Streamlit</p>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            min-width: 300px;
            max-width: 300px;
        }
    </style>
    """,
    unsafe_allow_html=True
)
# --- Theme (dark mode) ---
st.markdown(
    """
    <style>
    /* Main background */
    .stApp { background-color: #000000FF; }
    section[data-testid="stSidebar"] { background-color: #434343FF; }
    h1, h2, h3, h4 { color: #FFA500; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Load Data ---
@st.cache_data
def load_data():
    providers = pd.read_csv("data/providers_data.csv")
    receivers = pd.read_csv("data/receivers_data.csv")
    food_listings = pd.read_csv("data/food_listings_data.csv")
    claims_data = pd.read_csv("data/claims_data.csv")
    return providers, receivers, food_listings, claims_data

providers, receivers, food_listings, claims_data = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filters")

cities = ["All"] + sorted(providers["City"].dropna().astype(str).unique())
city_choice = st.sidebar.selectbox("City (providers)", options=cities, index=0)

if not claims_data.empty:
    claims_data["Timestamp"] = pd.to_datetime(claims_data["Timestamp"], errors="coerce")
    min_ts, max_ts = claims_data["Timestamp"].min(), claims_data["Timestamp"].max()
else:
    min_ts, max_ts = None, None

date_range = None
if min_ts and max_ts:
    date_range = st.sidebar.date_input(
        "Claim date range (optional)",
        value=(min_ts.date(), max_ts.date()),
        min_value=min_ts.date(),
        max_value=max_ts.date()
    )

# Filtered claims
claims_filtered = claims_data.copy()
if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
    claims_filtered = claims_filtered[
        (claims_filtered["Timestamp"].dt.date >= date_range[0]) &
        (claims_filtered["Timestamp"].dt.date <= date_range[1])
    ]

st.markdown("---")

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Providers", len(providers))
with col2:
    st.metric("Total Receivers", len(receivers))
with col3:
    st.metric("Total Listings", len(food_listings))
with col4:
    st.metric("Total Quantity Available", int(food_listings["Quantity"].sum()))

st.markdown("---")

# --- Question Dropdown ---
question_list = [
    "1. Providers & Receivers by City",
    "2. Quantity by Provider Type",
    "3. Provider Contacts by City",
    "4. Top Receivers by Claims",
    "5. Total Quantity Available",
    "6. Food Listings by City",
    "7. Most Common Food Types",
    "8. Claims per Food Item",
    "9. Top Providers by Successful Claims",
    "10. Claim Status Distribution",
    "11. Average Quantity Claimed per Receiver",
    "12. Most Claimed Meal Types",
    "13. Total Quantity Donated by Provider"
]
selected_question = st.selectbox("Select Question to View", question_list, index=0)
st.markdown("---")

# Q1
if selected_question == "1. Providers & Receivers by City":
    df1 = providers.groupby("City").size().reset_index(name="providers")
    df2 = receivers.groupby("City").size().reset_index(name="receivers")
    pr_city_df = pd.merge(df1, df2, on="City", how="outer").fillna(0)
    st.dataframe(pr_city_df, use_container_width=True)
    pr_long = pr_city_df.melt(id_vars="City", var_name="role", value_name="count")
    chart = alt.Chart(pr_long).mark_bar().encode(
        x="City:N", y="count:Q", color="role:N"
    ).properties(height=320)
    st.altair_chart(chart, use_container_width=True)
    st.info("**Insight:** This chart compares the number of providers and receivers across different cities. A higher number of providers in a city indicates strong food donation potential, whereas a higher number of receivers highlights greater demand for food assistance. Cities where both numbers are balanced suggest efficient local redistribution systems. However, cities with a mismatch—such as more providers than receivers or vice versa—may face challenges in food logistics and accessibility. This information helps NGOs and policymakers identify where to strengthen partnerships. For example, cities with many receivers but fewer providers might need food transportation support, while cities with more providers could benefit from improved receiver outreach. Ultimately, this analysis ensures that surplus food supply aligns better with community needs, reducing wastage and hunger simultaneously.")

# Q2
if selected_question == "2. Quantity by Provider Type":
    qty_by_type = food_listings.groupby("Provider_Type")["Quantity"].sum().reset_index()
    st.dataframe(qty_by_type, use_container_width=True)
    chart2 = alt.Chart(qty_by_type).mark_bar().encode(
        x="Provider_Type:N", y="Quantity:Q"
    ).properties(height=320)
    st.altair_chart(chart2, use_container_width=True)
    st.info("**Insight:** This analysis shows how much total food quantity comes from different provider types, such as households, restaurants, hotels, or supermarkets. By identifying which provider category donates the most, organizations can focus on strengthening collaboration with that segment. For example, if restaurants contribute the bulk of donations, then campaigns to encourage more restaurant participation will have the largest impact. Conversely, if households contribute significantly, awareness drives could focus on encouraging individuals to donate surplus food instead of letting it go to waste. Tracking provider types also helps design tailored policies—restaurants may need incentives for donating leftover meals, while households may require more accessible donation drop-off points. This insight ensures that interventions are data-driven, maximizing efficiency in reducing food wastage.")
    
# Q3
if selected_question == "3. Provider Contacts by City":
    contacts_df = providers.copy()
    if city_choice != "All":
        contacts_df = contacts_df[contacts_df["City"] == city_choice]
    st.dataframe(contacts_df[["Name", "Contact"]], use_container_width=True)
    st.info("**Insight:** This dataset shows the list of providers in each city along with their contact details. Having provider contact information readily available is critical for operational efficiency in food redistribution. For example, NGOs or food banks can quickly reach out to providers in specific cities when shortages arise or during emergencies. This also fosters direct communication, making it easier to schedule pickups, verify food safety, and strengthen collaboration. Cities with many providers indicate strong networks, while those with fewer may require outreach programs to build new partnerships. Overall, this insight improves coordination by ensuring that food does not remain unused at the provider level due to communication gaps.")
    
# Q4
if selected_question == "4. Top Receivers by Claims":
    df = claims_filtered.merge(receivers, on="Receiver_ID", how="left")
    df = df.merge(food_listings, on="Food_ID", how="left")
    top_receivers = df.groupby("Name").agg(
        claim_count=("Claim_ID", "count"),
        approx_total_qty=("Quantity", "sum")
    ).reset_index().sort_values(["claim_count", "approx_total_qty"], ascending=False).head(20)
    st.dataframe(top_receivers, use_container_width=True)
    chart3 = alt.Chart(top_receivers).mark_bar().encode(
        x="Name:N", y="claim_count:Q"
    ).properties(height=320)
    st.altair_chart(chart3, use_container_width=True)
    st.info("**Insight:** This chart ranks receivers based on the number of claims they have made, along with the approximate quantity of food claimed. High-claim receivers represent organizations or groups with large food needs, such as community kitchens, orphanages, or shelters. Tracking these helps providers and NGOs understand where demand is concentrated. If a small number of receivers consistently claim most donations, this could indicate reliance on surplus food for their operations. On the other hand, low-claim receivers may face barriers such as limited transportation or lack of awareness. Insights from this analysis help ensure fair distribution by balancing food between high- and low-claim receivers.")
        
# Q5
if selected_question == "5. Total Quantity Available":
    st.metric("Total Available Quantity", int(food_listings["Quantity"].sum()))
    st.info("**Insight:** This metric shows the total amount of food currently available across all providers and listings. It serves as a real-time indicator of donation capacity in the system. High total availability indicates that providers are actively contributing and that supply is strong. However, if food is not claimed quickly, wastage risk increases due to spoilage. On the other hand, low availability may suggest fewer active providers, reduced donations, or seasonal variations. Monitoring this figure helps NGOs align logistics—high supply requires faster transportation, while low supply means prioritizing high-need receivers. In short, this measure provides a snapshot of the ecosystem’s health and efficiency.")

# Q6
if selected_question == "6. Food Listings by City":
    listings_city = food_listings.merge(providers, on="Provider_ID", how="left")
    listings_city = listings_city.groupby("City")["Food_ID"].count().reset_index(name="total_listings")
    st.dataframe(listings_city, use_container_width=True)
    chart4 = alt.Chart(listings_city).mark_bar().encode(
        x="City:N", y="total_listings:Q"
    ).properties(height=320)
    st.altair_chart(chart4, use_container_width=True)
    st.info("**Insight:** This visualization shows how many food listings each city has. Cities with more listings indicate strong participation by providers and a higher chance of redistributing surplus food effectively. Conversely, cities with fewer listings may face challenges such as weaker provider networks, logistical issues, or lack of awareness about donation programs. This information is crucial for identifying geographical gaps in the food redistribution network. For example, if a major urban center shows unexpectedly low listings, it signals the need for outreach campaigns. By analyzing city-wise trends, organizations can better allocate resources and design interventions that maximize impact.")
    
# Q7
if selected_question == "7. Most Common Food Types":
    types_df = food_listings.groupby("Food_Type").size().reset_index(name="total_items")
    st.dataframe(types_df, use_container_width=True)
    chart5 = alt.Chart(types_df).mark_bar().encode(
        x="Food_Type:N", y="total_items:Q"
    ).properties(height=320)
    st.altair_chart(chart5, use_container_width=True)
    st.info("**Insight:** This analysis highlights the most frequently donated food categories. Understanding common food types helps in managing storage and distribution better. For example, perishable items like cooked meals require faster delivery systems, while packaged goods may have longer shelf lives. A concentration of donations in certain categories could indicate surplus patterns—for instance, bakeries might contribute more bread while households donate cooked meals. Conversely, less frequent categories could point to unmet nutritional needs. Having this breakdown ensures balanced food distribution, reduces spoilage risk, and helps in planning storage infrastructure (e.g., cold storage for perishables). ")
    
# Q8
if selected_question == "8. Claims per Food Item":
    df = claims_filtered.merge(food_listings, on="Food_ID", how="left")
    claims_per_food = df.groupby("Food_Name")["Claim_ID"].count().reset_index(name="total_claims")
    claims_per_food = claims_per_food.sort_values("total_claims", ascending=False).head(30)
    st.dataframe(claims_per_food, use_container_width=True)
    chart6 = alt.Chart(claims_per_food).mark_bar().encode(
        x="Food_Name:N", y="total_claims:Q"
    ).properties(height=320)
    st.altair_chart(chart6, use_container_width=True)
    st.info("**Insight:** This chart shows which specific food items are most frequently claimed by receivers. High-claim foods are often essential items in diets, such as rice, bread, or cooked meals, indicating strong demand. On the other hand, low-claim foods may reflect lower utility, dietary restrictions, or short shelf life. Understanding these patterns allows providers to better align their donations with actual needs, ensuring minimal wastage. Additionally, this helps NGOs anticipate which items require faster redistribution systems. For example, if perishable meals are among the most claimed, they must be delivered quickly to avoid spoilage.")
    
# Q9
if selected_question == "9. Top Providers by Successful Claims":
    df = claims_filtered[claims_filtered["Status"] == "Completed"]
    df = df.merge(food_listings, on="Food_ID", how="left")
    df = df.merge(providers, on="Provider_ID", how="left")
    provider_success = df.groupby("Name")["Claim_ID"].count().reset_index(name="successful_claims")
    provider_success = provider_success.sort_values("successful_claims", ascending=False).head(20)
    st.dataframe(provider_success, use_container_width=True)
    chart7 = alt.Chart(provider_success).mark_bar().encode(
        x="Name:N", y="successful_claims:Q"
    ).properties(height=320)
    st.altair_chart(chart7, use_container_width=True)
    st.info("**Insight:** This analysis highlights providers whose donations are most frequently claimed and completed. Such providers play a critical role in ensuring smooth redistribution. They may be located near receivers, donate highly demanded food types, or maintain consistent donation schedules. Recognizing these providers encourages continued participation and builds trust in the system. Conversely, providers with fewer successful claims may need logistical support or awareness programs. By identifying top performers, this insight helps build stronger partnerships and ensures that food surplus effectively reaches those in need.")
    
# Q10
if selected_question == "10. Claim Status Distribution":
    status_df = claims_filtered.groupby("Status").size().reset_index(name="cnt")
    status_df["percentage"] = (status_df["cnt"] / status_df["cnt"].sum()) * 100
    st.dataframe(status_df, use_container_width=True)
    chart8 = alt.Chart(status_df).mark_arc().encode(
        theta="cnt:Q", color="Status:N", tooltip=["Status", "cnt", "percentage"]
    ).properties(height=320)
    st.altair_chart(chart8, use_container_width=True)
    st.info("**Insight:** This pie chart shows the distribution of claim statuses (e.g., pending, completed, cancelled). A high percentage of completed claims indicates that the system is functioning efficiently. However, a large share of pending or cancelled claims suggests bottlenecks in logistics, communication, or matching between providers and receivers. For example, cancellations may occur if food spoils before pickup, while pending claims could indicate resource shortages. Monitoring claim statuses helps identify operational weaknesses and areas where technology, transportation, or awareness efforts can improve success rates.")
    
# Q11
if selected_question == "11. Average Quantity Claimed per Receiver":
    df = claims_filtered.merge(receivers, on="Receiver_ID", how="left")
    df = df.merge(food_listings, on="Food_ID", how="left")
    avg_claim = df.groupby("Name")["Quantity"].mean().reset_index(name="avg_qty_claimed")
    avg_claim = avg_claim.sort_values("avg_qty_claimed", ascending=False).head(20)
    st.dataframe(avg_claim, use_container_width=True)
    chart9 = alt.Chart(avg_claim).mark_bar().encode(
        x="Name:N", y="avg_qty_claimed:Q"
    ).properties(height=320)
    st.altair_chart(chart9, use_container_width=True)
    st.info("**Insight:** This metric highlights which receivers claim the largest average food quantities. High averages often indicate institutions like schools, shelters, or community kitchens that serve many people. On the other hand, low averages may represent smaller organizations or individual receivers. This insight helps balance food allocation—large receivers may need bulk deliveries, while small receivers might require smaller, more frequent support. It also helps ensure equity, preventing large receivers from dominating the system at the expense of smaller ones. Ultimately, this promotes fairness in food distribution while reducing wastage.")
    
# Q12
if selected_question == "12. Most Claimed Meal Types":
    df = claims_filtered.merge(food_listings, on="Food_ID", how="left")
    meal_claim = df.groupby("Meal_Type")["Claim_ID"].count().reset_index(name="total_claims")
    st.dataframe(meal_claim, use_container_width=True)
    chart10 = alt.Chart(meal_claim).mark_bar().encode(
        x="Meal_Type:N", y="total_claims:Q"
    ).properties(height=320)
    st.altair_chart(chart10, use_container_width=True)
    st.info("**Insight:** This analysis shows which meal types (breakfast, lunch, dinner, snacks) are most frequently claimed. High demand for specific meals may reflect cultural patterns or operational needs of receivers. For example, lunch and dinner may be claimed more by shelters and community kitchens, while breakfast might be common for schools. Understanding meal preferences allows providers to tailor donations, ensuring food is useful and consumed rather than wasted. This insight also helps optimize storage and delivery, since meal timings directly affect when and how food should be transported.")
    
# Q13
if selected_question == "13. Total Quantity Donated by Provider":
    df = food_listings.merge(providers, on="Provider_ID", how="left")
    donated = df.groupby("Name")["Quantity"].sum().reset_index(name="total_donated")
    donated = donated.sort_values("total_donated", ascending=False).head(30)
    st.dataframe(donated, use_container_width=True)
    chart11 = alt.Chart(donated).mark_bar().encode(
        x="Name:N", y="total_donated:Q"
    ).properties(height=320)
    st.altair_chart(chart11, use_container_width=True)
    st.info("**Insight:** This chart ranks providers based on total donation quantity. High-donating providers play a crucial role in sustaining the food redistribution ecosystem. Recognizing and rewarding them can encourage further contributions. On the other hand, providers with smaller donation volumes may need encouragement or logistical support to increase participation. This analysis helps identify key players in reducing food wastage and highlights opportunities to expand the network. By building stronger relationships with top donors, NGOs and policymakers can ensure a steady supply of food while also encouraging broader participation.")
st.markdown(
    "<p style='font-size:23px;color:#F3F3F3FF; font-weight:bold;'>Food Wastage Management Dashboard — Empowering Data-Driven Decisions. | Created by Ayushi Kanojiya</p>",
    unsafe_allow_html=True
)