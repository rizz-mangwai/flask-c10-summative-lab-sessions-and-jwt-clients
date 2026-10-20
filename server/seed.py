from random import randint
from faker import Faker

from config import app, db
from models import User, Mood

fake = Faker()

with app.app_context():
    print("Seeding database...")

    Mood.query.delete()
    User.query.delete()

    users = []
    for i in range(5):
        user = User(username=f"user{i+1}")
        user.password_hash = "password123"
        db.session.add(user)
        users.append(user)

    db.session.commit()

    for user in users:
        for _ in range(randint(4, 9)):
            mood = Mood(
                mood_score=randint(1, 10),
                note=fake.sentence(),
                energy_level=randint(1, 10),
                user_id=user.id
            )
            db.session.add(mood)

    db.session.commit()
    print("Seeding complete!")
