"""
fire_panel.py
Teddy Pomianek

creates widgets, map constructors, binds and plots in panel.
"""

import panel as pn
from wildfire_api_ted import FIREAPI
import plotly.express as px


# Loads javascript dependencies and configures Panel (required)
pn.extension("plotly", "tabulator")


# Initialize api
api = FIREAPI()
api.load_data("data/ODF_Fire_Occurrence_Data_2000-2022.csv")
df = api.return_dataframe()

# center lat and long for oregon to use for maps
center_oregon = {"lat": 46.0, "lon": -120.5}


# WIDGET DECLARATIONS

# Search Widgets

# allows user to select range of years to alter maps
year_range_slider = pn.widgets.IntRangeSlider(
    name='Year Slider',
    start=int(df["year"].min()),
    end=int(df["year"].max()),
    value=(int(df["year"].min()), int(df["year"].max())),
    step=1
)

# used in changing map type from acre density to acre scatter
mode_toggle = pn.widgets.RadioButtonGroup(
    name="Map Mode",
    options=["Density", "Circles"],
    value="Density"
)

# used in changing cause Human or Lightning
source_selector = pn.widgets.RadioButtonGroup(
    name="Fire Source",
    options=["Human", "Lightning"],
    value="Human"
)

# creates alphabetically sorted list of every distinct causeby category
causeby_options = sorted(api.human_df()["cause"].dropna().astype(str).unique().tolist())

# multiselect widget for causeby. default no options selected
cause_multi = pn.widgets.MultiSelect(
    name="Human Cause of Fire",
    options=causeby_options,
    value=[],
    size=10
)

# select all human causes button
select_all_human_btn = pn.widgets.Button(name="Select All Human Causes",
                                         button_type="primary")


# Plotting widgets

# plots dataframe with tabulator widget. default 100 rows shown
df_widget = pn.widgets.Tabulator(
    df,
    name="Oregon Wildfire Data",
    show_index=False,
    pagination='local',
    page_size=100
)


# CALLBACK FUNCTIONS
def get_density_map(dataframe, lat="lat", lon="lon", acres="acres",
                    center=center_oregon, zoom=5, radius=14, height=600):
    """
    Creates a plotly density map which displays the color density of fires
    based on acreage. So hotter colors become hotter when there are larger
    fires and a greater amount of fires in a given area. Cooler colors
    represent fewer and smaller fires.

    center: dictionary of a lat and lon point that represents the starting view
    radius: larger radius spreads colors and merges colors more and vice versa
    """
    # takes acres data, fills empty data with 0, takes square root to be able
    # to see smaller values, and set minimum weight per point so tiny values
    # don't disappear
    weights = dataframe[acres].fillna(0).pow(0.5).clip(lower=0.2)

    # saves a copy of the dataframe with new weight (new acre value of each
    # point)
    df_for_plot = dataframe.copy()
    df_for_plot["Acres (density weight)"] = weights

    # creates plot
    fig = px.density_mapbox(
        df_for_plot,
        lat=lat,
        lon=lon,
        z="Acres (density weight)",
        radius=radius, center=center, zoom=zoom,
        mapbox_style="open-street-map", height=height
    )
    # rename color bar
    fig.update_layout(
        coloraxis_colorbar=dict(title="Acres (density weight)"),
        margin=dict(l=0, r=0, t=0, b=0)
    )
    return fig


def get_circle_map(dataframe, lat="lat", lon="lon", acres="acres",
                   center=center_oregon, zoom=5, height=600):
    """Creates a scatter plot with circles ranging in sizes based on the
    acreage of the fire"""

    # set marker sizes to acres compressed with sqrt and makes min marker
    # size 0.5
    marker_sizes = dataframe[acres].pow(0.5).clip(lower = 0.5)

    # copy df to create new df with marker sizes col
    df_copy = dataframe.copy()
    df_copy["marker_size"] = marker_sizes

    # create plot
    fig = px.scatter_mapbox(
        df_copy,
        lat=lat,
        lon=lon,
        size="marker_size",
        size_max=48,
        color=acres,
        zoom=zoom, center=center, height=height,
        mapbox_style="open-street-map",
        hover_data={acres: ':.2f', lat: ':.3f', lon: ':.3f'} # sets max
        # decimals displayed for acres, lat and lon when hovered over a fire
        # instance
    )

    # title color bar
    fig.update_layout(
        coloraxis_colorbar=dict(title="Acres affected"),
        margin=dict(l=0, r=0, t=0, b=0)
    )
    return fig

def get_causeby_map(dataframe, lat="lat", lon="lon", acres="acres",
                    center=center_oregon, zoom=5, height=600):
    """
    Creates a scatter map by cause
    """
    # copies so the original dataframe is not changed when plotting
    df_copy = dataframe.copy()

    # if detailed human causes exist and at least one is not missing,
    # color points by that cause; otherwise color by Human vs Lightning
    if "cause" in df_copy.columns and df_copy["cause"].notna().any():
        color_column = "cause"
    else:
        color_column = "HumanOrLightning"

    # grab acres column as a series for marker sizing
    acres_series = df_copy[acres]

    # even out bubble sizes so small fires still show up
    df_copy["marker_size"] = acres_series.pow(0.5)

    # build circle map colored by the chosen column
    fig = px.scatter_mapbox(
        df_copy, lat=lat, lon=lon,
        color=color_column,
        size="marker_size", size_max=42,
        zoom=zoom, center=center, height=height,
        mapbox_style="open-street-map",
        hover_data={acres: ':.2f', lat: ':.3f', lon: ':.3f'}
    )

    # remove default margins and name the legend after the color column
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        legend_title_text=color_column
    )
    return fig


def base_filtered(year_range, source, causes):
    """
    returns a df
    """
    # grab start and end year from slider widget
    year_start, year_end = year_range

    # start with human data if source is Human if not then lightning
    if source == "Human":
        base_df = api.human_df()
        # if any human causes are selected, keep only those rows
        base_df = api.filter_by_cause(base_df, causes)
    else:
        base_df = api.lightning_df()

    # keep only rows within the selected year range
    filtered_df = base_df[base_df["year"].between(year_start, year_end)].copy()
    return filtered_df


def change_view(year_range, mode, source, causes):
    """
    changes between density and circle map based on mode selector
    """
    # build the filtered dataframe from widgets
    filtered_df = base_filtered(year_range, source, causes)

    # switch map type based on mode toggle
    if mode == "Density":
        fig = get_density_map(filtered_df)
    else:
        fig = get_circle_map(filtered_df)

    # return a Panel Plotly pane
    return pn.pane.Plotly(fig, config={"displayModeBar": False})


def change_causeby_view(year_range, source, causes):
    """
    updates the cause-by map in the right column
    """
    # creates filtered df bsed on year_range, source, causes selected
    filtered_df = base_filtered(year_range, source, causes)

    # plot scatter circle map with the filtered df
    fig = get_causeby_map(filtered_df)

    # return as a Panel Plotly pane
    return pn.pane.Plotly(fig, config={"displayModeBar": False})


def toggle_causes(event=None):
    """
    disables the human cause list when Lightning is selected
    """
    # if Lightning is chosen disable and clear the human causes list
    if source_selector.value == "Lightning":
        # disables widget
        cause_multi.disabled = True
        # empties selections
        cause_multi.value = []
    else:
        # if Human is chosen re-enable list
        cause_multi.disabled = False


def select_all_human_causes(event=None):
    """
    selects every human cause at once for select all human button.
    """
    # force Human mode
    source_selector.value = "Human"
    # select all human causes in the MultiSelect
    cause_multi.value = list(causeby_options)


# CALLBACK BINDINGS (Connecting widgets to callback functions)
map_bound = pn.bind(
    change_view,
    year_range=year_range_slider,
    mode=mode_toggle,
    source=source_selector,
    causes=cause_multi
)

cause_map_bound = pn.bind(
    change_causeby_view,
    year_range=year_range_slider,
    source=source_selector,
    causes=cause_multi
)

source_selector.param.watch(toggle_causes, "value")
toggle_causes()

select_all_human_btn.on_click(select_all_human_causes)


# DASHBOARD WIDGET CONTAINERS ("CARDS")

card_width = 320

search_card = pn.Card(
    pn.Column(
        # Widget 1
        year_range_slider,
        # Widget 2
        mode_toggle,
        # Widget 3
        source_selector,
        # Widget 4
        cause_multi,
        # Widget 5
        select_all_human_btn
    ),
    title="Map Filters", width=card_width, collapsed=False
)

# LAYOUT

layout = pn.template.FastListTemplate(
    title="Oregon Wildfire Dashboard by Teddy Pomianek",
    sidebar=[
        search_card,
    ],
    theme_toggle=False,
    main=[
        pn.Tabs(
            ("Oregon Wildfire Data", df_widget),  # Replace None with callback binding
            ("Wildfire Maps", pn.Row(map_bound, cause_map_bound)),  # two-column maps
            active=0  # Which tab is active by default?
        )

    ],
    header_background='#a93226'

).servable()

layout.show()
