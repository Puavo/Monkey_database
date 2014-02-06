# -*- coding: utf-8 -*-
"""
    monkey Tests
    ~~~~~~~~~~~~

    Tests the monkey application.

    :Original falskr micro blogging
    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.

Edited by Paavo Kivistö to monkey database
"""
import os
import monkey
import unittest
import tempfile


class monkeyTestCase(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""
        self.db_fd, monkey.app.config['DATABASE'] = tempfile.mkstemp()
        monkey.app.config['TESTING'] = True
        self.app = monkey.app.test_client()
        monkey.init_db()

    def tearDown(self):
        """Get rid of the database again after each test."""
        os.close(self.db_fd)
        os.unlink(monkey.app.config['DATABASE'])

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    # testing functions

    def test_empty_db(self):
        """Start with a blank database."""
        rv = self.app.get('/')
        assert b'No monkies here so far' in rv.data

    def test_login_logout(self):
        """Make sure login and logout works"""
        rv = self.login(monkey.app.config['USERNAME'],
                        monkey.app.config['PASSWORD'])
        assert b'You were logged in' in rv.data
        rv = self.logout()
        assert b'You were logged out' in rv.data
        rv = self.login(monkey.app.config['USERNAME'] + 'x',
                        monkey.app.config['PASSWORD'])
        assert b'Invalid username' in rv.data
        rv = self.login(monkey.app.config['USERNAME'],
                        monkey.app.config['PASSWORD'] + 'x')
        assert b'Invalid password' in rv.data

    def test_messages(self):
        """Test that messages work"""
        self.login(monkey.app.config['USERNAME'],
                   monkey.app.config['PASSWORD'])
        rv = self.app.post('/add', data=dict(
            name='Paavo',
	    age=28,
	    mail='paavo.kivisto@gmail.com',
            text='<strong>Kova</strong> koodari!'
        ), follow_redirects=True)
        assert b'No monkies here so far' not in rv.data
        assert b'Paavo' in rv.data
        assert b'paavo.kivisto@gmail.com' in rv.data
        assert b'<strong>Kova</strong> koodari!' in rv.data

    def test_edit(self):
        """Test that profile editing works"""
        self.login(monkey.app.config['USERNAME'],
                   monkey.app.config['PASSWORD'])
        rv = self.app.post('/add', data=dict(
            name='Paavo',
	    age=28,
	    mail='paavo.kivisto@gmail.com',
            text='<strong>Kova</strong> koodari!'
        ), follow_redirects=True)
        assert b'No monkies here so far' not in rv.data
        assert b'Paavo' in rv.data
        assert b'paavo.kivisto@gmail.com' in rv.data
        assert b'<strong>Kova</strong> koodari!' in rv.data
 	rv = self.app.post('/edit', data=dict(
            name='Paavo',
	    age=28,
	    mail='paavo.kivisto@aalto.fi',
            text='<strong>Tosi kova</strong> koodari!',
	    oldmail='paavo.kivisto@gmail.com'
        ), follow_redirects=True)
        assert b'No monkies here so far' not in rv.data
        assert b'Paavo' in rv.data
        assert b'paavo.kivisto@gmail.com' not in rv.data
        assert b'paavo.kivisto@aalto.fi' in rv.data
        assert b'<strong>Tosi kova</strong> koodari!' in rv.data
	
    def test_friends(self):
        """Test that friending works"""
        self.login(monkey.app.config['USERNAME'],
                   monkey.app.config['PASSWORD'])
        self.app.post('/add', data=dict(
            name='Paavo',
	    age=28,
	    mail='paavo.kivisto@gmail.com',
            text='<strong>Kova</strong> koodari!'
        ))
 	self.app.post('/add', data=dict(
            name='Kamu',
	    age=27,
	    mail='kamu.kiva@monkey.fi',
            text='Apina!'
        ))
	# Add friendship
	rv = self.app.get('/friends/kamu.kiva%40monkey.fi&paavo.kivisto%40gmail.com', follow_redirects=True)
	assert b'has no friends.' not in rv.data
        assert b'<strong>Friends: </strong>1' in rv.data
	rv = self.app.get('/')
        assert b'<strong>Friends: </strong>0' not in rv.data
        assert b'<strong>Friends: </strong>1' in rv.data
	# Remove friendship
	rv = self.app.get('/delfriends/kamu.kiva%40monkey.fi&paavo.kivisto%40gmail.com', follow_redirects=True)
	assert b'has no friends.' in rv.data
        assert b'<strong>Friends: </strong>0' in rv.data
	rv = self.app.get('/')
        assert b'<strong>Friends: </strong>0' in rv.data
        assert b'<strong>Friends: </strong>1' not in rv.data


if __name__ == '__main__':
    unittest.main()
