from .zeiss import ZeissHandler

_zeiss_handler = ZeissHandler()

def read_positions(filename, content):
    match filename.split(".")[-1].lower():
        case "czstm":
            return _zeiss_handler.read(content)
        case _:
            raise ValueError(f"Unsupported file type: {filename}")
        
def write_positions(positions, filename, format: str) -> str:
    path = ""
    match format.lower():
        case "czstm":
            path = f"{filename}.czstm"
            _zeiss_handler.write(positions, path)
        case _:
            raise ValueError(f"Unsupported file format: {format}")
    return path