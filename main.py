import re
from functools import reduce
import typer
from typing import List
import yaml
import os
import jmespath

ROW_LEN = 4
EXIST_ROW_LEN = 4
SEP = '-'
SEP_INDEX = 1
ENV_REGEXP = re.compile(r'\$\{?([^\s{}:]+)(:([^{}]+)?)?}?')
ROW_REGEXP = re.compile(r'\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|')
app = typer.Typer()


def create_row(regexp_groups: tuple):
    row = [''] * ROW_LEN
    row[0] = regexp_groups[0]
    row[1] = regexp_groups[2]
    if row[1] == '""':
        row[1] = ''
    row[2] = 'false'
    row[3] = ''
    return row


def parse_row(regexp_groups: tuple):
    row = []
    for group in regexp_groups:
        row.append(str(group).strip())
    return row[:]


def remove_duplicates(rows: list):
    envs = set()
    result = []
    for row in rows:
        env = row[0]
        if env not in envs:
            envs.add(env)
            result.append(row)
    return result


def normalize_row(rows: list, col_num: int):
    for row in rows:
        row[col_num] = row[col_num].strip()

    max_len = 0
    for row in rows:
        el = row[col_num]
        max_len = max(len(el), max_len)
    cell_max_len = max_len + 2
    for i in range(len(rows)):
        if i == SEP_INDEX:
            rows[i][col_num] = SEP * cell_max_len
        else:
            cell_len = len(rows[i][col_num])
            rows[i][col_num] = ' ' + rows[i][col_num] + (' ' * (max_len - cell_len)) + ' '


def sort_rows(rows: list):
    return sorted(rows, key=lambda x: x[0])


def build_markdown_table(rows: list):
    table = ''
    for row in rows:
        table += '|' + reduce(lambda x, y: x + '|' + y, row) + '|\n'
    return table


def create_rows(config_file, exist_table, ignoring):
    rows = []
    for file_uri in config_file:
        file = open(file_uri)
        file_data = file.read()
        rows += [create_row(env) for env in ENV_REGEXP.findall(file_data)]
    if exist_table is not None:
        for file_uri in exist_table:
            file = open(file_uri)
            file_data = file.read()
            existed_rows = [parse_row(row) for row in ROW_REGEXP.findall(file_data)]
            existed_rows_map = dict()
            for existed_row in existed_rows:
                existed_rows_map[existed_row[0]] = existed_row
            for i in range(len(rows)):
                row = rows[i]
                existed_row = existed_rows_map.get(row[0])
                if existed_row is not None and (rows[i][3] == '' or rows[i][3] is None):
                    rows[i] = existed_row
    rows = remove_duplicates(rows)
    rows = sort_rows(rows)
    if ignoring is not None:
        file = open(ignoring)
        ignoring_envs = file.readlines()
        rows = list(filter(lambda x: x[0] not in ignoring_envs, rows))
    return rows


def print_result(output, result):
    if output is None:
        print(result)
    else:
        f = open(output, "w")
        f.write(result)
        f.close()


def load_config(config):
    file_data = open(config).read()
    yaml_data = os.path.expandvars(file_data)
    config = yaml.load(yaml_data, yaml.Loader)
    config_file = jmespath.search('\"table.creator\".config', config)
    exist_table = jmespath.search('\"table.creator\".\"exist.table\"', config)
    ignoring = jmespath.search('\"table.creator\".ignoring', config)
    output = jmespath.search('\"table.creator\".output', config)
    return config_file, exist_table, ignoring, output


@app.command("create-env")
def create_env(
        config_file: List[str] = typer.Option(default=[]),
        output: str = typer.Option(default=None),
        exist_table: List[str] = typer.Option(default=None),
        ignoring: str = typer.Option(default=None),
        config: str = typer.Option(default=None)
):
    if config is not None:
        config_file, exist_table, ignoring, output = load_config(config)
    rows = create_rows(config_file, exist_table, ignoring)
    result = ''
    for row in rows:
        result += row[0] + '=' + row[1] + '\n'
    print_result(output, result)


@app.command("create-table")
def create(
        config_file: List[str] = typer.Option(default=[]),
        output: str = typer.Option(default=None),
        exist_table: List[str] = typer.Option(default=None),
        ignoring: str = typer.Option(default=None),
        config: str = typer.Option(default=None)
):
    if config is not None:
        config_file, exist_table, ignoring, output = load_config(config)
    rows = create_rows(config_file, exist_table, ignoring)

    rows.insert(0, ['env', 'default', 'secret', 'description'])
    rows.insert(1, [SEP] * ROW_LEN)
    for i in range(ROW_LEN):
        normalize_row(rows, i)

    print('Total: %d' % (len(rows) - 1))
    table = build_markdown_table(rows)
    print_result(output, table)


if __name__ == '__main__':
    app()
