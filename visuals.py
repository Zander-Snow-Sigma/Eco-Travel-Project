"""Visualisations for the dashboard."""

import altair as alt
import pandas as pd
import pydeck as pdk

GREEN_RGB = [0, 255, 0, 40]
RED_RGB = [240, 100, 0, 40]

PIE_COLOURS = ["#1A936F", "#88D498", "#114B5F"]


def get_car_train_bar(total_co2e: float) -> alt.Chart:
    """
    Returns a bar chart comparing emissions from a train journey and
    the equivalent car journey.
    """

    data = pd.DataFrame([{'transport': "Train", 'total': total_co2e}, {
        'transport': "Car", 'total': round(total_co2e * 5, 2)}])

    base = alt.Chart(data).encode(
        x=alt.X('transport', title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('total', title=None, axis=None),
        color=alt.Color('transport', scale=alt.Scale(
            range=PIE_COLOURS), legend=None)
    ).properties(height=200, width=140)

    text = base.transform_calculate(label_with_kg="datum.total + 'kg'").mark_text(
        align='center', baseline='bottom', fontSize=12, fontWeight=600, dy=-3
    ).encode(
        text='label_with_kg:N'
    )

    chart = base.mark_bar() + text

    return chart


def get_carbon_pie(journey_data: dict) -> alt.Chart:
    """Returns a pie chart of the direct and indirect carbon emissions."""

    direct_perc = round(
        (journey_data['co2e']['direct'] / journey_data['co2e']['total']) * 100, 1)
    indirect_perc = round(
        (journey_data['co2e']['indirect'] / journey_data['co2e']['total']) * 100, 1)

    data = pd.DataFrame(data=[{'co2e': round(journey_data['co2e']['direct'], 2), 'type': 'Direct', 'percentage': f"{direct_perc}%"}, {
                        'co2e': round(journey_data['co2e']['indirect'], 2), 'type': 'Indirect', 'percentage': f"{indirect_perc}%"}])

    # pie = alt.Chart(data).mark_arc().encode(
    #     angle=alt.Angle("co2e", title="CO2e in kg"),
    #     color=alt.Color('type', title="Emission Type",
    #                     scale=alt.Scale(range=PIE_COLOURS))
    # )

    base = alt.Chart(data).encode(
        alt.Theta("co2e", title="CO2e kg").stack(True),
        alt.Color("type", title=None,
                  legend=alt.Legend(orient='none',
                                    legendX=140, legendY=0, direction='horizontal', titleFontSize=18, titleFontWeight=300, titleAnchor='middle'),
                  scale=alt.Scale(range=PIE_COLOURS))
    )

    pie = base.mark_arc(outerRadius=120)
    text = base.mark_text(radius=140, size=15).encode(text='percentage')

    return pie + text


def get_transport_bar(journeys_df: pd.DataFrame) -> alt.Chart:
    """Returns a bar chart of CO2 per transport."""

    bar_chart = alt.Chart(journeys_df).mark_bar().encode(
        x=alt.X('transport', title=""),
        y=alt.Y('sum(total)', title='Total CO2 (kg)'),
        color=alt.Color('transport',
                        scale=alt.Scale(range=PIE_COLOURS)).legend(None)
    )

    return bar_chart


def get_transport_avgs(journeys_df: pd.DataFrame) -> alt.Chart:
    """Returns a bar chart of average CO2 per journey for each transport."""

    chart = alt.Chart(journeys_df).mark_bar().encode(
        x=alt.X('transport', title=""),
        y=alt.Y('mean(total)', title='CO2 (kg)'),
        color=alt.Color('transport',
                        scale=alt.Scale(range=PIE_COLOURS)).legend(None)
    ).configure_axis(grid=False)

    return chart


def get_transport_avg_km(journeys_df: pd.DataFrame) -> alt.Chart:
    """Returns a bar chart of CO2 per transport."""

    # test = journeys_df.groupby('transport')

    # print(test['total'])

    co2_tot = journeys_df.groupby('transport')['total'].sum()
    tot_dist = journeys_df.groupby('transport')['distance'].sum()

    data = []

    if 'air' in journeys_df['transport'].values:
        air_tot = co2_tot['air']
        air_dist = tot_dist['air']
        air_avg_km = round(air_tot / air_dist, 2)
        data.append({'transport': 'Air', 'average': air_avg_km})

    if 'car' in journeys_df['transport'].values:
        car_tot = co2_tot['car']
        car_dist = tot_dist['car']
        car_avg_km = round(car_tot / car_dist, 2)
        data.append({'transport': 'Car', 'average': car_avg_km})

    if 'rail' in journeys_df['transport'].values:
        rail_tot = co2_tot['rail']
        rail_dist = tot_dist['rail']
        rail_avg_km = round(rail_tot / rail_dist, 2)
        data.append({'transport': 'Rail', 'average': rail_avg_km})

    transport_data = pd.DataFrame(data)

    bar_chart = alt.Chart(transport_data).mark_bar().encode(
        x=alt.X('transport', title=""),
        y=alt.Y('average', title='CO2 (kg)'),
        color=alt.Color('transport',
                        scale=alt.Scale(range=PIE_COLOURS)).legend(None)
    ).configure_axis(grid=False)

    return bar_chart


def get_map(journey_data: dict) -> pdk.Deck:
    """Test map."""

    data = pd.DataFrame(data=[{'origin_name': journey_data['origin_name'], 'dest_name': journey_data['dest_name'], 'origin_lat': journey_data['origin_lat'],
                        'origin_long': journey_data['origin_long'], 'dest_lat': journey_data['dest_lat'], 'dest_long': journey_data['dest_long']}])

    print(data)

    arc_layer = pdk.Layer(
        type="ArcLayer",
        data=data,
        get_source_position=["origin_lat", "origin_long"],
        get_target_position=["dest_lat", "dest_long"],
        get_width=1000,
        get_tilt=15,
        get_source_color=RED_RGB,
        get_target_color=GREEN_RGB,
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=journey_data['origin_lat'],
        longitude=journey_data['origin_long'],
        bearing=0,
        pitch=50,
        zoom=8,
    )

    return pdk.Deck(arc_layer, initial_view_state=view_state)


DATA_URL = "https://raw.githubusercontent.com/ajduberstein/sf_public_data/master/bay_area_commute_routes.csv"
# A bounding box for downtown San Francisco, to help filter this commuter data
DOWNTOWN_BOUNDING_BOX = [
    -122.43135291617365,
    37.766492914983864,
    -122.38706428091974,
    37.80583561830737,
]


def in_bounding_box(point):
    """Determine whether a point is in our downtown bounding box"""
    lng, lat = point
    in_lng_bounds = DOWNTOWN_BOUNDING_BOX[0] <= lng <= DOWNTOWN_BOUNDING_BOX[2]
    in_lat_bounds = DOWNTOWN_BOUNDING_BOX[1] <= lat <= DOWNTOWN_BOUNDING_BOX[3]
    return in_lng_bounds and in_lat_bounds


df = pd.read_csv(DATA_URL)
# Filter to bounding box
df = df[df[["lng_w", "lat_w"]].apply(lambda row: in_bounding_box(row), axis=1)]

GREEN_RGB = [0, 255, 0, 40]
RED_RGB = [240, 100, 0, 40]

# Specify a deck.gl ArcLayer
arc_layer = pdk.Layer(
    "ArcLayer",
    data=df,
    get_width="S000 * 2",
    get_source_position=["lng_h", "lat_h"],
    get_target_position=["lng_w", "lat_w"],
    get_tilt=15,
    get_source_color=RED_RGB,
    get_target_color=GREEN_RGB,
    pickable=True,
    auto_highlight=True,
)

view_state = pdk.ViewState(
    latitude=37.7576171,
    longitude=-122.5776844,
    bearing=45,
    pitch=50,
    zoom=8,
)


TOOLTIP_TEXT = {
    "html": "{S000} jobs <br /> Home of commuter in red; work location in green"}


def get_example_map():
    return pdk.Deck(arc_layer, initial_view_state=view_state, tooltip=TOOLTIP_TEXT)


def get_transport_donut(journeys_df: pd.DataFrame) -> alt.Chart:
    """Returns a bar chart of CO2 per transport."""

    totals = journeys_df.groupby('transport')['total'].sum()

    data = []

    if 'air' in journeys_df['transport'].values:
        air_tot = totals['air']
        data.append({'transport': 'Air', 'total': round(air_tot, 1)})

    if 'rail' in journeys_df['transport'].values:
        rail_tot = totals['rail']
        data.append({'transport': 'Rail', 'total': round(rail_tot, 1)})

    if 'car' in journeys_df['transport'].values:
        car_tot = totals['car']
        data.append({'transport': 'Car', 'total': round(car_tot, 1)})

    transport_data = pd.DataFrame(data)

    # print(totals)

    # air_tot = journeys_df.groupby('transport')['total'].sum()['air']
    # rail_tot = journeys_df.groupby('transport')['total'].sum()['rail']
    # car_tot = journeys_df.groupby('transport')['total'].sum()['car']

    # data = pd.DataFrame([{'transport': 'Air', 'total': round(air_tot, 1)}, {
    #                     'transport': 'Rail', 'total': round(rail_tot, 1)}, {'transport': 'Car', 'total': round(car_tot, 1)}])

    base = alt.Chart(transport_data).encode(
        theta=alt.Theta('total', stack=True)
    )

    pie = base.mark_arc(innerRadius=60, outerRadius=140).encode(
        color=alt.Color('transport',
                        scale=alt.Scale(range=PIE_COLOURS), legend=None)
    )

    outer_text = base.mark_text(radius=165, size=17).encode(text=alt.Text('transport'), color=alt.Color('transport',
                                                                                                        scale=alt.Scale(range=PIE_COLOURS), legend=None))

    text = base.transform_calculate(label_with_kg="datum.total + 'kg'").mark_text(
        radius=100, size=15, color='white', fontWeight=600
    ).encode(
        text=alt.Text('label_with_kg:N')
    )

    chart = pie + text + outer_text

    return chart
