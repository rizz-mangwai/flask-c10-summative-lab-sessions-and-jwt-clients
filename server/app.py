from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Mood, UserSchema, MoodSchema


class Signup(Resource):
    def post(self):
        data = request.get_json(force=True)

        if not data.get('username') or not data.get('password'):
            return {'error': 'Username and password are required'}, 422

        if data.get('password') != data.get('password_confirmation'):
            return {'error': 'Passwords do not match'}, 422

        try:
            user = User(username=data['username'])
            user.password_hash = data['password']
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {'error': 'Username already taken'}, 422
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 422

        session['user_id'] = user.id
        return UserSchema().dump(user), 201


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {}, 401

        user = User.query.get(user_id)
        if not user:
            return {}, 401

        return UserSchema().dump(user), 200


class Login(Resource):
    def post(self):
        data = request.get_json(force=True)
        user = User.query.filter_by(username=data.get('username')).first()

        if user and user.authenticate(data.get('password')):
            session['user_id'] = user.id
            return UserSchema().dump(user), 200

        return {'error': 'Invalid username or password'}, 401


class Logout(Resource):
    def delete(self):
        if not session.get('user_id'):
            return {'error': 'Unauthorized'}, 401

        session.pop('user_id', None)
        return {}, 204


class MoodIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        pagination = Mood.query.filter_by(user_id=user_id)\
            .order_by(Mood.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

        return {
            'moods': MoodSchema(many=True).dump(pagination.items),
            'total': pagination.total,
            'pages': pagination.pages,
            'page': pagination.page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
        }, 200

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        data = request.get_json(force=True)

        try:
            mood = Mood(
                mood_score=data['mood_score'],
                note=data.get('note'),
                energy_level=data.get('energy_level'),
                user_id=user_id
            )
            db.session.add(mood)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 422

        return MoodSchema().dump(mood), 201


class MoodDetail(Resource):
    def get(self, id):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        mood = Mood.query.filter_by(id=id, user_id=user_id).first()
        if not mood:
            return {'error': 'Mood entry not found'}, 404

        return MoodSchema().dump(mood), 200

    def patch(self, id):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        mood = Mood.query.filter_by(id=id, user_id=user_id).first()
        if not mood:
            return {'error': 'Mood entry not found'}, 404

        data = request.get_json(force=True)

        try:
            if 'mood_score' in data:
                mood.mood_score = data['mood_score']
            if 'note' in data:
                mood.note = data['note']
            if 'energy_level' in data:
                mood.energy_level = data['energy_level']

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 422

        return MoodSchema().dump(mood), 200

    def delete(self, id):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401

        mood = Mood.query.filter_by(id=id, user_id=user_id).first()
        if not mood:
            return {'error': 'Mood entry not found'}, 404

        db.session.delete(mood)
        db.session.commit()
        return {}, 204


# Register routes
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(MoodIndex, '/moods', endpoint='moods')
api.add_resource(MoodDetail, '/moods/<int:id>', endpoint='mood_detail')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
