#!/usr/bin/python
# -*- coding: utf -*-

# setup
import unittest
import budget

class UsersTestCases(unittest.TestCase):

    def setUp(self):
        # create app with a testing database
        budget.app = budget.create_app(db='sqlite:///:memory:')
        self.app = budget.app.test_client()

        # cleanup
        #self.app.get('/test/wipe-tables')

        # setup our test user
        self.app.get('/test/create-user/admin')

    def tearDown(self):
        # cleanup
        from db.database import Base, engine
        Base.metadata.drop_all(bind=engine)

    def test_login(self):
        # login
        rv = self.app.post('/login', data=dict(username="hack3r", password="hack3r"), follow_redirects=True)
        assert 'You were logged in' not in rv.data

        # login
        rv = self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)
        assert 'You were logged in' in rv.data

    def test_logout(self):
        # logout
        rv = self.app.get('/logout', follow_redirects=True)
        assert '<title>Budget Login</title>' in rv.data

    def test_add_private_user(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # add private user
        rv = self.app.post('/user/add-private', data=dict(name="Barunka"), follow_redirects=True)
        assert 'Private user added' in rv.data

    def test_private_user_login(self):
        # login
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        self.app.post('/user/add-private', data=dict(name="Barunka"), follow_redirects=True)

        self.app.get('/logout', follow_redirects=True)

        rv = self.app.post('/login', data=dict(username="barunka", password="barunka"), follow_redirects=True)
        assert 'You were logged in' not in rv.data

    def test_link_users(self):
        # add normal user
        self.app.get('/test/create-user/jack')

        # login as jack
        self.app.post('/login', data=dict(username="jack", password="jack"), follow_redirects=True)

        # get our key
        rv = self.app.get('/test/get-key')
        user_key = rv.data

        # connect to a user through a user fail
        rv = self.app.post('/user/connect', data=dict(key=user_key), follow_redirects=True)
        assert 'I can haz myself impossible' in rv.data

        # logout
        self.app.get('/logout', follow_redirects=True)

        # login as admin
        self.app.post('/login', data=dict(username="admin", password="admin"), follow_redirects=True)

        # connect to a user through a user success
        rv = self.app.post('/user/connect', data=dict(key=user_key), follow_redirects=True)
        assert 'Connection made' in rv.data

        # add private user
        self.app.post('/user/add-private', data=dict(name="Barunka"), follow_redirects=True)

        # check the loans listing
        rv = self.app.get('/loans', follow_redirects=True)
        assert '<a href="/loans/with/jack">Jack</a>' in rv.data
        assert '<li class="last"><a href="/loans/with/barunka">Barunka</a>' in rv.data