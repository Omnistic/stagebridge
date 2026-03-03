from nicegui import events, ui
from readers import read_positions

positions = None

async def handle_upload(e: events.UploadEventArguments):
    content = await e.file.read()
    try:
        positions = read_positions(e.file.name, content)
        print(positions)
    except ValueError as ex:
        ui.notify(f"Error: {ex}")

with ui.tabs().classes("w-full") as tabs:
    relocate = ui.tab("Relocate")
    calibrate = ui.tab("Calibrate")
with ui.tab_panels(tabs, value=relocate).classes('w-full'):
    with ui.tab_panel(relocate):
        ui.upload(label="Upload a position file", max_files=1, auto_upload=True, on_upload=handle_upload)

ui.run(port=80)