"""Visualisations for the dashboard."""

import altair as alt
import pandas as pd
import pydeck as pdk
from pydeck.data_utils import compute_view

GREEN_RGB = [26, 147, 111]

PIE_COLOURS = ["#1A936F", "#88D498", "#114B5F"]


def get_zoom_data(journey_data: dict) -> pdk.ViewState:
    """Returns the zoom data for a given journey."""

    zoom_data = [[journey_data['origin']['lon'], journey_data['origin']['lat']], [
        journey_data['destination']['lon'], journey_data['destination']['lat']]]

    zoom = compute_view(zoom_data)

    zoom.width = 700
    zoom.height = 300
    zoom.pitch = 35
    zoom.zoom = zoom.zoom - 1

    return zoom


def get_journey_map(journey_data: dict) -> pdk.Deck:
    """Returns a map of the journey."""

    map_data = pd.DataFrame([{
        'origin_name': journey_data['origin']['name'],
        'origin_lat': journey_data['origin']['lat'],
        'origin_lon': journey_data['origin']['lon'],
        'dest_name': journey_data['destination']['name'],
        'dest_lat': journey_data['destination']['lat'],
        'dest_lon': journey_data['destination']['lon']
    }])

    origin = journey_data['origin']['name']
    dest = journey_data['destination']['name']

    zoom = get_zoom_data(journey_data)

    journey_map = pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=zoom,
        layers=[
            pdk.Layer(
                'ArcLayer',
                data=map_data,
                get_source_position=['origin_lon', 'origin_lat'],
                get_target_position=['dest_lon', 'dest_lat'],
                get_source_color=GREEN_RGB,
                get_target_color=GREEN_RGB,
                auto_highlight=True,
                pickable=True,
                get_tilt=0,
                get_width=3
            ),
        ],
        tooltip={'text': f"{origin} to {dest}"}
    )

    journey_map.picking_radius = 10

    return journey_map


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

    journeys_df['transport'] = journeys_df['transport'].apply(
        lambda x: x.capitalize())

    chart = alt.Chart(journeys_df).mark_bar().encode(
        x=alt.X('transport', title=""),
        y=alt.Y('mean(total)', title='CO2 (kg)'),
        color=alt.Color('transport',
                        scale=alt.Scale(range=PIE_COLOURS)).legend(None)
    ).configure_axis(grid=False)

    return chart


def get_transport_avg_km(journeys_df: pd.DataFrame) -> alt.Chart:
    """Returns a bar chart of CO2 per transport."""

    co2_tot = journeys_df.groupby('transport')['total'].sum()
    tot_dist = journeys_df.groupby('transport')['distance'].sum()

    data = []

    if 'Air' in journeys_df['transport'].values:
        air_tot = co2_tot['Air']
        air_dist = tot_dist['Air']
        air_avg_km = round(air_tot / air_dist, 2)
        data.append({'transport': 'Air', 'average': air_avg_km})

    if 'Car' in journeys_df['transport'].values:
        car_tot = co2_tot['Car']
        car_dist = tot_dist['Car']
        car_avg_km = round(car_tot / car_dist, 2)
        data.append({'transport': 'Car', 'average': car_avg_km})

    if 'Rail' in journeys_df['transport'].values:
        rail_tot = co2_tot['Rail']
        rail_dist = tot_dist['Rail']
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
