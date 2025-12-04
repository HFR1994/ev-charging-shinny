from shiny import ui, reactive, App
from shinywidgets import output_widget, render_widget
from ipyleaflet import Map, Marker, MarkerCluster
import geopandas as gpd
from src.shared import load_data_into_pandas, assets_dir

data_store_charging = reactive.Value()
data_store_utilization = reactive.Value()

# preload data
charging_data, utilization_data = load_data_into_pandas(assets_dir)
data_store_charging.set(charging_data)
data_store_utilization.set(utilization_data)

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_slider("connectors_filter", "Max number of connectors", 0, 20, 0),
        ui.input_checkbox_group(
            "amenities_filter",
            "Type of Amenities",
            [],
            selected=[],
        )
    ),
    ui.card(
        ui.card_header("Filtered Charging Stations"),
        ui.div(id="map", class_="map-fill")
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
    title="Restaurant tipping",
    fillable=True,
)

def server(input, output, session):

    @reactive.effect
    def _load_choices():
        df_charging = data_store_charging()
        df_utilization = data_store_utilization()

        # Flatten list of amenities
        all_amenities = sorted({a for lst in df_charging["amenities"] for a in lst})

        # Update UI choices
        ui.update_checkbox_group(
            "amenities_filter",
            choices=all_amenities,
            selected=[]
        )

        # Flatten list of amenities
        max_connectors = int(df_utilization.groupby("station_id")["id"].nunique().max())

        # Update UI choices
        ui.update_slider(
            "connectors_filter",
            max=max_connectors
        )

    @reactive.effect
    async def update_map():
        df = data_store_charging()

        centroid = gpd.points_from_xy(df["longitud"], df["latitud"]).union_all().centroid

        markers = []
        for _, row in df.iterrows():
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