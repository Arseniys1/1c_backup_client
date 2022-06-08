class Config:
    def __init__(self, dir_name) -> None:
        self.dir_name = dir_name
        self.files = {}

    def add_file(self, file_name, file_lines):
        self.files[file_name] = file_lines

