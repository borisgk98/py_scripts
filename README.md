# Скрипт создания таблицы переменных

## Установка
```shell
python3 -m venv proj_venv
```
Widnows:
```shell
proj_venv/Scripts/activate
```
Linux:
```shell
source proj_venv/bin/activate
```
```shell
pip3 install -r requirements.txt
```

## Запуск
```shell
proj_venv/bin/python main.py --config-file=application.yml --config-file=Dockerfile --exist-table=table.txt --output=result.table.txt
```