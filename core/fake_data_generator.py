from faker import Faker

from core.database import SessionLocal
from sqlalchemy.orm import Session
from users.models import UserModel
from tasks.models import TaskModel

faker = Faker()


def seed_users(db):
    user = UserModel(username=faker.user_name())
    user.set_password("12345678")
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"user created Username: {user.username} #{user.id}")
    return user


def seed_tasks(db, user, count=10):
    tasks_list = []
    for _ in range(count):
        tasks_list.append(
            TaskModel(
                user_id=user.id,
                title=faker.sentence(nb_words=6),
                description=faker.text(),
                is_completed=faker.boolean()
            )
        )
    db.add_all(tasks_list)
    db.commit()
    print(f"{count} task created for {user.username}")


def main():
    db = SessionLocal()

    try:
        user = seed_users(db)
        seed_tasks(db, user)
    finally:
        db.close()


if __name__ == "__main__":
    main()
