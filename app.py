import faicons
import pandas as pd
from shapely import Point
from shapely.constructive import centroid
from shiny import ui, reactive, App, render
import geopandas as gpd
from src.shared import load_data_into_pandas, assets_dir

centroid_compute = reactive.Value(Point(0,0))

# preload data
charging_data, utilization_data = load_data_into_pandas(assets_dir)

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
                    ,
                ),
            ),
            sidebar= ui.sidebar(
                ui.input_slider("connectors_filter", "Max number of connectors", 0, 20, 0),
                ui.input_checkbox_group(
                    "amenities_filter",
                    "Type of Amenities",
                    [],
                    selected=[],
                )
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
            if utilization_data.empty:
                max_connectors = 0
            else:
                max_connectors = int(utilization_data.groupby("station_id")["id"].nunique().max())

            # Update UI choices
            ui.update_slider(
                "connectors_filter",
                max=max_connectors,
                value=max_connectors,
            )

            # flip the flags
            initialize.set(False)

    @reactive.calc
    def apply_filter():
        df_charging = charging_data.copy()
        df_utilization = utilization_data.copy()

        selected_amenities = input.amenities_filter()
        max_connectors = input.connectors_filter()

        if initialize():
            return df_charging, df_utilization

        # Compute initial filters
        df_charging = df_charging[df_charging["amenities"].apply(lambda lst: all(a in lst for a in selected_amenities))]

        connectors = df_utilization.groupby("station_id")["id"].nunique()
        df_utilization = df_utilization[
            df_utilization["station_id"].isin(connectors[connectors <= max_connectors].index)]

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