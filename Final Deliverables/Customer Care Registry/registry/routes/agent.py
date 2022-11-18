from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, logout_user
import ibm_db
from .views import conn
from .views import pass_regex, mail
import re
from datetime import datetime
import uuid
import hashlib

USER_AGENT = "AGENT"

agent = Blueprint("agent", __name__)

@agent.route('/agent/profile')
@login_required
def profile():
    '''
        Displaying the agent's details in the dashboard
    '''
    from .views import agent
    
    # extra-level security
    if hasattr(agent, 'first_name'):
        return render_template('agent profile.html', agent = agent, id = 0, user = USER_AGENT)

    else:
        # logging out
        return redirect(url_for('blue_print.logout'))

@agent.route('/agent/assigned')
@login_required
def assigned():
    '''
        Showing the tickets asssigned to the agent by the admin
    '''
    from .views import agent

    if hasattr(agent, 'first_name'):
        # query to fetch the tickets assigned to the agent
        fetch_tickets_query = '''
            SELECT  
                tickets.ticket_id,
                tickets.raised_on,
                customer.first_name, 
                tickets.query_status,
                tickets.issue
            FROM 
                tickets
            JOIN
                customer ON customer.cust_id = tickets.raised_by AND tickets.assigned_to = ?
            ORDER BY
                tickets.raised_on ASC
        '''

        try:
            stmt = ibm_db.prepare(conn, fetch_tickets_query)
            ibm_db.bind_param(stmt, 1, agent.uuid)
            ibm_db.execute(stmt)

            tickets = ibm_db.fetch_assoc(stmt)

            if tickets:
                # some tickets are assigned to the agent
                tickets_list = []

                while tickets != False:
                    temp = []

                    temp.append(tickets['TICKET_ID'])
                    temp.append(str(tickets['RAISED_ON'])[0:10])
                    temp.append(tickets['FIRST_NAME'])
                    temp.append(tickets['QUERY_STATUS'])
                    temp.append(tickets['ISSUE'])

                    tickets_list.append(temp)

                    tickets = ibm_db.fetch_assoc(stmt)           

                return render_template(
                    'agent tickets.html',
                    id = 1,
                    tickets_to_show = True,
                    tickets = tickets_list,
                    msg = "Admin assigned these tickets to you",
                    user = USER_AGENT
                )

            else:
                # admin is yet to assign a ticket for the agent
                return render_template(
                    'agent tickets.html',
                    id = 1,
                    tickets_to_show = False,
                    msg = "Admin is yet to assign a ticket for you",
                    user = USER_AGENT
                )

        except:
            # something wrong went wrong while fetching the tickets
            return render_template(
                'agent tickets.html',
                id = 1,
                tp_show = True,
                message = "Something went wrong! Please Try Again",
                user = USER_AGENT
            )
        
    else:
        # logging out
        return redirect(url_for('blue_print.logout'))

@agent.route('/agent/change', methods = ['GET', 'POST'])
@login_required
def change():
    '''
        Changing the password for the agent
    '''
    from .views import agent
    
    if hasattr(agent, 'first_name'):
        if request.method == 'POST':
            # getting the passwords entered by the agent
            password = request.form.get('password')
            new1 = request.form.get('new-pass-1')
            new2 = request.form.get('new-pass-2')

            msg = ""
            to_show = False

            # validating the passwords entered by the agent
            if((len(password) and len(new1) and len(new2)) < 8):
                password = new1 = new2 = ""
                msg = "Passwords must be atleast 8 characters long!!" 
                to_show = True     

            elif new1 != new2:
                password = new1 = new2 = ""
                msg = "Passwords do not match" 
                to_show = True

            elif password == new1:
                password = new1 = new2 = ""
                msg = "Old and New passwords cannot be same" 
                to_show = True

            elif (not (re.fullmatch(pass_regex, new1))):
                password = new1 = new2 = ""
                msg = "Enter a valid password"
                to_show = True

            # by here the passwords are evaluated
            if not to_show:
                # updating the password of the agent
                # only if, the existing password of the user is valid
                # checking that if is true the database

                # query tp get the existing encrypted password of the agent
                get_password_sha = '''
                    SELECT passcode FROM agent WHERE agent_id = ?
                '''

                try:
                    stmt = ibm_db.prepare(conn, get_password_sha)
                    ibm_db.bind_param(stmt, 1, agent.uuid)
                    ibm_db.execute(stmt)

                    existing = ibm_db.fetch_assoc(stmt)['PASSCODE']

                    # checking 
                        # if the existing encrypted password is equal to
                        # the encrypted one of the one
                    # that is enetered by the agent
                    
                    # passwords match
                    if (existing == str(hashlib.sha256(password.encode()).hexdigest())):
                        # updating the password of the agent

                        # query to update the password
                        update_password_query = '''
                            UPDATE agent SET passcode = ? WHERE agent_id = ?
                        '''

                        # enrcypting the new password entered by the user
                        enc = str(hashlib.sha256(new1.encode()).hexdigest())

                        change = ibm_db.prepare(conn, update_password_query)
                        ibm_db.bind_param(change, 1, enc)
                        ibm_db.bind_param(change, 2, agent.uuid)

                        ibm_db.execute(change)

                        # password is changed
                        # now logging out the agent and re-directing to login page
                        logout_user()
                        
                        return render_template(
                            'login.html',
                            email = agent.email,
                            password = "",
                            to_show = True, 
                            message = "Password changed! Please login"
                        )
                        
                    else:
                        # passwords do not match
                        to_show = True
                        password = new1 = new2
                        msg = "Invalid current password!"

                except:
                    # something happened while changing the password
                    # alerting the agent
                    to_show = True
                    password = new1 = new2
                    msg = "Password not changed! Please try again"

            return render_template(
                'agent change.html',
                id = 2,
                password = password,
                new1 = new1,
                new2 = new2,
                to_show = to_show,
                message = msg,
                user = USER_AGENT
            )

        return render_template('agent change.html', id = 2, user = USER_AGENT)

    else:
        # logging out
        return redirect(url_for('blue_print.logout'))

@agent.route('/agent/about')
@login_required
def about():
    '''
        Showing the about of the application to the agent
    '''
    from .views import agent

    if hasattr(agent, 'first_name'):
        return render_template('agent about.html', id = 3, user = USER_AGENT)

    else:
        # logging out
        return redirect(url_for('blue_print.logout'))

@agent.route('/agent/support', methods = ['GET', 'POST'])
@login_required
def support():
    '''
        Agent can post his/her feedback here
    '''
    from .views import agent

    if hasattr(agent, 'first_name'):
        if request.method == 'POST':
            # collecting the feeback entered by the customer
            feed = str(request.form.get('feed-box')).strip()

            # checking if the feedback entered by the customer is empty! 
            # if so, alerting the customer
            if len(feed) == 0:
                message = "Feedback cannot be empty!"

            else:
                # feedback entered is valid
                # updating the feedback in the database
                insert_feedback_query = '''
                    INSERT INTO feedback 
                        (feed_id, raised_on, raised_by, raised_name, feed)
                    VALUES 
                        (?, ?, ?, ?, ?)
                '''

                try:
                    # creating unique id for the feedback
                    feed_id = str(uuid.uuid4())

                    stmt = ibm_db.prepare(conn, insert_feedback_query)
                    ibm_db.bind_param(stmt, 1, feed_id)
                    ibm_db.bind_param(stmt, 2, datetime.now())
                    ibm_db.bind_param(stmt, 3, "Agent")
                    ibm_db.bind_param(stmt, 4, agent.first_name)
                    ibm_db.bind_param(stmt, 5, feed)

                    ibm_db.execute(stmt)

                    # feedback is inserted
                    # Thanking the customer for the feedback
                    message = "Thank you for your feedback! Keep using CCR"

                except:
                    # something happened while sumbitting the feedback
                    message = "Feedback not submitted! Please Try Again"

            return render_template(
                'agent support.html',
                id = 5,
                to_show = True,
                message = message
            )

        return render_template('agent support.html', id = 4, user = USER_AGENT)

    else:
        # logging out
        return redirect(url_for('blue_print.logout'))

@agent.route('/agent/no-show', methods = ['GET', 'POST'])
@login_required
def no_show():
    '''
        Agent who is yet to be confirmed by the admin is shown this page
    '''
    from .views import agent
    
    # extra-level security
    if hasattr(agent, 'first_name'):
        return render_template('agent no show.html', agent = agent, user = USER_AGENT)

    else:
        # logging out
        return redirect(url_for('blue_print.logout'))
