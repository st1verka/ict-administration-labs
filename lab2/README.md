# Лабораторная работа №2 — Kafka для двух сервисов от команды VGTBLS

## 1. Создание сервисов

Для начала мы создали два сервиса:

- `user-service` — создаёт заказы и отправляет их в Kafka (Producer).
- `picker-service` — получает заказы из Kafka и обрабатывает их (Consumer).

![User Service](./screenshots/01-user-service.png)

*Рисунок 1 — Интерфейс user-service.*

![Picker Service](./screenshots/02-picker-service.png)

*Рисунок 2 — Интерфейс picker-service.*

Для Consumer настроили следующие параметры:

```python
{
    "group.id": "pickers",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
}
```

## 2. Запуск Kafka и создание топика

Для запуска проекта использовали уже знакомый нам Docker Compose:

```bash
docker compose up -d --build
docker compose ps
```

Kafka работает в режиме KRaft, без ZooKeeper.

![Kafka](./screenshots/03-kafka-healthy.png)

*Рисунок 3 — Запущенный брокер Kafka.*

Для создания топика `orders` использовали отдельный скрипт `kafka/init_topic.py`.

В итоге получили это:

| Параметр | Значение |
|---|---|
| Топик | `orders` |
| Партиции | 3 |
| Replication factor | 1 |
| Retention | 7 дней |

![Топик orders](./screenshots/04-orders-topic.png)

*Рисунок 4 — Создание топика orders.*

После этого создали тестовый заказ и проверили его получение сборщиком.

![Создание заказа](./screenshots/05-order-published.png)

*Рисунок 5 — Отправка заказа в Kafka.*

![Обработка заказа](./screenshots/06-order-processed.png)

*Рисунок 6 — Получение заказа сборщиком.*

Все норм идем дальше.

## 3. Проверка партиций и масштабирования

Мы увеличили количество партиций топика `orders` до трёх и запустили несколько экземпляров `picker-service`.

![Партиции](./screenshots/07-orders-three-partitions.png)

*Рисунок 7 — Три партиции топика orders.*

Затем создали новые заказы и проверили их распределение между сборщиками.

![Picker 1](./screenshots/08-picker-1-distribution.png)

*Рисунок 8 — Работа первого сборщика.*

![Picker 2](./screenshots/09-picker-2-distribution.png)

*Рисунок 9 — Работа второго сборщика.*
>[!WARNING]
>Тут был элемент мистики picker 2 отказался видеть заказы но после перепроверки и отправки новых все заработало 

Также запустили четыре сборщика при наличии трёх партиций. Один из них остался без назначенной партиции что нам и надо ведь ограничение 3.

![Четыре сборщика](./screenshots/10-picker-without-partition.png)

*Рисунок 10 — Один сборщик не получил партицию.*

Таким образом, мы убедились, что количество одновременно работающих потребителей одной группы ограничено количеством партиций.

## 4. Проверка остановки и восстановления сборщика

Остановили `picker-service` и отправили три новых заказа через `user-service`.

![Заказы](./screenshots/11-orders-while-picker-down.png)

*Рисунок 11 — Отправка заказов при остановленном сборщике.*

Затем снова запустили сборщик. Он получил накопившиеся сообщения и обработал заказы.

![Восстановление](./screenshots/12-orders-processed-after-restart.png)

*Рисунок 12 — Обработка заказов после перезапуска.*

Мы убедились, что Kafka сохраняет сообщения, пока Consumer отдыхает.

## 5. Работа с Kafka UI

Для просмотра топиков, сообщений и потребителей использовали Kafka UI.

![Топики](./screenshots/13-kafka-ui-orders.png)

*Рисунок 13 — Просмотр топика orders.*

![Consumer Group](./screenshots/14-kafka-ui-pickers.png)

*Рисунок 14 — Consumer group pickers.*

Затем нашли конкретный заказ и проверили его позицию.

- Partition: `0`
- Offset сообщения: `22`
- Current Offset группы: `23`

Это означает, что группа уже прошла сообщение с offset 22.

![Поиск заказа](./screenshots/15-kafka-ui-order-found.png)

*Рисунок 15 — Поиск заказа.*

![Offset](./screenshots/16-kafka-ui-order-committed.png)

*Рисунок 16 — Проверка offset.*

## 6. Повторное чтение сообщений

Мы остановили сборщик и через Kafka UI сбросили offsets группы `pickers` на `Earliest`.

![Сброс offsets](./screenshots/17-kafka-ui-offsets-reset.png)

*Рисунок 17 — Сброс offsets.*

После повторного запуска сборщик заново обработал 34 заказа.

![Повторная обработка](./screenshots/18-picker-replayed-orders.png)

*Рисунок 18 — Повторная обработка сообщений.*

Это значит, что сообщения можно повторно читать без повторной отправки.

## 7. Проверка времени хранения сообщений

Изначально параметр `retention.ms` составлял 604800000 миллисекунд (7 дней).

Для проверки мы временно изменили его на 120000 миллисекунд (2 минуты).

![Настройки retention](./screenshots/19-kafka-ui-retention-settings.png)

*Рисунок 19 — Изменение времени хранения.*

Создали контрольный заказ и проверили его наличие в топике.

![Заказ до удаления](./screenshots/20-kafka-ui-order-before-expiration.png)

*Рисунок 20 — Сообщение до истечения срока хранения.*

После ожидания проверили состояние партиции: First Offset стал равен 24, а контрольное сообщение имело offset 23.

![Заказ после удаления](./screenshots/21-kafka-ui-order-expired.png)

*Рисунок 21 — Удаление старого сообщения.*

После проверки вернули исходное значение `retention.ms`.

## 8. Настройка мониторинга

Для мониторинга подключили Kafka Exporter, Prometheus и Grafana.

В Prometheus настроили сбор метрик с Kafka Exporter с интервалом 15 секунд.

![Prometheus Targets](./screenshots/22-prometheus-kafka-target-up.png)

*Рисунок 22 — Kafka Exporter доступен в Prometheus.*

Проверили количество партиций с помощью запроса:

```promql
kafka_topic_partitions{topic="orders"}
```

Результат — три партиции (хороший результат, православный).

![Количество партиций](./screenshots/23-prometheus-orders-partitions.png)

*Рисунок 23 — Проверка количества партиций.*

В Grafana настроили дашборд со следующими метриками:

**Доступность экспортёра:**

```promql
up{job="kafka-exporter"}
```

**Количество партиций:**

```promql
kafka_topic_partitions{topic="orders"}
```

**Партиции с недостаточной репликацией:**

```promql
sum(kafka_topic_partition_under_replicated_partition{topic="orders"})
```

**Отставание потребителей:**

```promql
kafka_consumergroup_lag_sum{consumergroup="pickers",topic="orders"}
```

![Grafana Query](./screenshots/24-grafana-prometheus-query.png)

*Рисунок 24 — Проверка запросов в Grafana.*

После этого открыли готовый, красивый дашборд.

![Grafana Dashboard](./screenshots/25-grafana-kafka-dashboard.png)

*Рисунок 25 — Дашборд мониторинга Kafka.*

### Проверка Consumer Lag

Остановили сборщик и отправили 20 заказов. Consumer Lag увеличился с 0 до 20.

После запуска сборщика все сообщения были обработаны, а lag вернулся к 0.

![Consumer Lag](./screenshots/26-grafana-kafka-lag-recovery.png)

*Рисунок 26 — Изменение Consumer Lag.*

## 9. Заключение

Работа показалась не сильно сложнее предыдущей за исключением нескольких лаг моментов. В целом уже поинтереснее. Надеемся что так и будет продолжаться.
