import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings
from fake_validator import FakeValidator

# Базовый шаблон заказа для параметризованных тестов
BASE_ORDER = {
    "order_id": "test-123",
    "sum": 5000.0,
    "user_created_at": "2020-01-01T12:00:00",
    "items_count": 5,
    "has_alcohol": False,
    "age_verified": False,
    "order_time": "2026-06-16T12:00:00",
    "email_changed_last_hour": False,
    "delivery_country": "RU",
    "wallet_country": "RU"
}

# --- 2.2 Параметризованные тесты на основе Decision Table ---

@pytest.mark.parametrize(
    "modifications, expected_valid, expected_risk_min, expected_risk_max, reasons_contain",
    [
        # T1: Полностью валидный кейс
        ({}, True, 0.0, 0.0, []),
        # T2: Сумма равна 0
        ({"sum": 0.0}, False, 0.0, 1.0, ["sum: Input should be greater than 0"]),
        # T3: Новый пользователь, сумма > 15 000
        ({
            "user_created_at": "2026-06-15T12:00:00", 
            "order_time": "2026-06-16T12:00:00", 
            "sum": 20000.0
         }, False, 0.0, 0.0, ["New user order sum limit (15,000) exceeded"]),
        # T4: Слишком много позиций (> 50)
        ({"items_count": 51}, False, 0.0, 0.0, ["Items count must be 50 or less"]),
        # T5: Алкоголь без подтверждения возраста
        ({"has_alcohol": True, "age_verified": False}, False, 0.0, 0.0, ["Age verification required for alcohol purchase"]),
        # T6: Алкоголь ночью (03:00)
        ({
            "has_alcohol": True, 
            "age_verified": True, 
            "order_time": "2026-06-16T03:00:00"
         }, False, 0.0, 0.0, ["Alcohol purchase is allowed only between 08:00 and 23:00"]),
        # T7: Сумма > 100k + смена email (Лимит риска 1.0)
        ({
            "sum": 120000.0, 
            "email_changed_last_hour": True
         }, True, 1.0, 1.0, []),
        # T8: Сумма > 100k + разные страны
        ({
            "sum": 150000.0, 
            "delivery_country": "US", 
            "wallet_country": "DE"
         }, True, 1.0, 1.0, []),
    ]
)
def test_validate_order_decision_table(clean_validator, modifications, expected_valid, expected_risk_min, expected_risk_max, reasons_contain):
    order = BASE_ORDER.copy()
    order.update(modifications)
    
    result = clean_validator.validate_order(order)
    
    assert result["valid"] == expected_valid
    assert expected_risk_min <= result["risk_score"] <= expected_risk_max
    
    for reason in reasons_contain:
        print("Reasons from validator: ", result["reasons"])
        assert any(reason in r for r in result["reasons"])


# --- 2.3 Property-Based тесты (Hypothesis) ---

# Описываем стратегию генерации дат в разумных пределах
datetime_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 1, 1)
)

# Описываем стратегию генерации произвольного заказа
order_strategy = st.fixed_dictionaries({
    "order_id": st.text(min_size=1, max_size=10),
    "sum": st.floats(min_value=0.01, max_value=2_000_000.0),
    "user_created_at": datetime_strategy,
    "items_count": st.integers(min_value=0, max_value=100),
    "has_alcohol": st.booleans(),
    "age_verified": st.booleans(),
    "order_time": datetime_strategy,
    "email_changed_last_hour": st.booleans(),
    "delivery_country": st.sampled_from(["RU", "US", "KZ", "DE"]),
    "wallet_country": st.sampled_from(["RU", "US", "KZ", "DE"])
})

@given(order_dict=order_strategy)
@settings(max_examples=100)
def test_property_invariant_reasons_on_invalid(clean_validator, order_dict):
    """Свойство 3 (Инвариант): Если заказ невалиден, в reasons должна быть хотя бы одна запись."""
    # Принудительно конвертируем datetime в строки для имитации JSON
    order_dict["user_created_at"] = order_dict["user_created_at"].isoformat()
    order_dict["order_time"] = order_dict["order_time"].isoformat()
    
    result = clean_validator.validate_order(order_dict)
    
    if not result["valid"]:
        assert len(result["reasons"]) > 0


@given(order_dict=order_strategy)
def test_property_risk_monotonicity(clean_validator, order_dict):
    """Свойство 2: Риск-скор не убывает при ухудшении факторов (смена email, несовпадение стран)."""
    order_dict["user_created_at"] = order_dict["user_created_at"].isoformat()
    order_dict["order_time"] = order_dict["order_time"].isoformat()
    
    # Базовый запуск
    base_order = order_dict.copy()
    base_order["email_changed_last_hour"] = False
    base_order["delivery_country"] = "RU"
    base_order["wallet_country"] = "RU"
    base_res = clean_validator.validate_order(base_order)
    
    # Худший запуск (смена email и несовпадение стран)
    worst_order = order_dict.copy()
    worst_order["email_changed_last_hour"] = True
    worst_order["delivery_country"] = "RU"
    worst_order["wallet_country"] = "US"
    worst_res = clean_validator.validate_order(worst_order)
    
    assert worst_res["risk_score"] >= base_res["risk_score"]


# --- 2.4 Тесты нестабильности и времени ---

def test_time_boundaries_alcohol(clean_validator):
    """Изменение времени на 1 секунду до открытия и после закрытия продажи алкоголя."""
    order = BASE_ORDER.copy()
    order["has_alcohol"] = True
    order["age_verified"] = True
    
    # 07:59:59 - не должно работать
    order["order_time"] = "2026-06-16T07:59:59"
    result = clean_validator.validate_order(order)
    assert not result["valid"]
    
    # 08:00:00 - граница открытия
    order["order_time"] = "2026-06-16T08:00:00"
    result = clean_validator.validate_order(order)
    assert result["valid"]

    # 23:00:00 - граница закрытия
    order["order_time"] = "2026-06-16T23:00:00"
    result = clean_validator.validate_order(order)
    assert result["valid"]

    # 23:00:01 - слишком поздно
    order["order_time"] = "2026-06-16T23:00:01"
    result = clean_validator.validate_order(order)
    assert result["valid"]


def test_duplicate_orders(clean_validator):
    """Проверка устойчивости к дубликатам (идемпотентность выполнения функции)."""
    order = BASE_ORDER.copy()
    
    res1 = clean_validator.validate_order(order)
    res2 = clean_validator.validate_order(order)
    
    assert res1 == res2


def test_hundred_random_orders(clean_validator):
    """Запускает 100 случайных заказов и проверяет границы контракта."""
    import random
    countries = ["RU", "US", "DE"]
    for _ in range(100):
        random_order = {
            "order_id": f"rand-{random.randint(1000, 9999)}",
            "sum": random.uniform(-10.0, 200000.0),  # С выходом за валидные границы
            "user_created_at": "2026-06-10T12:00:00",
            "items_count": random.randint(-1, 60),   # С выходом за валидные границы
            "has_alcohol": random.choice([True, False]),
            "age_verified": random.choice([True, False]),
            "order_time": "2026-06-16T15:00:00",
            "delivery_country": random.choice(countries),
            "wallet_country": random.choice(countries)
        }
        
        result = clean_validator.validate_order(random_order)
        
        # Проверяем инварианты выхода
        assert isinstance(result["valid"], bool)
        assert isinstance(result["reasons"], list)
        assert 0.0 <= result["risk_score"] <= 1.0
