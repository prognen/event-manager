from __future__ import annotations

import bcrypt


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()  # Генерация соли
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"), salt
    )  # Хэширование пароля
    return hashed_password.decode("utf-8")  # Возвращаем строковое представление хэша


hashed_password = get_password_hash("123!e5T78")
print(hashed_password)
