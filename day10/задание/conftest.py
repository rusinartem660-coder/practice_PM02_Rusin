import pytest
from fake_validator import FakeValidator

@pytest.fixture(scope="class")
def clean_validator():
    """Чистый валидатор без задержек и хаоса для детерминированных тестов."""
    return FakeValidator(chaos_mode=False, delay=0.0)

@pytest.fixture
def chaos_validator():
    """Валидатор с включенным режимом хаоса."""
    return FakeValidator(chaos_mode=True, delay=0.0)

