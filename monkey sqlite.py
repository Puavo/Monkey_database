# -*- coding: utf-8 -*-
"""
    Flaskr
    ~~~~~~

    A microblog example application written as Flask tutorial with
    Flask and sqlite3.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.

Turned into monkey database by Paavo Kivistö

"""

from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash


# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE='monkey.db',
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
	g.sqlite_db.execute('pragma foreign_keys = on')
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
@app.route('/<int:page>')
@app.route('/<int:page>/<string:sort>')
def show_entries(page=1, sort='id'):
    db = get_db()
    cur = db.execute('select mail from entries')
    entries = cur.fetchall()
    for entry in entries:
	cur = db.execute('select * from entries where mail in (select mail1 as mail from friends where mail2=? union select mail2 as mail from friends where mail1=?)', [entry['mail'], entry['mail']])
	number = len(cur.fetchall());
	db.execute('update entries set friend=? where mail=?', [number, entry['mail']]);
	db.commit()

    if sort == 'id':
	cur = db.execute('select * from entries order by id desc')
    elif sort == 'age':
	cur = db.execute('select * from entries order by age asc')
    elif sort == 'name':
	cur = db.execute('select * from entries order by name asc')
    elif sort == 'best':
	cur = db.execute('select * from entries order by best asc')
    elif sort == 'friend':
	cur = db.execute('select * from entries order by friend desc')
    else:
	flash('Unknown sorting argument.');
	cur = db.execute('select * from entries order by id desc')

    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries, page=page, sort=sort)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (name, age, mail, text) values (?, ?, ?, ?)',
                 [request.form['name'], request.form['age'], request.form['mail'], request.form['text']])
    db.commit()
    flash('New monkey was successfully added')
    return redirect(url_for('show_entries'))

@app.route('/edit', methods=['POST'])
def edit_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('update entries set name=?, age=?, mail=?, text=? where mail=?', [request.form['name'], request.form['age'], request.form['mail'], request.form['text'], request.form['oldmail']])
    db.commit()
    flash('Monkey was successfully edited')
    return redirect(url_for('show_entries'))

@app.route('/delete', methods=['POST'])
def delete_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('delete from entries where mail=?', [request.form['mail']])
    db.commit()
    flash('Monkey was successfully removed from the database.')
    return redirect(url_for('show_entries'))

@app.route('/friends/<friend1>&<friend2>', )
def add_friends(friend1, friend2):
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into friends (mail1, mail2) values (?,?)', [friend1, friend2])
    db.commit()
    flash('Friendship added.')
    return redirect(url_for('profile',mail=friend2))

@app.route('/delfriends/<friend1>&<friend2>', )
def delete_friends(friend1, friend2):
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('delete from friends where (mail1=? and mail2=?) or (mail1=? and mail2=?)', [friend1, friend2, friend2, friend1])
    db.execute('update entries set best=null where (mail=? and best=?) or (mail=? and best=?)', [friend1, friend2, friend2, friend1])
    db.commit()
    flash('Friendship removed.')
    return redirect(url_for('profile',mail=friend2))

@app.route('/best/<string:mail>')
@app.route('/best/<string:best>&<string:mail>')
def make_best(mail, best=None):
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    if best is None:
	db.execute('update entries set best=null where mail=?', [mail])
    else:
	db.execute('update entries set best=? where mail=?', [best, mail])
    db.commit()
    flash('Best friend set for the monkey.')
    return  redirect(url_for('profile',mail=mail))

@app.route('/profile/<mail>/')
def profile(mail):
    db = get_db()
    cur = db.execute('select * from entries where mail=?', [mail])
    entry = cur.fetchone()
    if entry is None:
	flash('Profile not found')
	return redirect(url_for('show_entries'))
    cur = db.execute('select * from entries where mail in (select mail1 as mail from friends where mail2=? union select mail2 as mail from friends where mail1=?)', [mail, mail])
    friends = cur.fetchall()
    cur = db.execute('select * from entries where mail<>? and mail not in (select mail1 as mail from friends where mail2=? union select mail2 as mail from friends where mail1=?)', [mail, mail, mail])
    nonfriends = cur.fetchall()
    return render_template('show_profile.html', entry=entry, friends=friends, nonfriends=nonfriends)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


if __name__ == '__main__':
    init_db()
    app.run()
