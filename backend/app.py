# app.py
# Author : Andre Baldo (http://github.com/andrebaldo/)
# The main file for this login service, this will deal with the login process
# and the login authentication, and logout.
from services.jsonClassEncoder import JsonClassEncoder
from services.customSessionInterface import CustomSessionInterface
from services.auth import Auth
from models.loginTokenResult import LoginTokenResult
import flask
import flask_login
from flask import request
from flask_sqlalchemy import SQLAlchemy


app = flask.Flask(__name__)

# app.app_context().push()


# Configurations
ALOWED_CORS_DOMAIN = 'http://localhost:8081'
app.secret_key = 'this will be used to cryptograph sensible data like authentication tokens'
jsonClassEncoder = JsonClassEncoder()

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
app.session_interface = CustomSessionInterface()
# End of Configurations section

authModule = Auth()


@login_manager.user_loader
def load_user(user_id):
    return authModule.load_user(user_id)


# Only requests that have an Authorization request reader set with a valid login token
# can access the protected routes, like this '/home' one for example
@app.route('/coursecontent', methods=(['GET']))
@flask_login.login_required
def home():
    print("You are logged in")

    return 'Home protected by @flask_login.login_required'


# Sets the route for this endpoint, this will configure our web server to receive requests at this path.
@app.route('/register', methods=(['POST']))
def register():
    requestPayload = request.get_json()
    username = requestPayload['email']
    password = requestPayload['password']
    mobilePhone = requestPayload['mobilePhone']

    registerResult = authModule.register(username, password, mobilePhone)
    if registerResult.success == True:
        return jsonClassEncoder.encode(registerResult), 200
    else:
        return jsonClassEncoder.encode(registerResult), 500


# this route will login the user and return a Json Web Token, this token
# will be stored into the client aplication and need to be passed over for each new
# request, via Authorizaton header.
@app.route('/token', methods=(['POST']))
def token():
    authToken = request.headers.get('Authorization')
    activeSession = authModule.GetActiveSession(authToken)
    if activeSession is not None:
        loginResult = LoginTokenResult(
            True, 'Login successful', activeSession.jwToken)
        return jsonClassEncoder.encode(loginResult), 200
    else:
        requestPayload = request.get_json()
        username = requestPayload['email']
        password = requestPayload['password']
        loginResult = authModule.getLoginToken(
            username, password, app.config['SECRET_KEY'])
        if loginResult.success == True:
            return jsonClassEncoder.encode(loginResult), 200
        else:
            return jsonClassEncoder.encode(loginResult), 401


# This will invalidate the user current user session on the server
@app.route('/logout', methods=(['POST']))
def sessionLogout():
    authToken = request.headers.get('Authorization')
    logoutResult = authModule.SessionLogout(authToken, request.url)
    if logoutResult.success == True:
        return jsonClassEncoder.encode(logoutResult), 200
    else:
        return jsonClassEncoder.encode(logoutResult), 401


# This enable CORS, it means that this server will authorize AJAX calls from
# other domains than the current domain where the API is running
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = ALOWED_CORS_DOMAIN
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT'
        headers = request.headers.get('Access-Control-Request-Headers')
        if headers:
            response.headers['Access-Control-Allow-Headers'] = headers

    return response


app.after_request(add_cors_headers)


# Checks if the user is auhenticated for protected routes decorated with @flask_login.login_required
@login_manager.request_loader
def load_user_from_request(request):
    # Get the token from the Authorization request header
    authToken = request.headers.get('Authorization')
    if authToken:
        try:
            # Checks if is there a active session for this token and return his user
            user = authModule.GetUserByToken(authToken)
            return user
        except TypeError:
            pass

            # If it can't find an active session returns None,
    # this will cause the request decorated with @flask_login.login_required been denied
    return None


if __name__ == '__main__':
    app.run()
