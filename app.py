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
ui.h2("Filtered Charging Stations"),
    ui.layout_column_wrap(
        ui.card(
            ui.card_header("Map"),
            output_widget("render_map"),
        ),
        fill=True
    ),
    ui.include_css(assets_dir / "styles.css"),
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
    def _():
        df = data_store_charging()

        # If widget is not ready, skip
        if render_map.widget is None:
            return

        m = render_map.widget

        # update center
        centroid = gpd.points_from_xy(df["longitud"], df["latitud"]).union_all().centroid
        m.center = (centroid.y, centroid.x)

        markers = []
        for _, row in df.iterrows():
            marker = Marker(location=(row["latitud"], row["longitud"]))
            markers.append(marker)

        m.layers[1].markers = markers


    @render_widget
    def render_map():
        # create map
        m = Map(center=(0,0))
        m.add(MarkerCluster(markers=[Marker(location=(0,0))]))  # store empty cluster

        return m

app = App(app_ui, server)