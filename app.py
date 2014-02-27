# app.py

import datetime, os, json

from flask import request, url_for, jsonify, make_response
from flask.ext.api import FlaskAPI, status, exceptions
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, Boolean

app = FlaskAPI(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)


class Note(db.Model):

    __tablename__ = "note"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String)
    created = Column(DateTime, default=datetime.datetime.now())
    deleted = Column(Boolean, default=False)

    def __repr__(self):
        return self.text

    def to_json(self):
        return {
            'id': self.id,
            'text': self.text,
            'created': str(self.created),
            'url': request.host_url.rstrip('/') + url_for(
                'notes_detail',
                key=self.id
            ),
        }


@app.route("/", methods=['GET', 'POST'])
def notes_list():
    """
    List or create notes.
    """
    if request.method == 'POST':
        text = str(request.data.get('text', ''))
        note = Note(text=text)
        db.session.add(note)
        db.session.commit()
        return note.to_json(), status.HTTP_201_CREATED

    # request.method == 'GET'
    values = [note.to_json() for note in Note.query.all()]
    response = make_response()
    response.data = json.dumps(values)
    return response


@app.route("/<int:key>/", methods=['GET', 'PUT', 'DELETE'])
def notes_detail(key):
    """
    Retrieve, update or delete note instances.
    """
    note = Note.query.get(key)

    if request.method == 'PUT':
        text = str(request.data.get('text', ''))
        if note:
            note.text = text
        else:
            note = Note(text=text)
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_json())

    elif request.method == 'DELETE':
        db.session.delete(note)
        db.session.commit()
        return '', status.HTTP_204_NO_CONTENT

    # request.method == 'GET'
    if not note:
        raise exceptions.NotFound()
    return jsonify(note.to_json())


if __name__ == "__main__":
    app.run(debug=True)