from eaZy_backup._path import normalize_dir, remove_space


class Config:
    def __init__(self, dir_name, dir_path) -> None:
        self.dir_name = dir_name
        self.dir_path = dir_path
        self.files = {}
        self.original_file_names = {}

    def add_file(self, file_name, file_ext, file_lines):
        self.original_file_names[file_name] = file_name + file_ext
        self.files[file_name] = self.search_constructions(file_lines)

    @staticmethod
    def search_constructions(file_lines):
        new_file_lines = []
        skip_construct_lines = []
        for i, line in enumerate(file_lines):
            if line in skip_construct_lines:
                continue
            elif "{" in line:
                brace_i = len(line) - 1
                if line[brace_i] == "{":
                    construct_name = line[:brace_i]
                    construct_name = normalize_dir(construct_name)
                    file_lines_slice = file_lines[i + 1:]
                    for ii, _line in enumerate(file_lines_slice):
                        if "}" in _line:
                            construct_values = file_lines_slice[:ii]
                            for iii, construct_value in enumerate(construct_values):
                                construct_values[iii] = remove_space(construct_value)
                            new_file_lines.append(ConfigConstruct(construct_name, construct_values))
                            skip_construct_lines.append(_line)
                            break
                        else:
                            skip_construct_lines.append(_line)
            else:
                new_file_lines.append(line)
        return new_file_lines


class ConfigConstruct:
    def __init__(self, name, values) -> None:
        self.name = name
        self.values = values


