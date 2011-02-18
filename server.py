from cherrypy import wsgiserver
import budget

app = budget.create_app(db='sqlite:////var/www/html/python/flask/budget/db/database.sqlite3')
wsgi_apps = [('/', app)]
server = wsgiserver.CherryPyWSGIServer(('0.0.0.0', 8070), wsgi_apps, request_queue_size=500, server_name='localhost')

if __name__ == '__main__':
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()