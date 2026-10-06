from .zeiss import ZeissHandler
from .leica import LeicaHandler

_zeiss_handler = ZeissHandler()
_leica_handler = LeicaHandler()

def read_positions(filename, content):
    ext = filename.split(".")[-1].lower()
    match ext:
        case "czstm":
            return _zeiss_handler.read(content)
        case "maf" | "nes" | "rgn":
            return _leica_handler.read(content, ext)
        case _:
            raise ValueError(f"Unsupported file type: {filename}")

def output_format_for(filename) -> str:
    """Format to write for a microscope whose positions were read from filename."""
    ext = filename.split(".")[-1].lower()
    match ext:
        case "czstm":
            return "czstm"
        case "maf" | "nes" | "rgn":
            return "rgn"
        case _:
            raise ValueError(f"Unsupported file type: {filename}")

def write_positions(positions, filename, format: str) -> str:
    path = ""
    match format.lower():
        case "czstm":
            path = f"{filename}.czstm"
            _zeiss_handler.write(positions, path)
        case "rgn":
            path = f"{filename}.rgn"
            _leica_handler.write(positions, path)
        case _:
            raise ValueError(f"Unsupported file format: {format}")
    return path