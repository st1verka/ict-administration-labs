# Лабораторная работа № 5. Внутренний GitLab, единый вход, nginx и раннеры

## Цель работы

А вот и она - работа потратившая кучу времени и сил. Мы дошли до нее.

Итак список того что надо: развернуть собственный GitLab, настроить единый вход через Keycloak, организовать доступ через nginx потом подключить два типа GitLab Runner и настроить автоматическую сборку приложения. Дополнительно настроить мониторинг nginx с помощью Prometheus и Grafana.

В общем дел куча.

## 1. Подготовка стенда

Для выполнения работы мы использовали Docker. Опять.

В Docker Compose подготовили GitLab, Keycloak, nginx, Grafana, Prometheus и GitLab Runner. Дополнительно создали Kubernetes-кластер с помощью kind.

Основные адреса проживающих:

| Адрес | Назначение |
|---|---|
| `http://keycloak.local:8080` | Keycloak |
| `https://gitlab.local` | GitLab |
| `https://registry.gitlab.local` | Container Registry |
| `http://grafana.local:3000` | Grafana |
| `http://localhost:9090` | Prometheus |

## 2. Настройка единого входа через Keycloak

Сначала мы настроили Keycloak для централизованной авторизации.

Создали realm `devplatform`, добавили клиентов `gitlab` и `grafana`, а также пользователя `labuser`.

После этого подключили GitLab и Grafana через OpenID Connect. Благодаря этому пользователь может входить в оба приложения с одной учётки.

Проверили настройки Keycloak и созданные клиенты.

![01](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/01-keycloak-oidc-discovery.png)

![02](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/02-keycloak-clients.png)

![03](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/03-keycloak-test-user.png)

Затем проверили кнопку входа через Keycloak в GitLab.(работает)

![04](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/04-gitlab-keycloak-button.png)

После этого выполнили вход в GitLab и Grafana под одной учётной записью.(успешно)

![06](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/06-gitlab-sso-labuser.png)

![07](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/07-grafana-sso-labuser.png)

## 3. Настройка nginx и HTTPS

Далее мы настроили nginx, который принимает запросы пользователей и перенаправляет их на нужные нам сервисы.

Для GitLab и Container Registry настроили отдельные адреса и HTTPS.

Также добавили несколько правил:
- Перенаправление HTTP на HTTPS.
- Ограничение доступа к административной панели.
- Ограничение количества запросов к странице входа.
- Закрытие служебных адресов от внешнего доступа.

Для локального стенда создали самоподписанный сертификат.

Проверили перенаправление на HTTPS.

![08](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/08-nginx-https-redirect.png)

Проверили правила доступа.

![09](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/09-nginx-access-rules.png)

Отдельно проверили ограничение запросов. При превышении установленного лимита nginx возвращает код `429`.

![10](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/10-nginx-login-rate-limit.png)

Также проверили доступ к Container Registry. Без авторизации сервер возвращает `401`.

![11](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/11-registry-https.png)

В конце повторно проверили вход в GitLab через HTTPS.

![12](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/12-gitlab-sso-https.png)

## 4. Настройка GitLab Runner

Следующим этапом мы создали приватный проект `devplatform-service` и настроили два Runner:

- `static` — обычный Docker Runner.
- `dynamic` — Kubernetes Runner.

Они нужны для автоматического выполнения проверок и сборки приложения.

Сначала проверили созданный проект.

![13](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/13-gitlab-ci-project.png)

### 4.1. Docker Runner

Значится зарегистрировали обычный Docker Runner. Он работает постоянно и запускает отдельный контейнер для каждой задачи.

Проверили его состояние и запустили тестовую задачу.

![14](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/14-static-runner-online.png)

![15](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/15-static-runner-job.png)

### 4.2. Kubernetes Runner

Затем создали Kubernetes-кластер с помощью kind. В нём настроили отдельное пространство для Runner.

Особенность этого варианта заключается в том, что для каждой задачи создаётся отдельный под, который удаляется после завершения работы.

Проверили состояние кластера.

![16](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/16-kind-cluster-ready.png)

Убедились, что оба Runner доступны в GitLab.

![17](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/17-both-runners-online.png)

Проверили создание под и выполнение задачи.

![18](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/18-kind-job-pod.png)

![19](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/19-dynamic-runner-job.png)

После выполнения задачи проверили удаление под.

![20](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/20-kind-pod-cleanup.png)

Также увеличили количество одновременно выполняемых задач до двух и проверили параллельную работу.

![21](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/21-parallel-kind-pods.png)

## 5. Создание приложения и настройка CI/CD

Для проверки Runner мы собрали не  без посторонней помощи небольшое приложение на Flask.

В приложении предусмотрены два адреса:
- `/` — возвращает информацию о сервисе.
- `/health` — показывает состояние приложения.

Также добавили автоматические тесты.

В файле `.gitlab-ci.yml` настроили три задачи:

| Задача | Назначение |
|---|---|
| `check_syntax` | Проверка синтаксиса Python |
| `unit_tests` | Запуск тестов приложения |
| `build_publish` | Сборка и публикация Docker-образа |

Первые две задачи запускаются параллельно на Kubernetes Runner. После успешных проверок Docker Runner собирает образ и отправляет его в Container Registry. Проверяем.

Проверили успешное выполнение тестов.

![22](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/22-flask-checks-passed.png)

Затем проверили весь пайплайн. Пайплайн № 4 завершился успешно.

![23](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/23-full-pipeline-passed.png)

Отдельно проверили сборку и публикацию Docker-образа.

![24](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/24-static-build-publish.png)

В Container Registry проверили опубликованные образы. Они получили теги `latest` и `5fb7dea1`.

![25](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/25-registry-image-tags.png)

## 6. Настройка мониторинга nginx

Для мониторинга мы подключили три компонента:

- nginx Exporter — собирает показатели nginx.
- Prometheus — получает и хранит метрики.
- Grafana — отображает информацию в виде графиков.

Для начала включили `stub_status` и настроили передачу показателей через Exporter.

Проверили, что Prometheus успешно подключился к Exporter.

![26](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/26-prometheus-nginx-target-up.png)

Затем проверили получение метрик nginx.

![27](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/27-prometheus-nginx-metrics.png)

## 7. Создание дашборда Grafana

После настройки мониторинга мы создали дашборд Grafana.

На нём в этот раз разместили четыре показателя:

1. Состояние nginx.
2. Количество активных соединений.
3. Количество HTTP-запросов в секунду.
4. Разницу между принятыми и обработанными соединениями.

Данные обновляются автоматически каждые 10 секунд для удобства.

![28](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/28-grafana-nginx-dashboard.png)

## 8. Настройка уведомлений

Дополнительно мы настроили три правила оповещений в Prometheus.

| Название | Назначение |
|---|---|
| `NginxTelemetryUnavailable` | Проверка доступности метрик |
| `NginxHighActiveConnections` | Контроль большого количества соединений |
| `NginxUnhandledConnections` | Контроль необработанных соединений |

Для проверки остановили nginx Exporter. После этого первое правило перешло в состояние `Firing`.

Затем снова запустили Exporter. Метрики восстановились, а уведомление вернулось в нормальное состояние.

![29](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/29-prometheus-nginx-alerts.png)

![30](https://raw.githubusercontent.com/st1verka/ict-administration-labs/main/lab5/screenshots/30-nginx-alert-firing.png)

## 9. Возникшие трудности

А вот и блок достойный внимания. В данной работе все было не так просто.

Вот такую табличку приколов получилось собрать по ходу выполнения:

| Проблема | Решение |
|---|---|
| Необходимость согласовать адреса при переходе на HTTPS. | Настроили доменные имена и сертификат. |
| Не удавалось сразу проверить ограничение запросов nginx. | Выполнили параллельную отправку запросов. |
| Kubernetes Runner использовал неподходящий образ для ARM64. | Настроили выбор подходящей архитектуры. |
| Kubernetes не мог скачать некоторые образы. | Загрузили их локально и передали в кластер. |
| Задачи Kubernetes Runner выполнялись последовательно. | Увеличили количество одновременных задач до двух. |
| Registry не доверял самоподписанному сертификату. | Добавили сертификат в хранилище доверенных сертификатов. |

Когда все исправили перезапустили и нормально.

## 10. Итог работы

Ну что сказать, работа обьемная и не сильно простая. Однако довольно интересная. Кучу всего сделали не все с первого раза, лабораторная достойна называться сложной.

>[!IMPORTANT] 
>Вы победили!
