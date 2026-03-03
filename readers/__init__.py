from .zeiss import ZeissReder

def read_positions(filename, content):
    match filename.split(".")[-1].lower():
        case "czstm":
            return ZeissReder().read(content)
        case _:
            raise ValueError(f"Unsupported file type: {filename}")