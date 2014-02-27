# app.py

import datetime, os

from flask import request, url_for, render_template, escape
from flask.ext.api import FlaskAPI, status, exceptions
from flask.ext.api.decorators import set_renderers
from flask.ext.api.renderers import HTMLRenderer
from flask.ext.api.exceptions import APIException
from flask.ext.sqlalchemy import SQLAlchemy

from sqlalchemy import Column, Integer, String, DateTime, Boolean, desc
from unipath import Path

TEMPLATE_DIR = Path(__file__).ancestor(1).child("templates")

app = FlaskAPI(__name__, template_folder=TEMPLATE_DIR)
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
            'text': escape(self.text),
            'created': str(self.created),
            'url': request.host_url.rstrip('/') + url_for(
                'notes_detail',
                key=self.id
            ),
        }


@app.route("/", methods=['GET'])
@set_renderers([HTMLRenderer])
def index():
    return render_template('index.html')


@app.route("/api/", methods=['GET', 'POST'])
def notes_list():
    """
    List or create notes.
    """
    if request.method == 'POST':
        text = str(request.data.get('text', ''))
        if not text:
            return { "message": "Please enter text" }, status.HTTP_204_NO_CONTENT
        note = Note(text=text)
        db.session.add(note)
        db.session.commit()
        return note.to_json(), status.HTTP_201_CREATED

    # request.method == 'GET'
    return [
        note.to_json() for note in Note.query.filter(
            Note.deleted == False
        ).order_by(
            desc(Note.id),
        )
    ]


@app.route("/api/<int:key>/", methods=['GET', 'PUT', 'DELETE'])
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
        return note.to_json()

    elif request.method == 'DELETE':
        note.deleted = True
        db.session.add(note)
        db.session.commit()
        return '', status.HTTP_204_NO_CONTENT

    # request.method == 'GET'
    if not note:
        raise exceptions.NotFound()
    return note.to_json()


if __name__ == "__main__":
    app.run(debug=True)