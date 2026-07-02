from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
from models import User
from routers.auth import hash_password

program_is_completed = "Программа завершена"


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
            print(f'Вы ввели {mode}.\nВведите: 1, 2, exit')
    return mode

def data_for_function(mode):
    if mode == '1':
        email = input('Введите email >> ').strip()
        name = input('Введите имя администратора >> ').strip()
        phone = input('Введите телефон администратора >> ').strip()
        password = input('Введите пароль >> ').strip()
        if not email or not password:
            print(f"Ошибка: email и пароль обязательны.\n{program_is_completed}")
            return None
        if not name:
            name = 'No_name_Administrator'
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
    print(program_is_completed)
    return None


def add_admin(db: Session, user: User, buff_password: str) -> None:
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        print(f"Пользователь с таким email: {user.email} уже существует!!!\n"
              f"{program_is_completed}")
        return
    existing_phone = db.query(User).filter(User.phone == user.phone).first()
    if existing_phone:
        print(f"Пользователь с таким телефоном: {user.phone} уже существует!!!\n"
              f"{program_is_completed}")
        return
    db.add(user)
    print(f"\nСоздан администратор!\n"
          f"Не забудьте учетные данные для входа:\n"
          f"Ваш email: {user.email}\n"
          f"Ваш пароль: {buff_password}\n"
          f"{program_is_completed}")
    db.commit()


def del_admin(db: Session, email: str) -> None:
    existing = db.query(User).filter(User.email == email).first()

    if existing and existing.is_admin:
        db.delete(existing)
        db.commit()
        print(f"Администратор: {email} удалён\n{program_is_completed}")
    else:
        print(f"Администратор: {email} не найден\n{program_is_completed}")


def main() -> None:
    print("Создание таблиц (если не существуют)...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        mode = select_choosing_mode_operation_with_administrator_rights()
        if mode == '1':
            dict_user = data_for_function(mode)
            buff_password = dict_user['password']
            dict_user['hashed_password'] = hash_password(dict_user.pop('password'))
            user = User(**dict_user)
            add_admin(db, user, buff_password)
        elif mode == '2':
            email = data_for_function(mode)
            del_admin(db, email)
        else:
            print(program_is_completed)

    finally:
        db.close()


if __name__ == "__main__":
    main()