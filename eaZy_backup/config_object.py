from eaZy_backup._path import normalize_dir, remove_space
import re

from eaZy_backup.exceptions.TwoVariablesWithTheSameName import TwoVariablesWithTheSameName

VARIABLE_REGEX = r"^([a-zA-Z0-9_-]+)\s*=\s*[\"]{0,1}(.*[^\"])[\"]{0,1}\s*$"
SKIP_EXTENSIONS = [".env"]


class Config:
    def __init__(self, dir_name, dir_path) -> None:
        self.dir_name = dir_name
        self.dir_path = dir_path
        self.files = {}
        self.original_file_names = {}
        self.variables = []
        self.constructions = []

    def add_file(self, file_name, file_ext, file_lines):
        self.original_file_names[file_name] = file_name + file_ext
        file_lines = self.search_constructions(file_name, file_ext, file_lines)
        file_lines = self.search_variables(file_name, file_ext, file_lines)
        self.files[file_name] = file_lines

    def search_constructions(self, file_name, file_ext, file_lines):
        new_file_lines = []
        skip_construct_lines = []
        if file_ext in SKIP_EXTENSIONS:
            return new_file_lines
        for i, line in enumerate(file_lines):
            if line in skip_construct_lines:
                continue
            elif "[" in line:
                brace_i = len(line) - 1
                if line[brace_i] == "[":
                    construct_name = line[:brace_i]
                    construct_name = normalize_dir(construct_name)
                    file_lines_slice = file_lines[i + 1:]
                    for ii, _line in enumerate(file_lines_slice):
                        if "]" in _line:
                            construct_values = file_lines_slice[:ii]
                            for iii, construct_value in enumerate(construct_values):
                                construct_values[iii] = remove_space(construct_value)
                            config_construct = ConfigConstruct(construct_name, construct_values, None)
                            self.constructions = config_construct
                            new_file_lines.append(config_construct)
                            skip_construct_lines.append(_line)
                            break
                        else:
                            skip_construct_lines.append(_line)
            else:
                new_file_lines.append(line)
        return new_file_lines

    def search_variables(self, file_name, file_ext, file_lines):
        new_file_lines = []
        if file_ext in SKIP_EXTENSIONS:
            return new_file_lines
        for index, line in enumerate(file_lines):
            if type(line) is ConfigConstruct:
                parse_variable_result = self.parse_variable(line.name, file_name, file_ext)
                if parse_variable_result:
                    line.name = parse_variable_result.value
                for _index, value in enumerate(line.values):
                    parse_variable_result = self.parse_variable(value, file_name, file_ext)
                    if parse_variable_result:
                        line.values[_index] = parse_variable_result.value
                new_file_lines.append(line)
            else:
                parse_variable_result = self.parse_variable(line, file_name, file_ext)
                if parse_variable_result:
                    new_file_lines.append(parse_variable_result.value)
                else:
                    new_file_lines.append(line)
        return new_file_lines

    def parse_variable(self, line, file_name, file_ext):
        variable_regex_compiled = re.compile(VARIABLE_REGEX)
        search_result = variable_regex_compiled.search(line)
        if search_result:
            if len(search_result.groups()) == 2:
                config_variable = ConfigVariable(search_result.group(1), search_result.group(2), line)
                for variable in self.variables:
                    if config_variable.name == variable.name:
                        raise TwoVariablesWithTheSameName(
                            "Две переменные с одинаковым именем."
                            " В одной директории конфигурации не может быть 2 переменных с одинаковым именем")
                self.variables.append(config_variable)
                return config_variable
            else:
                print(
                    "Игнорирую строку: \"" + line + "\" в файле: " +
                    self.dir_path + "\\" + file_name + file_ext +
                    " неверный синтаксис")
        return None

    def files_are_over(self):
        self.replace_vars()

    def replace_vars(self):
        for file_name, file_lines in self.files.items():
            new_file_lines = []
            for i, line in enumerate(file_lines):
                for var in self.variables:
                    if type(line) is ConfigConstruct:
                        line.name = self.replace_var_in_line(line.name, var)
                        for ii, value in enumerate(line.values):
                            line.values[ii] = self.replace_var_in_line(value, var)
                    else:
                        line = self.replace_var_in_line(line, var)
                new_file_lines.append(line)
            self.files[file_name] = new_file_lines

    @staticmethod
    def replace_var_in_line(line, var):
        return line.replace("${" + var.name + "}", var.value)


class ConfigConstruct:
    def __init__(self, name, values, without_parsing) -> None:
        self.name = name
        self.values = values
        self.without_parsing = without_parsing


class ConfigVariable:
    def __init__(self, name, value, without_parsing) -> None:
        self.name = name
        self.value = value
        self.without_parsing = without_parsing
