# Task 12 — приложение из Task 4 и GitLab CI

В этой папке находится самостоятельная копия API из `task4-api`.
GitLab собирает Docker-образ текущего коммита и отправляет его в Docker Hub.
`GET /` показывает версию приложения, а `GET /health/live` работает без PostgreSQL.
Для задания с публикацией PostgreSQL запускать не требуется: запросы `/health/ready`
и `/db-time` без БД возвращают 503, как предусмотрено в Task 4.

## Что подготовить в GitLab и Docker Hub

1. Создай GitLab-проект. Содержимое **этой папки** должно лежать в корне его репозитория:
   `app.py`, `requirements.txt`, `Dockerfile`, `.dockerignore`, `.gitignore`,
   `.gitlab-ci.yml`, `verify-image.sh` и `README.md`.
2. Защити ветку `main` в настройках Branch rules. Разреши себе push в неё.
3. В Docker Hub создай два репозитория: `app-<твой-ID>-devops2026` и `fastapi-app`.
   В PDF указаны разные имена в пунктах 2 и 5. Поэтому CI собирает образ один раз,
   присваивает ему оба имени с одним SHA и публикует в оба репозитория.
4. Создай Docker Hub access token с правом **Read & Write**.
5. В GitLab → Settings → CI/CD → Variables добавь:

| Имя | Значение | Настройки |
| --- | --- | --- |
| `DOCKERHUB_USERNAME` | Твой Docker Hub username | Protected |
| `DOCKERHUB_TOKEN` | Docker Hub access token | Masked и Protected; expansion выключен |
| `STUDENT_ID` | Твой учебный ID для имени репозитория | Protected |

Токен вводится только в настройках GitLab. Не добавляй его в код, `.env`, команды
с аргументом `--password` или Dockerfile. Не включай `CI_DEBUG_TRACE`.
CI передаёт токен через stdin и удаляет временную Docker-конфигурацию после job;
Dockerfile копирует только приложение и зависимости.
[Документация переменных GitLab](https://docs.gitlab.com/ci/variables/) и
[Docker login](https://docs.docker.com/reference/cli/docker/login/).

## Свой runner

Нужен собственный GitLab Runner с **Docker executor**, тегом `devops-docker`
и поддержкой Docker-in-Docker. Создай project runner в Settings → CI/CD → Runners,
укажи этот тег, включи Protected и отключи Run untagged jobs.
Если runner ещё не установлен, следуй
[официальной инструкции установки](https://docs.gitlab.com/runner/install/).

На машине runner выполни интерактивную регистрацию:

```bash
sudo gitlab-runner register
```

Укажи URL `https://gitlab.com/`, выданный GitLab runner authentication token
(`glrt-...`), executor `docker` и default image `docker:29.1.3-cli`.
Токен runner не совпадает с Docker Hub token.
В созданном `/etc/gitlab-runner/config.toml` проверь блок этого runner:

```toml
[runners.docker]
  image = "docker:29.1.3-cli"
  privileged = true
  volumes = ["/certs/client", "/cache"]
```

Сохрани остальные настройки и токен в этом локальном файле, затем:

```bash
sudo gitlab-runner restart
```

DinD использует отдельный Docker daemon внутри CI и TLS на порту 2376.
`privileged` нужен для DinD; используй этот runner для своего доверенного проекта.
[Регистрация runner](https://docs.gitlab.com/runner/register/),
[Docker-in-Docker с TLS](https://docs.gitlab.com/ci/docker/docker_in_docker/).

## Первая версия

В отдельном локальном клоне нового GitLab-проекта размести перечисленные выше
файлы в корне. Из этого клона выполни:

```bash
git switch -c main
git add app.py requirements.txt Dockerfile .dockerignore .gitignore .gitlab-ci.yml verify-image.sh README.md
git commit -m "Add API and Docker image pipeline"
git push -u origin main
git rev-parse HEAD
```

Если ветка `main` уже существует, используй `git switch main` вместо `git switch -c main`.
Последняя команда показывает полный SHA первого коммита. Сохрани его как `SHA1`.
Дождись зелёного `build_and_push` в GitLab → Build → Pipelines.
Job запускается только при push в защищённую `main`; ручной Run pipeline,
другие ветки и теги не подходят под правило.
[Правила запуска jobs](https://docs.gitlab.com/ci/jobs/job_rules/).

Для проверки на своём компьютере нужны Docker, curl, Python 3 и свободный порт 8080.
Подставь настоящий username и полный SHA:

```bash
bash verify-image.sh docker.io/YOUR_USERNAME/fastapi-app:SHA1 1.0
```

Скрипт делает `docker pull`, запускает скачанный образ с `8080:8000`, проверяет
`/health/live` и версию в `/`, затем удаляет свой контейнер. Ничего не собирается
локально и исходники не монтируются. Если Docker Hub repository private,
перед проверкой выполни `docker login`.

Те же действия вручную, если хочешь оставить контейнер работающим:

```bash
docker pull docker.io/YOUR_USERNAME/fastapi-app:SHA1
docker run --rm -d --name task12-api -p 127.0.0.1:8080:8000 docker.io/YOUR_USERNAME/fastapi-app:SHA1
curl --fail http://127.0.0.1:8080/health/live
curl --fail http://127.0.0.1:8080/
docker stop task12-api
```

## Вторая версия

В `app.py` измени ответ функции `home`: строку версии `1.0` на `2.0`
и сообщение `Hello from FastAPI` на `Hello from FastAPI v2`. Затем:

```bash
git add app.py
git commit -m "Change API response to version 2"
git push origin main
git rev-parse HEAD
```

Сохрани новый SHA как `SHA2`, дождись второго успешного pipeline и проверь обе версии:

```bash
bash verify-image.sh docker.io/YOUR_USERNAME/fastapi-app:SHA1 1.0
bash verify-image.sh docker.io/YOUR_USERNAME/fastapi-app:SHA2 2.0
bash verify-image.sh docker.io/YOUR_USERNAME/app-YOUR_ID-devops2026:SHA2 2.0
```

SHA1 и SHA2 — места для подстановки реальных SHA; это не готовые имена тегов.
В Docker Hub должны быть оба тега в обоих репозиториях.

## Что сдавать и что означают настройки

Сдай ссылку на GitLab-проект, `.gitlab-ci.yml`, этот README, успешные pipelines
и ссылки на образы `docker.io/<username>/app-<ID>-devops2026:<SHA1>` и `<SHA2>`.
Добавь такие же ссылки для `fastapi-app` и результаты проверки версий.

`image:` в `.gitlab-ci.yml` задаёт окружение job: здесь это контейнер с Docker CLI.
Dockerfile описывает другой образ — само Python-приложение, которое job собирает
и публикует. SHA-тег связывает образ с конкретным коммитом, позволяет сравнить версии
и запустить старую. Один тег `latest` при следующей публикации указывает уже на другой
образ. SHA-теги тоже технически перезаписываемы, поэтому не публикуй под старым SHA
изменённый код; для строгой фиксации содержимого используют digest.

Локально проверено: `docker build -t task12-api:local-check .` завершился успешно;
контейнер без PostgreSQL вернул `GET /` с версией `1.0`, `/health/live` — 200,
`/health/ready` и `/db-time` — 503 менее чем за 5 секунд.
Образ запускается от непривилегированного пользователя; в `/app` находятся только
`app.py` и `requirements.txt`. Также проверен синтаксис YAML и shell-скриптов.
Тестовый контейнер удалён после проверки.

Реальные GitLab pipelines, push в Docker Hub и проверка двух опубликованных
SHA-версий выполняются после настройки аккаунтов; локальная сборка не заменяет
эти пункты приёмки.
