import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pydantic import BaseModel, Field, ValidationError, validator

class OrderModel(BaseModel):
    order_id: str
    sum: float = Field(..., gt=0)
    user_created_at: datetime
    items_count: int = Field(..., ge=0)
    has_alcohol: bool = False
    age_verified: bool = False
    order_time: datetime
    email_changed_last_hour: bool = False
    delivery_country: str = Field(..., min_length=2, max_length=3)
    wallet_country: str = Field(..., min_length=2, max_length=3)

class FakeValidator:
    def __init__(self, chaos_mode: bool = False, delay: float = 0.0):
        self.chaos_mode = chaos_mode
        self.delay = delay

    def validate_order(self, order_dict: dict) -> dict:
        # Симуляция задержки сети/процесса
        if self.delay > 0:
            time.sleep(self.delay)

        # Режим хаоса (5% вероятность вернуть непредсказуемый результат)
        if self.chaos_mode and random.random() < 0.05:
            return {
                "valid": random.choice([True, False]),
                "reasons": ["Chaos magic happened!"],
                "risk_score": random.uniform(-0.5, 2.0)  # Сломанный скор
            }

        try:
            # Сначала валидируем схему через Pydantic
            order = OrderModel(**order_dict)
        except ValidationError as e:
            # Превращаем ошибки Pydantic в красивый плоский список причин
            reasons = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            return {
                "valid": False,
                "reasons": reasons,
                "risk_score": 1.0  # Ошибка схемы считается критическим риском
            }

        valid = True
        reasons = []
        risk_score = 0.0

        # Rule 1: Сумма строго в границах (0 .. 1 000 000)
        if not (0 < order.sum < 1000000):
            valid = False
            reasons.append("Order sum must be strictly between 0 and 1,000,000")

        # Rule 2: Новый пользователь (регистрация менее 7 дней назад)
        is_new_user = (order.order_time - order.user_created_at) < timedelta(days=7)
        if is_new_user and order.sum > 15000:
            valid = False
            reasons.append("New user order sum limit (15,000) exceeded")

        # Rule 3: Количество позиций
        if order.items_count > 50:
            valid = False
            reasons.append("Items count must be 50 or less")

        # Rule 4: Алкоголь
        if order.has_alcohol:
            if not order.age_verified:
                valid = False
                reasons.append("Age verification required for alcohol purchase")
            
            # Время заказа 08:00–23:00 по времени заказа
            order_hour = order.order_time.hour
            order_minute = order.order_time.minute
            order_time_float = order_hour + order_minute / 60.0
            if not (8.0 <= order_time_float <= 23.0):
                valid = False
                reasons.append("Alcohol purchase is allowed only between 08:00 and 23:00")

        # Rule 5: Риск-скоринг
        if order.sum > 100000:
            risk_score = 0.9
        
        if order.email_changed_last_hour:
            risk_score += 0.2
        
        if order.delivery_country != order.wallet_country:
            risk_score += 0.3

        # Ограничиваем риски диапазоном [0.0 .. 1.0]
        risk_score = min(1.0, max(0.0, risk_score))

        return {
            "valid": valid,
            "reasons": reasons,
            "risk_score": round(risk_score, 2)
        }
