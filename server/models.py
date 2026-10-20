from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from marshmallow import Schema, fields

from config import db, bcrypt


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column(db.String, nullable=False)

    moods = db.relationship('Mood', back_populates='user', cascade='all, delete-orphan')

    @hybrid_property
    def password_hash(self):
        raise AttributeError('Password hashes may not be viewed.')

    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(password.encode('utf-8'))
        self._password_hash = password_hash.decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))

    @validates('username')
    def validate_username(self, key, username):
        if not username or not username.strip():
            raise ValueError('Username is required')
        return username.strip()

    def __repr__(self):
        return f'<User {self.username}>'


class Mood(db.Model):
    __tablename__ = 'moods'

    id = db.Column(db.Integer, primary_key=True)
    mood_score = db.Column(db.Integer, nullable=False)      # 1-10
    note = db.Column(db.String)                             # optional text
    energy_level = db.Column(db.Integer)                    # 1-10 optional
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('User', back_populates='moods')

    @validates('mood_score')
    def validate_mood_score(self, key, score):
        if score is None or not (1 <= int(score) <= 10):
            raise ValueError('mood_score must be an integer between 1 and 10')
        return int(score)

    @validates('energy_level')
    def validate_energy_level(self, key, level):
        if level is not None and not (1 <= int(level) <= 10):
            raise ValueError('energy_level must be between 1 and 10')
        return level

    def __repr__(self):
        return f'<Mood {self.id} score={self.mood_score}>'


class UserSchema(Schema):
    id = fields.Int()
    username = fields.Str()


class MoodSchema(Schema):
    id = fields.Int()
    mood_score = fields.Int()
    note = fields.Str()
    energy_level = fields.Int()
    created_at = fields.DateTime()
    user_id = fields.Int()