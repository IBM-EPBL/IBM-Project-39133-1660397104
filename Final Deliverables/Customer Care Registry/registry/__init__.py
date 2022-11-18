from flask import Flask, session
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "PHqtYfAN2v@CCR2022"

    # registering the blue prints with the app
    from .routes.views import views
    app.register_blueprint(views, appendix='/')

    from .routes.cust import cust
    app.register_blueprint(cust, appendix='/customer/')

    from .routes.admin import admin
    app.register_blueprint(admin, appendix='/admin/')

    from .routes.agent import agent
    app.register_blueprint(agent, appendix='/agent/')

    from .routes.chat import chat
    app.register_blueprint(chat, appendix='/chat/')

    # setting up the login manager
    login_manager = LoginManager()
    login_manager.login_view = "blue_print.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        if session.get('LOGGED_IN_AS') is not None:
            if session['LOGGED_IN_AS'] == "CUSTOMER":
                from .routes.views import customer
                
                if hasattr(customer, 'first_name'):
                    return customer

            elif session['LOGGED_IN_AS'] == "AGENT":
                from .routes.views import agent

                if hasattr(agent, 'first_name'):
                    return agent

            elif session['LOGGED_IN_AS'] == "ADMIN":
                from .routes.views import admin

                if hasattr(admin, 'email'):
                    return admin

        else:
            return None

    return app