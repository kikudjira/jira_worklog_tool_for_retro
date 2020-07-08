# jira_worklog_tool_for_retro

Mac.
Нужно установить:
1. python3: https://www.python.org/downloads/
2. Устанавливаем PIP: sudo easy_install pip
3. Устанавливаем Pandas: pip3 install pandas
4. Устанавливаем Requests: pip3 install requests

Далее делаем так, чтобы скрипт можно было запускать по клику:
1. Размещаем папку со скриптом в постоянном месте на диске.
2. ПКМ на файле script.py → Get Info → ПКМ на поле Where → Copy
3. Открываем Terminal
4. Пишем в нем: chmod +x + нажимаем CMD+V → у вас должно получиться: chmod +x path/to/script.py
5. ПКМ на файле script.py в Finder → Open With → Other...
6. Меняем значение Enable внизу открывшегося окна на All Applications
7. Находим и выбираем Terminal.app (можно через поиск справа вверху окна) → ставим галочку Always Open With → Жмем Open

У вас откроется терминал и начнется выполняться скрипт, в следующий раз вы сможет просто два раза кликнут на сам файл script.py
