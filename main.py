import re
from functools import reduce
import typer
from typing import List
from functools import cmp_to_key


ROW_LEN = 4
EXIST_ROW_LEN = 4
SEP = '-'
SEP_INDEX = 1
ENV_REGEXP = re.compile(r'\$\{?([^\s{}:]+)(:([^{}]+)?)?}?')
ROW_REGEXP = re.compile(r'\|([^|]+)' * EXIST_ROW_LEN + r'\|')
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
        row.append(group)
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
    return sorted(rows, key=cmp_to_key(lambda x, y: x[0] <= y[0] and x[3] >= y[3]))


def create_table(rows: list):
    table = ''
    for row in rows:
        table += '|' + reduce(lambda x, y: x + '|' + y, row) + '|\n'
    return table


@app.command()
def create(
        config_file: List[str] = typer.Option(default=[]),
        output: str = typer.Option(default=None),
        exist_table: List[str] = typer.Option(default=None)
           ):

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
            rows += existed_rows

    rows = sort_rows(rows)
    rows = remove_duplicates(rows)

    rows.insert(0, ['env', 'default', 'secret', 'description'])
    rows.insert(1, [SEP] * ROW_LEN)
    for i in range(ROW_LEN):
        normalize_row(rows, i)

    print('Total: %d' % (len(rows) - 1))
    table = create_table(rows)
    if output is None:
        print(table)
    else:
        f = open(output, "a")
        f.write(table)
        f.close()


if __name__ == '__main__':
    app()
