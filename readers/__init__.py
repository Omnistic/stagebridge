from .zeiss import ZeissReader

_zeiss_reader = ZeissReader()

def read_positions(filename, content):
    match filename.split(".")[-1].lower():
        case "czstm":
            return _zeiss_reader.read(content)
        case _:
            raise ValueError(f"Unsupported file type: {filename}")