# https://stackoverflow.com/a/71664198/5122790

from jinja2 import Environment, FileSystemLoader, nodes


def get_variables(path, filename):
    template_variables = set()
    env = Environment(loader=FileSystemLoader(searchpath=path))
    template_source = env.loader.get_source(env, filename)[0]
    parsed_content = env.parse(template_source)
    if parsed_content.body and hasattr(parsed_content.body[0], 'nodes'):
        for variable in parsed_content.body[0].nodes:
            if type(variable) is nodes.Name or type(variable) is nodes.Getattr:
                parsed_variable = parse_jinja_variable(variable)
                if parsed_variable:
                    template_variables.add(parsed_variable)
    return template_variables


def parse_jinja_variable(variable, suffix=''):
    if type(variable) is nodes.Name:
        variable_key = join_keys(variable.name, suffix)
        return variable_key
    elif type(variable) is nodes.Getattr:
        return parse_jinja_variable(variable.node, join_keys(variable.attr, suffix))


def join_keys(parent_key, child_key):
    key = child_key if child_key else parent_key
    if parent_key and child_key:
        key = parent_key + '.' + key
    return key


if __name__ == "__main__":
    variable_keys = get_variables("file/path/", "file.name")
    print(*variable_keys, sep='\n')