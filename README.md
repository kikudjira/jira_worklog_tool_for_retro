# jira_worklog_tool_for_retro

#### Нужно установить:
1. Python3: https://www.python.org/downloads/

##### Mac
1. Открываем Terminal
1. Устанавливаем PIP: sudo easy_install pip
1. Устанавливаем Pandas: pip3 install pandas
1. Устанавливаем Requests: pip3 install requests

##### Windows
1. Открываем Terminal
1. Устанавливаем Pandas: py -m install pandas 
                    или: pip install pandas
1. Устанавливаем Requests: py -m install requests 
                      или: pip install requests

#### Для работы скрипта вам нужно:
1. Скачиваем файлы из репы. Code → Download ZIP.
1. Размещаем папку со скриптом в постоянном месте на диске.
1. Отредактировать название файла credits_exp.py, удалив _exp, чтобы стало credits.py.
1. Открыть credits.py в текстовом редакторе и запольнить необходимыми данными.
1. Положить в папку со скриптом файл notDev.csv

#### Далее делаем так, чтобы скрипт можно было запускать по клику:
##### Mac
1. ПКМ на файле script.py → Нажать ⌥Option → Copy "script.py" as Pathname.
1. Открываем Terminal.
1. Пишем в нем: chmod +x и нажимаем CMD+V → у вас должно получиться: chmod +x path/to/script.py
1. ПКМ на файле script.py в Finder → Open With → Other...
1. Меняем значение Enable внизу открывшегося окна на All Applications
1. Cтавим галочку Always Open With → Находим и выбираем Terminal.app (можно через поиск справа вверху окна) → Жмем Open

##### Windows
1. Можно сразу запускать скрипт двумя кликами по нему

У вас откроется терминал и начнется выполняться скрипт, в следующий раз вы сможет просто два раза кликнут на сам файл script.py