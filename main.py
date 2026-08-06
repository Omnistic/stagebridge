from nicegui import app, events, ui
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import numpy as np

from handlers import read_positions, write_positions
from transform import apply_transform, calculate_transform, read_transform, write_transform

import os, uuid, secrets

STORAGE_SECRET_FILE = ".storage_secret"


def get_storage_secret() -> str:
    """Return a stable secret for signing per-user session cookies.

    Reads from the STAGEBRIDGE_STORAGE_SECRET environment variable if set,
    otherwise reuses (or creates) a local secret file so that restarting the
    app doesn't invalidate every user's in-progress session.
    """
    env_secret = os.environ.get("STAGEBRIDGE_STORAGE_SECRET")
    if env_secret:
        return env_secret
    if os.path.exists(STORAGE_SECRET_FILE):
        with open(STORAGE_SECRET_FILE) as f:
            return f.read().strip()
    new_secret = secrets.token_hex(32)
    with open(STORAGE_SECRET_FILE, "w") as f:
        f.write(new_secret)
    return new_secret

file_columns = [
    {"name": "index", "label": "Index", "field": "index"},
    {"name": "name", "label": "File Name", "field": "name"},
    {"name": "centroid_a", "label": "Centroid A", "field": "centroid_a"},
    {"name": "centroid_b", "label": "Centroid B", "field": "centroid_b"},
    {"name": "scaling", "label": "Scaling", "field": "scaling"},
    {"name": "rotation", "label": "Rotation (degrees)", "field": "rotation"},
    {"name": "flip_x", "label": "Flip X", "field": "flip_x"},
    {"name": "flip_y", "label": "Flip Y", "field": "flip_y"},
]
def update_file_table(table, files):
    if files is not None:
        rows = []
        for i, file in enumerate(files):
            name = os.path.basename(file).removesuffix(".json")
            transform = read_transform(name)
            rotation_deg = np.rad2deg(np.arctan2(np.array(transform["rotation"])[1, 0], np.array(transform["rotation"])[0, 0]))
            mirror = np.array(transform.get("mirror", [[1, 0], [0, 1]]))
            rows.append({
                "index": i,
                "name": name,
                "centroid_a": str(np.round(transform["centroid_a"], 2)),
                "centroid_b": str(np.round(transform["centroid_b"], 2)),
                "scaling": round(transform["scaling"], 4),
                "rotation": round(rotation_deg, 2),
                "flip_x": bool(mirror[0, 0] < 0),
                "flip_y": bool(mirror[1, 1] < 0),
            })
        table.rows = rows
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
    calibrate_a_positions = app.storage.user.get("calibrate_a_positions")
    calibrate_b_positions = app.storage.user.get("calibrate_b_positions")
    if calibrate_a_positions is not None:
        a = np.array(calibrate_a_positions)
        labels_a = [str(i) for i in range(len(a))]
        fig.add_trace(go.Scatter(x=a[:, 0], y=a[:, 1], mode="markers+text", name="Microscope A", marker=dict(color="#D55E00"), text=labels_a, textposition="top center", textfont=dict(color="#D55E00")), row=1, col=1)
    if calibrate_b_positions is not None:
        b = np.array(calibrate_b_positions)
        labels_b = [str(i) for i in range(len(b))]
        fig.add_trace(go.Scatter(x=b[:, 0], y=b[:, 1], mode="markers+text", name="Microscope B", marker=dict(color="#0072B2"), text=labels_b, textposition="bottom center", textfont=dict(color="#0072B2")), row=1, col=1)
    transform = app.storage.user.get("transform")
    if transform is not None and calibrate_a_positions is not None and calibrate_b_positions is not None:
        a_transformed = apply_transform(
            np.array(calibrate_a_positions),
            np.array(transform["centroid_a"]),
            np.array(transform["centroid_b"]),
            transform["scaling"],
            np.array(transform.get("mirror", [[1, 0], [0, 1]])),
            np.array(transform["rotation"])
        )
        fig.add_trace(go.Scatter(x=a_transformed[:, 0], y=a_transformed[:, 1], mode="markers+text", name="Microscope A (transformed)", marker=dict(color="#D55E00"), text=labels_a, textposition="top center", textfont=dict(color="#D55E00")), row=1, col=2)
        fig.add_trace(go.Scatter(x=b[:, 0], y=b[:, 1], mode="markers+text", name="Microscope B", marker=dict(color="#0072B2"), text=labels_b, textposition="bottom center", textfont=dict(color="#0072B2"), showlegend=False), row=1, col=2)
    calibration_plot.update_figure(fig)

def sync():
    available_transforms = os.listdir("available_transforms") if os.path.exists("available_transforms") else []
    update_file_table(transform_file_table, available_transforms)

    relocate_position_file = app.storage.user.get("relocate_position_file")
    if relocate_position_file:
        relocate_position_label.text = f"Position file in memory: {relocate_position_file}"
    else:
        relocate_position_label.text = "Position file in memory:"

    relocate_positions = app.storage.user.get("relocate_positions")
    update_position_table(relocate_position_table, relocate_positions)

    calibrate_a_position_file = app.storage.user.get("calibrate_a_position_file")
    if calibrate_a_position_file:
        calibrate_a_position_label.text = f"Position file in memory: {calibrate_a_position_file}"
    else:
        calibrate_a_position_label.text = "Position file in memory:"

    calibrate_b_position_file = app.storage.user.get("calibrate_b_position_file")
    if calibrate_b_position_file:
        calibrate_b_position_label.text = f"Position file in memory: {calibrate_b_position_file}"
    else:
        calibrate_b_position_label.text = "Position file in memory:"

    calibrate_a_positions = app.storage.user.get("calibrate_a_positions")
    update_position_table(calibrate_a_position_table, calibrate_a_positions)

    calibrate_b_positions = app.storage.user.get("calibrate_b_positions")
    update_position_table(calibrate_b_position_table, calibrate_b_positions)

def make_upload_handler(source: str):
    async def handle_upload(e: events.UploadEventArguments):
        content = await e.file.read()
        try:
            app.storage.user[f"{source}_position_file"] = e.file.name
            app.storage.user[f"{source}_positions"] = read_positions(e.file.name, content)
            sync()
            e.sender.reset()
        except ValueError as ex:
            ui.notify(f"Error: {ex}")

    return handle_upload

def calculate_transform_handle():
    positions_a = app.storage.user.get("calibrate_a_positions")
    positions_b = app.storage.user.get("calibrate_b_positions")

    if positions_a is None or positions_b is None:
        transform_status_label.text = "Please upload position files for both microscopes before calculating the transform."
        return

    if len(positions_a) != len(positions_b):
        transform_status_label.text = "The number of positions in both files must be the same."
        return

    centroid_a, centroid_b, scaling, mirror, rotation = calculate_transform(positions_a, positions_b)
    app.storage.user["transform"] = {
        "centroid_a": centroid_a.tolist(),
        "centroid_b": centroid_b.tolist(),
        "scaling": float(scaling),
        "mirror": mirror.tolist(),
        "rotation": rotation.tolist()
    }

    update_calibration_plot()

    if not transform_filename_input.value:
        transform_status_label.text = "Transform calculated successfully, but please enter a name for the transform to save it."
        return

    try:
        # write_transform() itself rejects an existing filename atomically,
        # so two users saving the same name at the same moment can't clobber
        # each other - whoever's write lands second gets this error instead.
        write_transform(app.storage.user["transform"], transform_filename_input.value)
    except FileExistsError:
        transform_status_label.text = "A transform with that name already exists. Please choose a different name to save this transform."
        return
    except ValueError as ex:
        transform_status_label.text = str(ex)
        return

    update_transform_dropdown()
    transform_status_label.text = f"Transform calculated and saved as '{transform_filename_input.value}'."
    sync()

def transform_positions(transform_name):
    selected_transform = read_transform(transform_name)
    centroid_a = np.array(selected_transform["centroid_a"])
    centroid_b = np.array(selected_transform["centroid_b"])
    scaling = selected_transform["scaling"]
    mirror = np.array(selected_transform.get("mirror", [[1, 0], [0, 1]]))
    rotation = np.array(selected_transform["rotation"])
    positions = app.storage.user.get("relocate_positions")

    offset = np.array([offset_x_input.value or 0, offset_y_input.value or 0])
    relocated_positions = apply_transform(positions, centroid_a, centroid_b, scaling, mirror, rotation) + offset
    # Unique per-call temp file, read into memory, then deleted immediately -
    # no shared filename, and nothing lingers on disk afterward.
    temp_path = write_positions(relocated_positions, f"temp_{uuid.uuid4().hex}", "czstm")
    with open(temp_path, "rb") as f:
        content = f.read()
    os.remove(temp_path)
    original_name = app.storage.user.get("relocate_position_file", "")
    base = os.path.splitext(os.path.basename(original_name))[0] if original_name else "positions"
    ui.download(content, filename=f"{base}_relocated.czstm")

def update_transform_dropdown():
    available_transforms = os.listdir("available_transforms") if os.path.exists("available_transforms") else []
    transform_dropdown.clear()
    with transform_dropdown:
        for file in available_transforms:
            name = os.path.basename(file).removesuffix(".json")
            ui.item(name, on_click=lambda n=name: transform_positions(n))

def clear_all_data():
    # app.storage.user is scoped to this browser session, so this only
    # clears the data belonging to the person who clicked the button -
    # not everyone connected to the app.
    app.storage.user.clear()
    offset_x_input.value = 0
    offset_y_input.value = 0
    sync()

with ui.tabs().classes("w-full") as tabs:
    relocate_tab = ui.tab("Relocate")
    calibrate_tab = ui.tab("Calibrate")
with ui.tab_panels(tabs, value=relocate_tab).classes("w-full"):
    with ui.tab_panel(relocate_tab):
        ui.upload(label="Position file", max_files=1, auto_upload=True, on_upload=make_upload_handler("relocate"))
        relocate_position_label = ui.label("Position file in memory:").classes("text-gray-400 text-sm")
        relocate_position_table = ui.table(columns=position_columns, rows=[])
        with ui.row().classes("items-center gap-4"):
            offset_x_input = ui.number(label="X Offset", value=0, precision=0).classes("w-32")
            offset_y_input = ui.number(label="Y Offset", value=0, precision=0).classes("w-32")
        transform_dropdown = ui.dropdown_button("Apply transform", auto_close=True)
        transform_dropdown.bind_enabled_from(relocate_position_table, 'rows', backward=lambda rows: len(rows) > 0)
    with ui.tab_panel(calibrate_tab):
        with ui.splitter() as splitter:
            with splitter.before:
                with ui.column().classes("pr-8"):
                    ui.label("From Microscope A").classes("text-h6")
                    ui.upload(label="Position file", max_files=1, auto_upload=True, on_upload=make_upload_handler("calibrate_a"))
                    calibrate_a_position_label = ui.label("Position file in memory:").classes("text-gray-400 text-sm")
                    calibrate_a_position_table = ui.table(columns=position_columns, rows=[])
            with splitter.after:
                with ui.column().classes("pl-8"):
                    ui.label("To Microscope B").classes("text-h6")
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
transform_file_table = ui.table(columns=file_columns, rows=[]).classes("w-[1000px]")
for _col in ("flip_x", "flip_y"):
    transform_file_table.add_slot(f"body-cell-{_col}", '<q-td :props="props"><q-checkbox :model-value="props.value" disable /></q-td>')
ui.button("Clear all data", on_click=clear_all_data)
update_transform_dropdown()
ui.timer(2, sync)
ui.run(port=80, storage_secret=get_storage_secret())