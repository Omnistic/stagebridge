from nicegui import events, ui
from readers import read_positions

state = {"positions": None}

def update_table(table, positions):
    table.rows = [{"index": i, "x": pos[0], "y": pos[1]} for i, pos in enumerate(positions)]
    table.update()

async def handle_upload(e: events.UploadEventArguments):
    content = await e.file.read()
    try:
        state["positions"] = read_positions(e.file.name, content)
        update_table(relocate_position_table, state["positions"])
        relocate_position_label.text = f"Position file in memory: {e.file.name} ({len(state['positions'])} positions)"
    except ValueError as ex:
        ui.notify(f"Error: {ex}")

columns = [
    {"name": "index", "label": "Index", "field": "index"},
    {"name": "x", "label": "X", "field": "x"},
    {"name": "y", "label": "Y", "field": "y"}
]

with ui.tabs().classes("w-full") as tabs:
    relocate_tab = ui.tab("Relocate")
    calibrate_tab = ui.tab("Calibrate")
with ui.tab_panels(tabs, value=relocate_tab).classes('w-full'):
    with ui.tab_panel(relocate_tab):
        ui.upload(label="Position file", max_files=1, auto_upload=True, on_upload=handle_upload)
        relocate_position_label = ui.label("Position file in memory:").classes('text-gray-400 text-sm')
        relocate_position_table = ui.table(columns=columns, rows=[])
    with ui.tab_panel(calibrate_tab):c
        with ui.splitter() as splitter:
            with splitter.before:
                with ui.column().classes('pr-8'):
                    ui.label("Microscope A").classes('text-h6')
                    ui.upload(label="Position file", max_files=1, auto_upload=True, on_upload=None)
                    ui.label("Position file in memory:").classes('text-gray-400 text-sm')
            with splitter.after:
                with ui.column().classes('pl-8'):
                    ui.label("Microscope B").classes('text-h6')
                    ui.upload(label="Position file", max_files=1, auto_upload=True, on_upload=None)
                    ui.label("Position file in memory:").classes('text-gray-400 text-sm')
            splitter.enabled = False


ui.run(port=80)