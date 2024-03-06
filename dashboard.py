"""Streamlit Dashboard."""

from datetime import datetime
from os import environ
import time

import bcrypt
from extra_streamlit_components.CookieManager import CookieManager
import pandas as pd
import pydeck as pdk
from pydeck.data_utils import compute_view
from pymongo import MongoClient
from pymongo.collection import Collection
import streamlit as st
from streamlit_lottie import st_lottie
from st_keyup import st_keyup

from config import AIRPORTS_DATA, STATIONS_DATA, CAR_SIZE_DATA
from extract import is_valid_postcode, get_car_db_data, get_rail_db_data, get_flight_db_data
from visuals import (
    get_carbon_pie,
    get_car_train_bar,
    get_transport_avgs,
    get_transport_avg_km,
    get_transport_donut,
    get_journey_map
)

TRANSPORT_EMOJIS = {'car': '🚗', 'rail': '🚝', 'air': '✈️'}

TRAVEL_OPTIONS = ['Car 🚗', 'Train 🚝', 'Flight ✈️']

CAR_TYPES = {'Petrol': 'petrol', 'Diesel': 'diesel',
             'Electric': 'battery', 'Hybrid': 'hybrid', 'Plug-in Hybrid': 'plugin_hybrid', 'Unsure': 'average'}

CAR_SIZES = {'Small': 'small', 'Medium': 'medium',
             'Large': 'large', 'Unsure': 'average'}

CABIN_CLASSES = {'Economy': 'economy', 'First Class': 'first',
                 'Business Class': 'business', 'Unsure': 'average'}


def set_cookies(cookie_manager: CookieManager, username: str) -> None:
    """Sets cookies after logging in."""

    cookie_manager.set('logged_in', True, max_age=86400, key='logged_in')
    cookie_manager.set('username', username, max_age=86400, key='username')


def clear_cookies(cookie_manager: CookieManager) -> None:
    """Clears cookies after logging out."""

    cookie_manager.delete('logged_in', key='logged_in')
    cookie_manager.delete('username', key='username')


def get_stations(search: str, stations: list) -> list:
    """Returns a list of stations containing the search term."""

    return [s for s in stations if search.lower() in s.lower()] if search else []


def submit_and_clear_rail():
    """Inserts the rail form data into the database and resets the form."""

    origin_station = st.session_state.origin_station
    dest_station = st.session_state.dest_station

    journey_data = get_rail_db_data(
        origin_station, dest_station, STATIONS_DATA)

    user_id = st.session_state.user_id

    journey_data = journey_data | {
        "user_id": user_id, "submitted_at": datetime.now()}

    journey_collection: Collection = st.session_state.journey_coll

    journey_collection.insert_one(journey_data)

    st.sidebar.success("Submitted!", icon="✅")

    st.session_state.journey = journey_data

    st.session_state['travel_mode'] = None


def submit_and_clear_car():
    """Inserts the car form data into the database and resets the form."""

    origin_postcode = st.session_state.origin_postcode
    dest_postcode = st.session_state.dest_postcode
    car_size = st.session_state.car_size
    car_type = st.session_state.car_type
    car_details = {
        'car_size': CAR_SIZES[car_size], 'car_type': CAR_TYPES[car_type]}

    journey_data = get_car_db_data(
        origin_postcode, dest_postcode, car_details)

    user_id = st.session_state.user_id

    journey_data = journey_data | {
        "user_id": user_id, "submitted_at": datetime.now()}

    journey_collection: Collection = st.session_state.journey_coll

    journey_collection.insert_one(journey_data)

    st.sidebar.success("Submitted!", icon="✅")

    st.session_state.journey = journey_data
    st.session_state['travel_mode'] = None


def submit_and_clear_air():
    """Inserts the air form data into the database and resets the form."""

    origin_airport = st.session_state.origin_airport
    dest_airport = st.session_state.dest_airport
    cabin_class = CABIN_CLASSES[st.session_state.cabin_class]

    journey_data = get_flight_db_data(
        origin_airport, dest_airport, cabin_class, AIRPORTS_DATA)

    user_id = st.session_state.user_id

    journey_data = journey_data | {
        "user_id": user_id, "submitted_at": datetime.now()}

    journey_collection: Collection = st.session_state.journey_coll

    journey_collection.insert_one(journey_data)

    st.sidebar.success("Submitted!", icon="✅")

    st.session_state.journey = journey_data
    st.session_state['travel_mode'] = None


def validate_username(username: str, collection: Collection) -> bool:
    """Checks whether the username already exists."""

    if collection.find_one({"username": username}):
        return False
    return True


def insert_user(username: str, password: str, collection: Collection) -> None:
    """Inserts user data into the MongoDB collection."""

    collection.insert_one({"username": username, "password": password})


def authenticate_user(username: str, password: str, collection: Collection) -> bool:
    """Checks if the user's details are correct."""

    user = collection.find_one({"username": username})

    if user and bcrypt.checkpw(password.encode(), user['password']):
        return True
    return False


def login(collection: Collection, cookie_manager: CookieManager) -> None:
    """Somet."""

    with st.form("Login", clear_on_submit=True):
        st.subheader("Login")

        username = st.text_input(
            'Username', placeholder="Enter a username")
        password = st.text_input(
            'Password', placeholder="Enter your password", type='password')

        if authenticate_user(username, password, collection):
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            set_cookies(cookie_manager, username)
            time.sleep(1)
            st.rerun()
        elif username and password:
            st.error("Incorrect Username or Password")

        st.form_submit_button("Login")


# def render_login() -> tuple:
#     """Renders the login form."""

#     st.subheader("Login")

#     username = st.text_input(
#         'Username', placeholder="Enter a username")
#     password = st.text_input(
#         'Password', placeholder="Enter your password", type='password')

    # return username, password


# def handle_login(username: str, password: str, collection: Collection) -> None:
#     """Handles the login authentication."""

#     if authenticate_user(username, password, collection):
#         st.session_state['logged_in'] = True
#         st.session_state['username'] = username
#         st.rerun()
#     elif st.session_state.tried_login:
#         st.error("Incorrect username or password")
#     else:
#         st.session_state.tried_login = True


def sign_up(collection: Collection) -> None:
    """A sign up form."""

    with st.form(key='signup', clear_on_submit=True):
        st.subheader(":green[Sign Up]")
        username = st.text_input(
            'Username', placeholder="Enter a username")
        password = st.text_input(
            'Password', placeholder="Enter your password", type='password')
        conf_password = st.text_input(
            'Confirm Password', placeholder='Please confirm your password', type='password')

        if username:
            if validate_username(username, collection):
                if password:
                    if password == conf_password:
                        hash_password = bcrypt.hashpw(
                            password.encode(), bcrypt.gensalt())
                        insert_user(username, hash_password, collection)
                        st.success("Account created successfully!")

                    else:
                        st.warning("Passwords do not match!")
                else:
                    st.warning("Please enter a password")
            else:
                st.warning("Username is already taken!")

        st.form_submit_button('Sign Up')


def render_login_page(user_collection: Collection, cookie_manager: CookieManager) -> None:
    """Renders the login page."""

    col1, col2 = st.columns(2)

    with col1:
        st.title(":green[Green]Route 🌱")
        st.markdown(
            """### Plan journeys around your :green[carbon footprint]""")
        subcol1, subcol2 = st.columns([0.15, 2])
        with subcol1:
            st.image("./images/climatiq_logo.png", width=25)

        with subcol2:
            st.write(
                "Data provided by **[Climatiq](https://www.climatiq.io/)**")

    with col2:

        st_lottie(
            "https://lottie.host/21cf136b-2ca0-4429-8ec6-cf19069235f5/BrvtJ7RHJJ.json", width=340, height=200)

    col1, col2 = st.columns(2)

    with col1:
        login(user_collection, cookie_manager)
    with col2:
        sign_up(user_collection)


def get_sorted_user_journeys(journey_collection: Collection, user_id: str) -> list:
    """Returns a list of journeys submitted by the user sorted by date in descending order."""

    journeys = list(journey_collection.find({"user_id": user_id}))

    sorted_journeys = sorted(
        journeys, key=lambda x: x['submitted_at'], reverse=True)

    return sorted_journeys


def get_journey_name(journey: dict) -> str:
    """Returns the name of the journey from its dictionary."""

    journey_emoji = TRANSPORT_EMOJIS[journey['transport']['type']]
    journey_origin = journey['origin']['name']
    journey_dest = journey['destination']['name']

    return f"{journey_emoji} {journey_origin} to {journey_dest}"


def render_car_form() -> None:
    """Renders the form for submitting a car journey."""

    origin_postcode = st_keyup(
        label="Origin Postcode", key='origin_postcode')

    if origin_postcode:
        if is_valid_postcode(origin_postcode):
            st.success("Postcode found!", icon="✅")
        else:
            st.warning("No postcode found", icon="🚨")

    destination_postcode = st_keyup(
        label='Destination Postcode', key='dest_postcode')

    if destination_postcode:
        if is_valid_postcode(destination_postcode):
            st.success("Postcode found!", icon="✅")
        else:
            st.warning("No postcode found", icon="🚨")

    car_size = st.selectbox('Select your car size:', options=[
                            'Small', 'Medium', 'Large', 'Unsure'], index=None, key='car_size')

    with st.expander("How big is my car?"):
        st.dataframe(CAR_SIZE_DATA, hide_index=True)
        st.write(
            'Data taken from https://www.climatiq.io/docs/api-reference/travel')

    car_type = st.selectbox('Select car type:', options=[
                            'Petrol', 'Diesel', 'Electric', 'Hybrid', 'Plug-in Hybrid', 'Unsure'
                            ], index=None, key='car_type')

    if origin_postcode and destination_postcode and is_valid_postcode(origin_postcode) and is_valid_postcode(destination_postcode) and car_size and car_type:

        st.button('Submit Journey', on_click=submit_and_clear_car)


def render_rail_form() -> None:
    """Renders the form for submitting a rail journey."""

    stations = STATIONS_DATA['stationName'].to_list()

    origin_station = st.selectbox(
        'Origin Station', options=stations, index=None, key='origin_station')

    destination_station = st.selectbox(
        'Destination Station', options=stations, index=None, key='dest_station')

    if origin_station and destination_station:

        st.button('Submit Journey', on_click=submit_and_clear_rail)


def render_air_form() -> None:
    """Renders the form for submitting an air journey."""

    airports = AIRPORTS_DATA['name']

    origin_airport = st.selectbox(
        'Origin Airport', options=airports, index=None, key='origin_airport'
    )

    destination_airport = st.selectbox(
        'Destination Airport', options=airports, index=None, key='dest_airport'
    )

    cabin_class = st.selectbox(
        'Cabin Class', options=['Economy', 'First Class', 'Business Class', 'Unsure'], index=None, key='cabin_class'
    )

    if origin_airport and destination_airport and cabin_class:

        st.button(
            'Submit Journey', on_click=submit_and_clear_air
        )


def render_sidebar(username: str) -> None:
    """Renders the sidebar."""

    with st.sidebar:

        st.title(":green[Green]Route 🌱")
        st.subheader(f"Welcome {username}!")

        st.divider()

        st.header('Enter Journey Details')

        transport = st.selectbox(
            'Mode of Transport', options=TRAVEL_OPTIONS, index=None, key='travel_mode')

        if transport == TRAVEL_OPTIONS[0]:

            render_car_form()

        if transport == TRAVEL_OPTIONS[1]:

            render_rail_form()

        if transport == TRAVEL_OPTIONS[2]:

            render_air_form()

        st.divider()

        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ''
            clear_cookies(cookie_manager)
            time.sleep(1)
            st.rerun()


def delete_journey() -> None:
    """Removes a journey from the db."""

    journey_collection: Collection = st.session_state.journey_coll
    user_id = st.session_state.user_id
    journey = st.session_state.journey

    journey_collection.delete_one(
        filter={'user_id': user_id, 'submitted_at': journey['submitted_at']})

    st.rerun()


def get_journeys_df(user_journeys: list) -> pd.DataFrame:
    """Returns a dataframe of the users journeys."""

    journeys_df = pd.DataFrame(user_journeys)

    journeys_df = journeys_df.join(pd.DataFrame(
        journeys_df.pop('transport').values.tolist()).rename(columns={'type': 'transport'}))

    journeys_df = journeys_df.join(pd.DataFrame(
        journeys_df.pop('origin').values.tolist()).rename(columns={'name': 'origin_name', 'lat': 'origin_lat', 'lon': 'origin_lon'}))

    journeys_df = journeys_df.join(pd.DataFrame(
        journeys_df.pop('destination').values.tolist()).rename(columns={'name': 'dest_name', 'lat': 'dest_lat', 'lon': 'dest_lon'}))

    journeys_df = journeys_df.join(pd.DataFrame(
        journeys_df.pop('co2e').values.tolist()))

    return journeys_df


if __name__ == "__main__":

    st.set_page_config(page_title="GreenRoute",
                       page_icon="🌱", layout='centered')

    cookie_manager = CookieManager()
    logged_in = cookie_manager.get('logged_in')

    cluster = MongoClient(environ['DB_URL'])
    db = cluster['eco_travel']
    user_collection = db['users']

    if logged_in:
        st.session_state.logged_in = True
    else:
        st.session_state.logged_in = False

    if "tried_login" not in st.session_state:
        st.session_state.tried_login = False

    if not st.session_state.get('logged_in'):

        render_login_page(user_collection, cookie_manager)

    else:

        username = cookie_manager.get('username')

        st.session_state['user_id'] = user_collection.find_one(
            {"username": username}).get("_id")

        render_sidebar(username)

        journey_collection = db['journeys']
        st.session_state.journey_coll = journey_collection

        if not journey_collection.find_one({"user_id": st.session_state.user_id}):
            # st_lottie(
            #     "https://lottie.host/37615ec4-3b66-404a-86ab-d1a75894690f/ha454AgqDi.json")
            st.subheader("Enter a journey to get started")

        else:

            user_journeys = get_sorted_user_journeys(
                journey_collection, st.session_state.user_id)

            latest_journey = user_journeys[0]

            journey_names = {get_journey_name(journey): journey['_id']
                             for journey in user_journeys
                             }

            col1, col2 = st.columns([1.3, 1])

            with col1:

                st.title(":green[Journey] Spotlight")

            with col2:

                journey_name = st.selectbox(
                    "Select a journey", options=journey_names.keys())
                if journey_name:
                    for j in user_journeys:
                        if j['_id'] == journey_names[journey_name]:
                            journey = j

                else:
                    journey = latest_journey

            st.session_state['journey'] = journey

            emoji = TRANSPORT_EMOJIS[journey['transport']['type']]

            journey_map = get_journey_map(journey)

            st.pydeck_chart(journey_map)

            col1, col2 = st.columns([4, 1.5])

            with col1:
                distance = round(journey['distance'], 2)
                journey_name = get_journey_name(journey)
                st.subheader(f"{journey_name} ({distance}km)")

            with col2:
                if emoji == TRANSPORT_EMOJIS['car']:
                    with st.expander("Car details"):
                        st.write(
                            f"**Car Size:** {journey['transport']['car_size'].capitalize()}")
                        st.write(
                            f"**Car Type:** {journey['transport']['car_type'].capitalize()}")
                if emoji == TRANSPORT_EMOJIS['air']:
                    with st.expander("Cabin details"):
                        st.write(
                            f"**Cabin Class:** {journey['transport']['cabin_class'].capitalize()}")

            total_co2e = round(journey['co2e']['total'], 2)

            co2e_per_kg = round(total_co2e / distance, 2)

            col1, col2 = st.columns([1.8, 1.5])

            with col1:
                subcol1, subcol2 = st.columns(2)
                with subcol1:
                    st.metric("Total CO2e Produced",
                              f"{total_co2e}kg")
                with subcol2:
                    st.metric("CO2e per km 📈", f"{co2e_per_kg}kg/km")
                with st.expander("That's the same as:", expanded=True):
                    excol1, excol2 = st.columns(2)
                    with excol1:
                        st.write(
                            "Using your washing machine")
                        st.subheader(
                            f"**:green[{round(total_co2e/0.6)} times]**")
                    with excol2:
                        st.image("./images/washing_machine.png")
                if emoji == TRANSPORT_EMOJIS['rail']:
                    with st.expander("How much have you saved?"):
                        subcol1, subcol2 = st.columns([1.2, 1])
                        with subcol2:
                            bar = get_car_train_bar(total_co2e)
                            st.altair_chart(bar, use_container_width=True)
                        with subcol1:
                            st.subheader(f"**:green[{total_co2e * 4}kg]**")
                            st.write(
                                "is how much more CO2 would be produced if you traveled by car")

                st.button("Delete Journey", on_click=delete_journey)

            with col2:

                pie = get_carbon_pie(journey)

                subcol1, subcol2 = st.columns([0.8, 2])

                with subcol2:

                    st.write("##### Emissions Breakdown")

                st.altair_chart(pie)

            st.divider()

            journeys_df = get_journeys_df(user_journeys)

            col1, col2 = st.columns([3, 1])

            with col1:
                st.title(":green[Summary] of Journeys")
            with col2:
                num_journeys = len(journeys_df.index)

                st.metric("Number of Journeys", num_journeys)

            col1, col2 = st.columns(2)

            with col1:

                st.subheader("Transport Breakdown")

                transport_donut = get_transport_donut(journeys_df)
                st.altair_chart(transport_donut, use_container_width=True)

            with col2:
                total = round(journeys_df['total'].sum(), 2)
                st.metric(label="Total CO2e", value=f"{total}kg")
                with st.expander("How much is this?"):
                    excol1, excol2 = st.columns(2)
                    with excol1:
                        st.write("It would take a fully grown tree")
                        st.subheader(f"**:green[{round(total/10)} years]**")
                        st.write("to absorb this CO2")
                    with excol2:
                        st.image("./images/tree.jpeg")
                avg_co2_journey = round(total / num_journeys, 2)
                st.metric('CO2 per journey', f"{avg_co2_journey}kg")

                transport_values = journeys_df['transport'].value_counts()

                transport_values = transport_values.sort_values(
                    ascending=False).to_dict()

                pop_transport = []
                max_val = 0
                for k, v in transport_values.items():
                    if v > max_val:
                        max_val = v
                        pop_transport = [
                            f"{k.capitalize()} {TRANSPORT_EMOJIS[k]}"]
                        continue
                    if v == max_val:
                        pop_transport.append(
                            f"{k.capitalize()} {TRANSPORT_EMOJIS[k]}")

                pop_transport = " and ".join(pop_transport)

                st.metric("Most Popular Transport", value=pop_transport)

            col1, col2 = st.columns(2)

            with col1:

                st.subheader("Average Journey")

                transport_avgs = get_transport_avgs(journeys_df)

                st.altair_chart(transport_avgs, use_container_width=True)

            with col2:

                st.subheader("Average per km")

                transport_avg_km = get_transport_avg_km(journeys_df)

                st.altair_chart(transport_avg_km, use_container_width=True)
