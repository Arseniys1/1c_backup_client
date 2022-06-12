from eaZy_backup._path import normalize_dir, remove_space
import re


VARIABLE_REGEX = r"^([a-zA-Z0-9_-]+)=[\"]{0,1}(.*[^\"])[\"]{0,1}$"


class Config:
    def __init__(self, dir_name, dir_path) -> None:
        self.dir_name = dir_name
        self.dir_path = dir_path
        self.files = {}
        self.original_file_names = {}

    def add_file(self, file_name, file_ext, file_lines):
        self.original_file_names[file_name] = file_name + file_ext
        self.files[file_name] = self.search_variables(file_name, file_ext,
                                                      self.search_constructions(file_name, file_ext, file_lines))

    def search_constructions(self, file_name, file_ext, file_lines):
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

    def search_variables(self, file_name, file_ext, file_lines):
        new_file_lines = []
        for index, line in enumerate(file_lines):
            if type(line) is ConfigConstruct:
                for _index, value in enumerate(line.values):
                    parse_variable_result = self.parse_variable(value, file_name, file_ext)
                    if parse_variable_result:
                        line.values[_index] = parse_variable_result
                new_file_lines.append(line)
            else:
                parse_variable_result = self.parse_variable(line, file_name, file_ext)
                if parse_variable_result:
                    new_file_lines.append(parse_variable_result)
                else:
                    new_file_lines.append(line)
        return new_file_lines

    def parse_variable(self, line, file_name, file_ext):
        variable_regex_compiled = re.compile(VARIABLE_REGEX)
        search_result = variable_regex_compiled.search(line)
        if search_result:
            if len(search_result.groups()) == 2:
                return ConfigVariable(search_result.group(1), search_result.group(2))
            else:
                print(
                    "Игнорирую строку: \"" + line + "\" в файле: " +
                    self.dir_path + "\\" + file_name + file_ext +
                    " неверный синтаксис")


class ConfigConstruct:
    def __init__(self, name, values) -> None:
        self.name = name
        self.values = values


class ConfigVariable:
    def __init__(self, name, value) -> None:
        self.name = name
        self.value = value



