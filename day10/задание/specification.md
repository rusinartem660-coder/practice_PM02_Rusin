## 1. Контракт и Форматы Данных

### Сигнатура функции

python

def validate_order(order: dict) -> dict:

    """

    Принимает словарь с данными заказа, проверяет его по бизнес-правилам

    и возвращает словарь с результатами валидации и оценкой риска.

    """

### JSON-схема входных данных (Входной формат)
Определяет структуру и типы полей, которые передаются в систему для проверки.

json

{

  "$schema": "http://json-schema.org/draft-07/schema#",

  "title": "OrderInputSchema",

  "type": "object",

  "properties": {

    "order_id": { 

      "type": "string",

      "description": "Уникальный идентификатор заказа"

    },

    "sum": { 

      "type": "number", 

      "minimum": 0,

      "description": "Сумма заказа"

    },

    "user_created_at": { 

      "type": "string", 

      "format": "date-time",

      "description": "Дата и время регистрации пользователя в формате ISO 8601"

    },

    "items_count": { 

      "type": "integer", 

      "minimum": 0,

      "description": "Количество позиций в заказе"

    },

    "has_alcohol": { 

      "type": "boolean",

      "description": "Флаг наличия алкогольной продукции в заказе"

    },

    "age_verified": { 

      "type": "boolean",

      "description": "Подтвержден ли возраст пользователя"

    },

    "order_time": { 

      "type": "string", 

      "format": "date-time",

      "description": "Время оформления заказа в формате ISO 8601"

    },

    "email_changed_last_hour": { 

      "type": "boolean",

      "description": "Менял ли пользователь email за последний час"

    },

    "delivery_country": { 

      "type": "string", 

      "minLength": 2, 

      "maxLength": 3,

      "description": "Код страны доставки (например, RU, US)"

    },

    "wallet_country": { 

      "type": "string", 

      "minLength": 2, 

      "maxLength": 3,

      "description": "Код страны платежного средства"

    }

  },

  "required": [

    "order_id", 

    "sum", 

    "user_created_at", 

    "items_count", 

    "order_time", 

    "delivery_country", 

    "wallet_country"

  ]

}

### JSON-схема выходных данных (Выходной формат)
Определяет структуру ответа системы валидации.

json

{

  "$schema": "http://json-schema.org/draft-07/schema#",

  "title": "ValidationResultSchema",

  "type": "object",

  "properties": {

    "valid": { 

      "type": "boolean",

      "description": "Результат валидации (true — заказ одобрен, false — отклонен)"

    },

    "reasons": {

      "type": "array",

      "items": { "type": "string" },

      "description": "Список текстовых причин отклонения (пустой, если valid = true)"

    },

    "risk_score": { 

      "type": "number", 

      "minimum": 0.0, 

      "maximum": 1.0,

      "description": "Оценка риска транзакции от 0.0 (безопасно) до 1.0 (высокий риск)"

    }

  },

  "required": ["valid", "reasons", "risk_score"]

}
---

## 2. Бизнес-правила

### Валидация (Влияет на флаг `valid` и список `reasons`):
1. **Правило 1 (Границы суммы):** Сумма заказа должна быть строго больше 0 и строго меньше 1 000 000.
   $$\text{sum} > 0 \quad \text{and} \quad \text{sum} < 1\,000\,000$$
2. **Правило 2 (Лимит нового пользователя):** Если с момента регистрации пользователя прошло менее 7 полных суток (сравниваются `order_time` и `user_created_at`), то сумма заказа не должна превышать 15 000.
   $$\text{Если } (\text{order\_time} - \text{user\_created\_at}) < 7 \text{ дней} \implies \text{sum} \le 15\,000$$
3. **Правило 3 (Количество позиций):** В заказе должно быть не более 50 позиций.
   $$\text{items\_count} \le 50$$
4. **Правило 4 (Алкоголь):** Если в заказе есть алкоголь (`has_alcohol` = true):
   * Возраст пользователя должен быть обязательно подтвержден (`age_verified` = true).
   * Время заказа (`order_time`) должно попадать в интервал с **08:00:00** до **23:00:00** включительно.

### Риск-скоринг (Влияет на `risk_score`):
5. **Правило 5 (Расчет рисков):**
   * Базовый `risk_score` равен `0.0`.
   * Если сумма заказа больше 100 000, `risk_score` принудительно устанавливается в `0.9` (перезаписывая базовый уровень).
   * Если пользователь менял email за последний час (`email_changed_last_hour` = true), то к текущему значению `risk_score` прибавляется `0.2`.
   * Если страна доставки не совпадает со страной кошелька (`delivery_country` != `wallet_country`), то к текущему значению `risk_score` прибавляется `0.3`.
   * Итоговый `risk_score` математически ограничивается сверху значением `1.0` и округляется до 2 знаков после запятой.

### Разрешение конфликтов:
* Все правила валидации применяются **одновременно**. Если заказ нарушает сразу несколько правил, флаг `valid` устанавливается в `false`, а в массив `reasons` записываются сообщения обо всех нарушениях.
* Риск-скоринг рассчитывается независимо от того, прошел ли заказ валидацию по правилам 1–4.

---

## 3. Таблица принятия решений (Decision Table)

| ID | Сумма в норме (0..1M) | Новый юзер (<7д) | Сумма <= 15k | Лимит позиций (<=50) | Алкоголь в заказе | Возраст ок | Время ок (8-23) | Страны совп. | Email изменен | **VALID** | **RISK_SCORE** |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **T1** | Да | Нет | Не важно | Да | Нет | Не важно | Не важно | Да | Нет | **True** | **0.0** |
| **T2** | Нет (0) | Нет | Не важно | Да | Нет | Не важно | Не важно | Да | Нет | **False**| **0.0** |
| **T3** | Да | Да | Нет (>15k) | Да | Нет | Не важно | Не важно | Да | Нет | **False**| **0.0** |
| **T4** | Да | Нет | Не важно | Нет (>50) | Нет | Не важно | Не важно | Да | Нет | **False**| **0.0** |
| **T5** | Да | Нет | Не важно | Да | Да | Нет | Да | Да | Нет | **False**| **0.0** |
| **T6** | Да | Нет | Не важно | Да | Да | Да | Нет | Да | Нет | **False**| **0.0** |
| **T7** | Да (>100k)| Нет | Не важно | Да | Нет | Не важно | Не важно | Да | Да | **True** | **1.0** (0.9+0.2, max 1.0) |
| **T8** | Да (>100k)| Нет | Не важно | Да | Нет | Не важно | Не важно | Нет | Нет | **True** | **1.0** (0.9+0.3, max 1.0) |

---

## 4. Примеры заказов для тестирования

### Пример 1. Валидный заказ (Обычный)
* **Вход (JSON):**
  

json

  {

    "order_id": "ord-001",

    "sum": 4500.00,

    "user_created_at": "2025-12-01T10:00:00",

    "items_count": 3,

    "has_alcohol": false,

    "age_verified": false,

    "order_time": "2026-06-16T14:30:00",

    "email_changed_last_hour": false,

    "delivery_country": "RU",

    "wallet_country": "RU"

  }

* **Выход (Ожидаемый JSON):**
  

json

  {

    "valid": true,

    "reasons": [],

    "risk_score": 0.0

  }

### Пример 2. Ошибка нового пользователя (Превышение суммы)
Пользователь зарегистрирован вчера, но делает покупку на 25 000.
* **Вход (JSON):**


json

  {

    "order_id": "ord-002",

    "sum": 25000.00,

    "user_created_at": "2026-06-15T12:00:00",

    "items_count": 2,

    "has_alcohol": false,

    "age_verified": false,

    "order_time": "2026-06-16T12:00:00",

    "email_changed_last_hour": false,

    "delivery_country": "RU",

    "wallet_country": "RU"

  }

* **Выход (Ожидаемый JSON):**
  

json

  {

    "valid": false,

    "reasons": ["New user order sum limit (15,000) exceeded"],

    "risk_score": 0.0

  }

### Пример 3. Нарушение правил продажи алкоголя ночью
Заказ содержит алкоголь, оформлен в 03:00 ночи, возраст не подтвержден.
* **Вход (JSON):**
  

json

  {

    "order_id": "ord-003",

    "sum": 1200.00,

    "user_created_at": "2020-01-01T00:00:00",

    "items_count": 1,

    "has_alcohol": true,

    "age_verified": false,

    "order_time": "2026-06-16T03:00:00",

    "email_changed_last_hour": false,

    "delivery_country": "RU",

    "wallet_country": "RU"

  }

* **Выход (Ожидаемый JSON):**
  

json

  {

    "valid": false,

    "reasons": [

      "Age verification required for alcohol purchase",

      "Alcohol purchase is allowed only between 08:00 and 23:00"

    ],

    "risk_score": 0.0

  }

### Пример 4. Безопасный дорогой заказ с повышенным риском
Заказ корректен по всем бизнес-правилам, но из-за суммы >100k и несовпадения стран получает максимальный риск-скор.
* **Вход (JSON):**
  

json

  {

    "order_id": "ord-004",

    "sum": 150000.00,

    "user_created_at": "2022-01-01T12:00:00",

    "items_count": 12,

    "has_alcohol": false,

    "age_verified": false,

    "order_time": "2026-06-16T11:00:00",

    "email_changed_last_hour": false,

    "delivery_country": "RU",

    "wallet_country": "US"

  }

* **Выход (Ожидаемый JSON):**
  

json

  {

    "valid": true,

    "reasons": [],

    "risk_score": 1.0

  }

### Пример 5. Множественные нарушения (Конфликтный кейс)
Превышено число позиций, сумма равна 0 (недопустимо), новый юзер пытается купить алкоголь.
* **Вход (JSON):**
  

json

  {

    "order_id": "ord-005",

    "sum": 0.00,

    "user_created_at": "2026-06-15T12:00:00",

    "items_count": 55,

    "has_alcohol": true,

    "age_verified": false,

    "order_time": "2026-06-16T01:00:00",

    "email_changed_last_hour": true,

    "delivery_country": "RU",

    "wallet_country": "KZ"

  }

* **Выход (Ожидаемый JSON):**
  

json

  {

    "valid": false,

    "reasons": [

      "Order sum must be strictly between 0 and 1,000,000",

      "Items count must be 50 or less",

      "Age verification required for alcohol purchase",

      "Alcohol purchase is allowed only between 08:00 and 23:00"

    ],

    "risk_score": 0.5

  }
