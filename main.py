from nicegui import app, events, ui
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import numpy as np

from readers import read_positions
from transform import apply_transform, calculate_transform, read_transform, write_transform

import os

file_columns = [
    {"name": "index", "label": "Index", "field": "index"},
    {"name": "name", "label": "File Name", "field": "name"}
]
def update_file_table(table, files):
    if files is not None:
        table.rows = [{"index": i, "name": os.path.basename(file).removesuffix(".json")} for i, file in enumerate(files)]
    else:
        table.rows = []
    table.update()

position_columns = [
    {"name": "index", "label": "Index", "field": "index"},
    {"name": "x", "label": "X", "field": "x"},
    {"name": "y", "label": "Y", "field": "y"}
]
def update_position_table(table, positions):
    if positions is not None:
        table.rows = [{"index": i, "x": pos[0], "y": pos[1]} for i, pos in enumerate(positions)]
    else:
        table.rows = []
    table.update()

def update_calibration_plot():
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Before", "After"))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(scaleanchor="y", scaleratio=1),
        xaxis2=dict(scaleanchor="y2", scaleratio=1),
    )
    calibrate_a_positions = app.storage.general.get("calibrate_a_positions")
    calibrate_b_positions = app.storage.general.get("calibrate_b_positions")
    if calibrate_a_positions is not None:
        a = np.array(calibrate_a_positions)
        labels_a = [str(i) for i in range(len(a))]
        fig.add_trace(go.Scatter(x=a[:, 0], y=a[:, 1], mode="markers+text", name="Microscope A", marker=dict(color="#D55E00"), text=labels_a, textposition="top center", textfont=dict(color="#D55E00")), row=1, col=1)
    if calibrate_b_positions is not None:
        b = np.array(calibrate_b_positions)
        labels_b = [str(i) for i in range(len(b))]
        fig.add_trace(go.Scatter(x=b[:, 0], y=b[:, 1], mode="markers+text", name="Microscope B", marker=dict(color="#0072B2"), text=labels_b, textposition="bottom center", textfont=dict(color="#0072B2")), row=1, col=1)
    transform = app.storage.general.get("transform")
    if transform is not None and calibrate_a_positions is not None and calibrate_b_positions is not None:
        a_transformed = apply_transform(
            np.array(calibrate_a_positions),
            np.array(transform["centroid_a"]),
            np.array(transform["centroid_b"]),
            transform["scaling"],
            np.array(transform["rotation"])
        )
        fig.add_trace(go.Scatter(x=a_transformed[:, 0], y=a_transformed[:, 1], mode="markers+text", name="Microscope A (transformed)", marker=dict(color="#D55E00"), text=labels_a, textposition="top center", textfont=dict(color="#D55E00")), row=1, col=2)
        fig.add_trace(go.Scatter(x=b[:, 0], y=b[:, 1], mode="markers+text", name="Microscope B", marker=dict(color="#0072B2"), text=labels_b, textposition="bottom center", textfont=dict(color="#0072B2"), showlegend=False), row=1, col=2)
    calibration_plot.update_figure(fig)

def sync():
    available_transforms = os.listdir("available_transforms") if os.path.exists("available_transforms") else []
    update_file_table(transform_file_table, available_transforms)

    relocate_position_file = app.storage.general.get("relocate_position_file")
    if relocate_position_file:
        relocate_position_label.text = f"Position file in memory: {relocate_position_file}"
    else:
        relocate_position_label.text = "Position file in memory:"

    relocate_positions = app.storage.general.get("relocate_positions")
    update_position_table(relocate_position_table, relocate_positions)

    calibrate_a_position_file = app.storage.general.get("calibrate_a_position_file")
    if calibrate_a_position_file:
        calibrate_a_position_label.text = f"Position file in memory: {calibrate_a_position_file}"
    else:
        calibrate_a_position_label.text = "Position file in memory:"

    calibrate_b_position_file = app.storage.general.get("calibrate_b_position_file")
    if calibrate_b_position_file:
        calibrate_b_position_label.text = f"Position file in memory: {calibrate_b_position_file}"
    else:
        calibrate_b_position_label.text = "Position file in memory:"

    calibrate_a_positions = app.storage.general.get("calibrate_a_positions")
    update_position_table(calibrate_a_position_table, calibrate_a_positions)

    calibrate_b_positions = app.storage.general.get("calibrate_b_positions")
    update_position_table(calibrate_b_position_table, calibrate_b_positions)

def make_upload_handler(source: str):
    async def handle_upload(e: events.UploadEventArguments):
        content = await e.file.read()
        try:
            app.storage.general[f"{source}_position_file"] = e.file.name
            app.storage.general[f"{source}_positions"] = read_positions(e.file.name, content)
            sync()
        except ValueError as ex:
            ui.notify(f"Error: {ex}")
    
    return handle_upload

def calculate_transform_handle():
    posiitons_a = app.storage.general.get("calibrate_a_positions")
    positions_b = app.storage.general.get("calibrate_b_positions")

    if posiitons_a is None or positions_b is None:
        transform_status_label.text = "Please upload position files for both microscopes before calculating the transform."
        return
    
    if len(posiitons_a) != len(positions_b):
        transform_status_label.text = "The number of positions in both files must be the same."
        return

    centroid_a, centroid_b, scaling, rotation = calculate_transform(posiitons_a, positions_b)
    app.storage.general["transform"] = {
        "centroid_a": centroid_a.tolist(),
        "centroid_b": centroid_b.tolist(),
        "scaling": float(scaling),
        "rotation": rotation.tolist()
    }

    update_calibration_plot()

    if transform_filename_input.value:
        if transform_filename_input.value not in [file["name"] for file in transform_file_table.rows]:
            write_transform(app.storage.general["transform"], transform_filename_input.value)
            update_transform_dropdown()
            transform_status_label.text = f"Transform calculated and saved as '{transform_filename_input.value}'."
            sync()
        else:
            transform_status_label.text = "A transform with that name already exists. Please choose a different name to save this transform."
            return
    else:
        transform_status_label.text = "Transform calculated successfully, but please enter a name for the transform to save it."
        return

def load_transform(name):
    app.storage.general["selected_transform"] = read_transform(name)

def update_transform_dropdown():
    available_transforms = os.listdir("available_transforms") if os.path.exists("available_transforms") else []
    transform_dropdown.clear()
    with transform_dropdown:
        for file in available_transforms:
            name = os.path.basename(file).removesuffix(".json")
            ui.item(name, on_click=lambda n=name: load_transform(n))

def clear_all_data():
    app.storage.general.clear()
    sync()

with ui.tabs().classes("w-full") as tabs:
    relocate_tab = ui.tab("Relocate")
    calibrate_tab = ui.tab("Calibrate")
with ui.tab_panels(tabs, value=relocate_tab).classes("w-full"):
    with ui.tab_panel(relocate_tab):
        ui.upload(label="Position file", max_files=1, auto_upload=True, on_upload=make_upload_handler("relocate"))
        relocate_position_label = ui.label("Position file in memory:").classes("text-gray-400 text-sm")
        relocate_position_table = ui.table(columns=position_columns, rows=[])
        transform_dropdown = ui.dropdown_button("Apply transform", auto_close=True)
        transform_dropdown.bind_enabled_from(relocate_position_table, 'rows', backward=lambda rows: len(rows) > 0)
    with ui.tab_panel(calibrate_tab):
        with ui.splitter() as splitter:
            with splitter.before:
                with ui.column().classes("pr-8"):
                    ui.label("Microscope A").classes("text-h6")
                    ui.upload(label="Position file", max_files=1, auto_upload=True, on_upload=make_upload_handler("calibrate_a"))
                    calibrate_a_position_label = ui.label("Position file in memory:").classes("text-gray-400 text-sm")
                    calibrate_a_position_table = ui.table(columns=position_columns, rows=[])
            with splitter.after:
                with ui.column().classes("pl-8"):
                    ui.label("Microscope B").classes("text-h6")
                    ui.upload(label="Position file", max_files=1, auto_upload=True, on_upload=make_upload_handler("calibrate_b"))
                    calibrate_b_position_label = ui.label("Position file in memory:").classes("text-gray-400 text-sm")
                    calibrate_b_position_table = ui.table(columns=position_columns, rows=[])
            splitter.enabled = False
        calibration_plot = ui.plotly(go.Figure()).classes("w-full")
        transform_filename_input = ui.input(label="Transform name", placeholder="Enter a name for this transform (without extension)").classes("w-96")
        with ui.row().classes("items-center"):
            ui.button("Calculate Transform", on_click=calculate_transform_handle)
            transform_status_label = ui.label("").classes("text-h7")
ui.label("Available Transforms:").classes("text-h6")
transform_file_table = ui.table(columns=file_columns, rows=[]).classes("w-96")
ui.button("Clear all data", on_click=clear_all_data)
update_transform_dropdown()
ui.timer(2, sync)
ui.run(port=80)