def _load_amenities_choices():
    df = data_store_charging.get()

    # Flatten list of amenities
    all_amenities = sorted({a for lst in df["amenities"] for a in lst})

    # Update UI choices
    ui.update_checkbox_group(
        "amenities_filter",
        choices=all_amenities,
        selected=[]
    )

@reactive.effect
def _load_amenities_choices():
    df = data_store_charging.get()

    # Flatten list of amenities
    all_amenities = sorted({a for lst in df["amenities"] for a in lst})

    # Update UI choices
    ui.update_checkbox_group(
        "amenities_filter",
        choices=all_amenities,
        selected=[]
    )
