import uuid
from math import ceil

import faicons
import pandas as pd
import plotly.express as px
from shapely import Point
from shiny import ui, reactive, App, render
from shinywidgets import output_widget, render_widget
import geopandas as gpd

from src.shared import load_data_into_pandas, assets_dir, inject_random_data

centroid_compute = reactive.Value(Point(0,0))
PAGE_SIZE = 5

# preload data
charging_data, utilization_tmp = load_data_into_pandas(assets_dir)
utilization_data = reactive.Value(utilization_tmp)

app_ui = ui.div(
        ui.page_navbar(
            ui.nav_spacer(),
            ui.nav_panel(
                "Map",
                ui.layout_columns(
                    ui.value_box(
                            title="Locations",
                            value=ui.output_ui("locations"),
                            showcase=faicons.icon_svg("map", width="50px"),
                            fill=False
                        ),
                        ui.value_box(
                            title="Total Charging Points",
                            value=ui.output_ui("charging_points"),
                            showcase=faicons.icon_svg("bolt", width="50px"),
                            fill=False
                        ),
                        style="margin-bottom: 10px;"
                ),
                ui.card(
                    ui.card_header("Map"),
                    ui.div(id="map", class_="map-fill")
                ),
            ),
            ui.nav_panel(
                "Data",
             ui.card(
                        ui.input_select(
                            "station_filter",
                            "Select Station",
                            [],
                            multiple=False,
                        ),
                        ui.input_action_button("action_button", "Generate Random Data"),
                        ui.output_data_frame("utilization_df"),
                    ),
                    ui.card(
                        ui.output_ui("charger_cards"),  # container for dynamic cards
                        ui.div(
                            ui.input_action_button("prev_page", "← Previous", class_="btn btn-secondary btn-sm mx-2"),
                            ui.p(ui.output_text("page_info"), class_="text-center"),
                            ui.input_action_button("next_page", "Next →", class_="btn btn-secondary btn-sm mx-2"),
                            class_="d-flex justify-content-center align-items-center mt-3 mb-2"
                        ),
                    ),
            ),
            sidebar= ui.sidebar(
                ui.input_slider("connectors_filter", "Max number of connectors", 0, 20, 0),
                ui.input_checkbox_group(
                    "amenities_filter",
                    "Type of Amenities",
                    [],
                    selected=[],
                ),
                ui.input_select(
                    "mva_filter",
                    "Has MVA (tax)",
            {"any": "Any Choice", "true": "Yes", "false": "No"},
                ),
                ui.input_select(
                    "extra_filter",
                    "Has extra tariff",
                    {"any": "Any Choice", "true": "Yes", "false": "No"},
                ),
            ),
            id="tabs",
            title="Filtered EV Charging",
            fillable=True
        ),
        ui.HTML("""
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
            <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
            <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
            <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
        """),
        ui.include_css(assets_dir / "styles.css"),
        ui.include_js(assets_dir / "map.js"),
)

def server(input, output, session):
    initialize = reactive.Value(True)
    page = reactive.Value(0)
    max_pages = reactive.Value(0)
    current_chargers = reactive.Value(pd.DataFrame())

    @reactive.effect
    @reactive.event(input.next_page)
    async def _next():
        if page() + 1 <= max_pages():
            page.set(page() + 1)
            await session.send_custom_message("scroll_top", {})

    @reactive.effect
    @reactive.event(input.prev_page)
    async def _prev():
        if page() > 1:
            page.set(page() - 1)
            await session.send_custom_message("scroll_top", {})

    @reactive.effect
    @reactive.event(input.action_button)
    def generate_data():
        _, df_utilization = apply_filter()

        stations = df_utilization["station_id"].unique().tolist()

        try:
            df_new, station_id = inject_random_data(number=50, alternatives=stations, utilization_data=utilization_data())
            utilization_data.set(df_new)

            ui.notification_show(
                f"Inject 50 rows to {station_id} station, please refresh the view",
                type="message",
                duration=5,
            )

            ui.update_select("station_filter", selected=station_id)
        except Exception as e:
            ui.notification_show(
                str(e),
                type="error",
                duration=5,
            )


    @output
    @render.text
    def page_info():
        return f"Page {page()} of {max_pages()}"

    @render.data_frame
    @reactive.event(input.station_filter, ignore_none=False)
    @reactive.event(utilization_data, ignore_none=False)
    def utilization_df():
        _, df_utilization = apply_filter()

        station = input.station_filter()
        df_station = df_utilization[df_utilization["station_id"] == station]

        return render.DataGrid(df_station)

    @reactive.effect
    def _load_choices():
        if initialize():

            centroid = gpd.points_from_xy(charging_data["longitud"], charging_data["latitud"]).union_all().centroid
            centroid_compute.set(centroid)

            # Flatten list of amenities
            all_amenities = sorted({a for lst in charging_data["amenities"] for a in lst})

            # Update UI choices
            ui.update_checkbox_group(
                "amenities_filter",
                choices=all_amenities
            )

            # Flatten list of amenities
            if utilization_data().empty:
                max_connectors = 0
            else:
                max_connectors = int(utilization_data().groupby("station_id")["id"].nunique().max())

            # Update UI choices
            ui.update_slider(
                "connectors_filter",
                max=max_connectors,
                value=max_connectors,
            )

            stations = sorted(utilization_data()["station_id"].unique())
            ui.update_select("station_filter", choices=stations, selected=None)

            # flip the flags
            initialize.set(False)

    @reactive.effect
    @reactive.event(input.station_filter, ignore_none=False)
    @reactive.event(utilization_data, ignore_none=False)
    def change_graph():
        _, df_utilization = apply_filter()

        station = input.station_filter()

        df_station = df_utilization[df_utilization["station_id"] == station]
        charger_ids = df_station["id"].unique().tolist()

        page.set(1)
        max_pages.set(ceil(len(charger_ids) / PAGE_SIZE))
        current_chargers.set(df_station)

    @reactive.effect
    @reactive.event(input.connectors_filter, input.amenities_filter, input.mva_filter, input.extra_filter)
    def update_input():
        _, df_utilization = apply_filter()

        stations = sorted(df_utilization["station_id"].unique())
        ui.update_select("station_filter", choices=stations, selected=None)

        if not stations:
            page.set(0)
            max_pages.set(0)
            current_chargers.set(pd.DataFrame())

    @output
    @render.ui
    def charger_cards():
        df_station = current_chargers()

        if not df_station.empty:

            chargers_ids = df_station["id"].unique().tolist()

            # Build a list of UI elements (cards)
            card_list = []

            lower_bound = (page() - 1) * PAGE_SIZE
            upper_bound = page() * PAGE_SIZE

            for charger_id in chargers_ids[lower_bound:upper_bound]:
                name = str(uuid.uuid4()).split("-")[0]
                charger_df = df_station[df_station["id"] == charger_id]

                card_list.append(
                    ui.card(
                        ui.card_header(f"Tariff History - Charger {charger_id}"),
                        output_widget(name, height="300px"),
                        full_screen=True,
                        style="margin-bottom: 20px;"
                    )
                )

                output(render_plot_func(charger_df=charger_df), id=name)

            # Auto-layout grid
            return ui.layout_column_wrap(*card_list, width="300px")

        return ui.div()

    def render_plot_func(charger_df):
        @render_widget
        def f():
            fig = px.box(
                charger_df,
                x="id",
                y="price",
                color="id",
                points="all",
            )

            fig.update_layout(showlegend=False)

            return fig

        return f

    @reactive.calc
    def apply_filter():

        df_charging = charging_data.copy()
        df_utilization = utilization_data().copy()

        selected_amenities = input.amenities_filter()
        max_connectors = input.connectors_filter()
        has_mva = input.mva_filter()
        has_extra = input.extra_filter()

        if initialize():
            return df_charging, df_utilization

        # Compute initial filters
        df_charging = df_charging[df_charging["amenities"].apply(lambda lst: all(a in lst for a in selected_amenities))]

        connectors = df_utilization.groupby("station_id")["id"].nunique()
        df_utilization = df_utilization[
            df_utilization["station_id"].isin(connectors[connectors <= max_connectors].index)]


        if 'any' != has_mva:
            condition = has_mva == "true"
            df_utilization = df_utilization[df_utilization["has_vat"] == condition]


        match has_extra:
            case 'true':
                df_utilization = df_utilization[df_utilization["extra_tariff"].notnull()]
            case 'false':
                df_utilization = df_utilization[df_utilization["extra_tariff"].isnull()]

        # Cross match with the other filter

        charging_ids = set(df_charging["id"])
        utilization_ids = set(df_utilization["station_id"])
        common_ids = charging_ids & utilization_ids

        df_charging = df_charging[df_charging["id"].isin(common_ids)]
        df_utilization = df_utilization[df_utilization["station_id"].isin(common_ids)]

        return df_charging, df_utilization

    @render.text
    def locations():
        df_charging, _ = apply_filter()

        return str(int(df_charging["name"].nunique()))

    @render.text
    def charging_points():
        _, df_utilization = apply_filter()

        unique_count = pd.concat([df_utilization["station_id"],
                                  df_utilization["id"]], ignore_index=True)

        return str(int(unique_count.nunique()))

    @reactive.effect
    async def update_map():
        df_charging, _ = apply_filter()

        markers = []
        centroid = centroid_compute()

        if not df_charging.empty:

            markers = []
            for _, row in df_charging.iterrows():
                html_popup = f"""
                    <div style='font-size:14px'>
                        <b>{row['name']}</b><br/>
                        {row['address']}<br/>
                    </div>
                """

                markers.append({
                    "lat": row["latitud"],
                    "lng": row["longitud"],
                    "popup": html_popup,
                })

        await session.send_custom_message(
            "update_map",
            {
                "center": {"lat": centroid.y, "lng": centroid.x},
                "markers": markers,
            }
        )

app = App(app_ui, server)