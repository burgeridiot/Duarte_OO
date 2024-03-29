from flask import Flask, request, jsonify
import serial
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/express'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fingerprint_code = db.Column(db.String(120), unique=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'fingerprint_code': self.fingerprint_code,
            'access_history': [access.date.strftime('%Y-%m-%d %H:%M:%S') for access in self.access_history]
        }

class AccessHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S')
        }

# Inicialize a comunicação serial com o Arduino
arduino = serial.Serial('COM5', 9600)

@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    fingerprint_code = data.get('fingerprint_code')
    user = User(fingerprint_code=fingerprint_code)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User created', 'user': user.to_dict()}), 201

@app.route('/add_access/<user_id>', methods=['POST'])
def add_access(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    access = AccessHistory(user_id=user.id)
    db.session.add(access)
    db.session.commit()
    return jsonify({'message': 'Access time added', 'user': user.to_dict()}), 200

@app.route('/unlock', methods=['POST'])
def unlock_door():
    # Aqui você pode enviar um comando para o Arduino para destravar a porta
    arduino.write(b'unlock')
    return jsonify({'message': 'Comando enviado'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
