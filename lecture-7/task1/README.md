# Task 1: API, systemd и ротация логов

Приложение в `app.py` не меняется. systemd запускает его, направляет stdout
и stderr в `/home/logs/app.log` и ограничивает ресурсы. Таймер раз в 5 секунд
запускает простой Bash-скрипт `rotate.sh`.

Когда размер `app.log` достигает **1 MiB (1 048 576 байт)**, скрипт:

1. Удаляет старую копию `app.log.2`.
2. Переименовывает `app.log.1` в `app.log.2`, если она есть.
3. Копирует текущий `app.log` в `app.log.1`.
4. Обнуляет `app.log`, сохраняя сам файл открытым для приложения.
5. Печатает дату и длительность ротации; systemd записывает строку
   в `/home/log_rotates.log`.

Получается максимум **три файла приложения**: `app.log`, `app.log.1`, `app.log.2`.
Директория `/home/logs` предназначена для этого API; чужие файлы скрипт не удаляет.

## Установка

Нужен Linux с работающим systemd, Python 3 и модулем venv. Для Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv curl
cd /home/beknur/devops1/lecture-7/task1
sudo ./setup.sh
curl --fail http://localhost:8000/health
```

`setup.sh` копирует приложение в `/opt/simple-api`, создаёт отдельный venv,
устанавливает зависимости и systemd-юниты, включает автозапуск и запускает их.
Повторный запуск обновляет установку и перезапускает сервис.
Порт 8000 должен быть свободен.

## Проверка

```bash
systemctl status simple-api.service --no-pager
systemctl list-timers logrotate-api.timer

# Создать запросами достаточно строк для ротации.
for i in $(seq 1 20000); do
    curl --fail --silent "http://localhost:8000/items/$i" > /dev/null
done

# Можно запустить проверку размера, не дожидаясь таймера.
sudo systemctl start logrotate-api.service
ls -lh /home/logs
cat /home/log_rotates.log

# Проверить лимиты CPU, памяти и числа процессов/потоков.
systemctl show simple-api.service -p MemoryMax -p CPUQuotaPerSecUSec -p TasksMax
```

`MemoryMax=256M`, `CPUQuota=50%`, `TasksMax=50` заданы в `simple-api.service`.
`DynamicUser=yes` запускает API без root; `Restart=on-failure` перезапускает
процесс при падении. `/health` позволяет проверять доступность HTTP.

Локально проверены четыре последовательные ротации: максимум три файла,
правильное содержимое копий и продолжение записи через открытый файл.
Синтаксис Bash и systemd-юнитов проверен; для проверки юнитов использовались
временные пути установки. Сами сервисы в рабочей среде агента не запускались:
здесь нет systemd в роли системного менеджера.

## Что учитывать

**1 MiB здесь — порог ротации, а не строгий запрет превышения размера.** Между
срабатываниями таймера файл может вырасти больше, и копия сохранит этот размер.
Если преподаватель требует, чтобы каждый файл никогда не превышал 1 MB,
одного периодического таймера недостаточно: нужен отдельный обработчик потока
логов. Также между `cp` и `truncate` могут потеряться строки, записанные
приложением в этот короткий промежуток. Это ограничение простого copy/truncate.

Проверка размера без ротации ничего не записывает в `/home/log_rotates.log`.
Для проверки скрипта в другой папке можно передать `LOG_DIR=/tmp/my-test-logs`.
Вручную запускай ротацию через systemctl, чтобы она не пересекалась с таймером.

Документация: [systemd.timer](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html),
[перенаправление вывода systemd](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html#StandardOutput=).
