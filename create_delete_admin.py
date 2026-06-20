from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
from models import User
from routers.auth import hash_password


def select_choosing_mode_operation_with_administrator_rights():
    print(f'1 - добавить администратора системы;\n'
          f'2 - удалить администратора системы;\n'
          f'exit - выйти из программы;\n')
    mode = None
    while mode not in ['1', '2', 'exit']:
        mode = input(f'Введите:\n"1" - для добавления администратора системы\n'
                     f'"2" - для удаления администратора системы\n'
                     f'exit - выйти из программы\n>> ').strip()
        if mode not in ['1', '2', 'exit']:
            print(f'Вы ввели {mode}. Выбор один из трех: 1, 2, exit')
    return mode

def data_for_function(mode):
    if mode == '1':
        email = input('Введите email >> ').strip()
        name = input('Введите имя администратора >> ').strip()
        phone = input('Введите телефон администратора >> ').strip()
        password = input('Введите пароль >> ').strip()
        if not email or not password:
            print("Ошибка: email и пароль обязательны.")
            return None
        return {
            'email': email,
            'name': name,
            'phone': phone,
            'password': password,
            'is_admin': True
        }
    if mode == '2':
        email = input('Введите email >> ').strip()
        return email
    print('Выход из программы')
    return None


def add_admin(db: Session, user: User) -> None:
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        print(f"  • Пользователь {user.email} уже существует")
        return
    db.add(user)
    print(f"  ✓ Создан пользователь {user.email} (пароль: {user.hashed_password})")
    db.commit()


def del_admin(db: Session, email: str) -> None:
    existing = db.query(User).filter(User.email == email).first()

    if existing and existing.is_admin:
        db.delete(existing)
        db.commit()
        print(f"Администратор {email} удалён")
    else:
        print("Администратор не найден")


def main() -> None:
    print("Создание таблиц (если не существуют)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        mode = select_choosing_mode_operation_with_administrator_rights()
        if mode == '1':
            dict_user = data_for_function(mode)
            dict_user['hashed_password'] = hash_password(dict_user.pop('password'))
            user = User(**dict_user)
            add_admin(db, user)
        elif mode == '2':
            email = data_for_function(mode)
            del_admin(db, email)
        else:
            print('Выход из программы')

    finally:
        db.close()


if __name__ == "__main__":
    main()