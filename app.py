import os
from pathlib import Path

# Import data from shared.py
from shiny import ui, reactive, App
from src.shared import load_data_into_pandas, assets_dir

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_slider("connectors_filter", "Max number of connectors", 0, 20, 0),
        ui.input_checkbox_group(
            "amenities_filter",
            "Type of Amenities",
            ["Adelie", "Gentoo", "Chinstrap"],
            selected=["Adelie", "Gentoo", "Chinstrap"],
        )
    ),
    ui.layout_column_wrap(
ui.h2("Filtered Charging Stations"),
        fill=False
    ),
    ui.include_css(assets_dir / "styles.css"),
    title="Restaurant tipping",
    fillable=True,
)

def server(input, output, session):

    data_store_charging = reactive.Value()
    data_store_utilization = reactive.Value()

    charging_data, utilization_data = load_data_into_pandas(assets_dir)

    data_store_charging.set(charging_data)
    data_store_utilization.set(utilization_data)

    @reactive.effect
    def _load_choices():
        df = data_store_charging.get()

        # Flatten list of amenities
        all_amenities = sorted({a for lst in df["amenities"] for a in lst})

        # Update UI choices
        ui.update_checkbox_group(
            "amenities_filter",
            choices=all_amenities,
            selected=[]
        )

        # What is the max number of connectors?
        max_chargers = df["totalConnectors"].max()

        # Update UI choices
        ui.update_slider(
            "connectors_filter",
            min=0,
            max=max_chargers
        )

app = App(app_ui, server)