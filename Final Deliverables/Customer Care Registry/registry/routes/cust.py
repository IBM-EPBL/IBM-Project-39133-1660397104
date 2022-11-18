from flask import Blueprint, render_template, request, redirect, session, url_for
from flask_login import login_required, logout_user
import ibm_db
from .views import conn, pass_regex, mail
import uuid
from datetime import date, datetime
import re
import hashlib


QUERY_STATUS_OPEN = "OPEN"
QUERY_STATUS_ASSIGNED_AGENT = "AGENT ASSIGNED"
QUERY_STATUS_CLOSE = "CLOSE"

cust = Blueprint("customer", __name__)

@cust.route('/customer/')
@login_required
def profile():
    '''
        Custome can see his/her profile card
    '''
    from .views import customer
        
    if hasattr(customer, 'uuid'):
        return render_template('cust profile.html', customer = customer, id = 0)

    else:
        return redirect(url_for('blue_print.logout'))

@cust.route('/customer/new', methods = ['GET', 'POST'])
@login_required
def new():
    '''
        Customer can create a new ticket 
    '''
    from .views import customer

    if(hasattr(customer, 'uuid')):
        if request.method == 'POST':
            # collecting the query entered by the customer in the textarea
            query = request.form.get('query-box')

            msg = ""
            to_show = False

            if(len(query) == 0):
                msg = "Query cannot be empty!"
                to_show = True

            else:
                # updating the query in the database
                update_query = '''
                    INSERT INTO tickets 
                        (ticket_id, raised_by, raised_on, issue, query_status)
                    VALUES 
                        (?, ?, ?, ?, ?)
                '''

                try:
                    stmt = ibm_db.prepare(conn, update_query)

                    # creating a uuid for the ticket_id
                    ticket_id = str(uuid.uuid4())
                    raised_by = customer.uuid
                    raied_on = datetime.now()

                    ibm_db.bind_param(stmt, 1, ticket_id)
                    ibm_db.bind_param(stmt, 2, raised_by)
                    ibm_db.bind_param(stmt, 3, raied_on)
                    ibm_db.bind_param(stmt, 4, query)
                    ibm_db.bind_param(stmt, 5, QUERY_STATUS_OPEN)

                    ibm_db.execute(stmt)

                    msg = "Ticket created!"
                    to_show = True

                    send_email = session['EMAIL']

                    # sending the acknowledgement mail to the customer
                    mail.sendEmail(
                        f'Customer Care Registry', 
                        f'''Welcome {session['FIRST_NAME']}! <br/>
                            You have created a new ticket! <br/>
                            Ticket ID : <strong>{ticket_id}</strong> <br/>
                            Query : <strong>{query}</strong> <br/> <br/>
                            <br/>
                            An agent will be assigned to you very soon!! <br/>
                            Stay Tuned...''',
                        [f'{send_email}']
                    )

                except:
                    msg = "Something went wrong!"
                    to_show = True

            return render_template('cust new ticket.html', id = 1, to_show = to_show, message = msg)

        return render_template('cust new ticket.html', id = 1)

    else:
        # logging out
        return redirect(url_for('blue_print.logout'))

@cust.route('/customer/tickets')
@login_required
def tickets():
    '''
        Fetching all the tickets raised by the customer
    '''
    from .views import customer

    if(hasattr(customer, 'uuid')):
        fetch_query = '''
            SELECT  
                tickets.ticket_id,
                tickets.raised_on,
                tickets.query_status,
                agent.first_name, 
                tickets.issue,
                tickets.raised_by
            FROM
                tickets
            LEFT JOIN 
                agent ON agent.agent_id = tickets.assigned_to 
            ORDER BY tickets.raised_on DESC
        '''

        from .views import customer
        raised_by = customer.uuid

        try:
            stmt = ibm_db.prepare(conn, fetch_query)
            ibm_db.execute(stmt)

            tickets = ibm_db.fetch_assoc(stmt)
            tickets_list = []

            if tickets:
                # means, the customer has raised some tickets before
                while tickets != False:
                    if raised_by == tickets['RAISED_BY']:
                        temp = []

                        temp.append(tickets['TICKET_ID'])
                        temp.append(str(tickets['RAISED_ON'])[0:10])
                        temp.append(tickets['QUERY_STATUS'])
                        temp.append(tickets['ISSUE'])
                        temp.append(tickets['FIRST_NAME'])

                        tickets_list.append(temp)                       

                    tickets = ibm_db.fetch_assoc(stmt)

                return render_template(
                    'cust tickets.html',
                    id = 2,
                    tickets_to_show = True,
                    tickets = tickets_list,
                    msg = "These are your tickets"
                )

            else:
                # means, the customer is yet to raise a ticket
                return render_template(
                    'cust tickets.html',
                    id = 2,
                    tickets_to_show = False,
                    msg = "You are yet to rise a ticket"
                )

        except:
            # something fishy happened while loading the customer's tickets
            return render_template(
                'cust tickets.html',
                id = 2,
                to_show = True,
                message = "Something went wrong! Please Try Again"
            )

    else:
        # logging out
        return redirect(url_for('blue_print.logout'))
    
@cust.route('/customer/change', methods = ['GET', 'POST'])
@login_required
def change():
    '''
        Changing the password of the customer
    '''
    from .views import customer
    
    if hasattr(customer, 'first_name'):
        if request.method == 'POST':
            # getting the passwords entered by the customer
            password = request.form.get('password')
            new1 = request.form.get('new-pass-1')
            new2 = request.form.get('new-pass-2')

            msg = ""
            to_show = False

            # validating the passwords entered by the ucer
            if((len(password) or len(new1) or len(new2)) < 8):
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
                # updating the password of the customer
                # only if, the existing password of the user is valid
                # checking that if is true the database

                # query tp get the existing encrypted password of the customer
                get_password_sha = '''
                    SELECT passcode FROM customer WHERE cust_id = ?
                '''

                try:
                    stmt = ibm_db.prepare(conn, get_password_sha)
                    ibm_db.bind_param(stmt, 1, customer.uuid)
                    ibm_db.execute(stmt)

                    existing = ibm_db.fetch_assoc(stmt)['PASSCODE']

                    # checking 
                        # if the existing encrypted password is equal to
                        # the encrypted one of the one
                    # that is enetered by the customer
                    
                    # passwords match
                    if (existing == str(hashlib.sha256(password.encode()).hexdigest())):
                        # updating the password of the customer

                        # query to update the password
                        update_password_query = '''
                            UPDATE customer SET passcode = ? WHERE cust_id = ?
                        '''

                        # enrcypting the new password entered by the user
                        enc = str(hashlib.sha256(new1.encode()).hexdigest())

                        change = ibm_db.prepare(conn, update_password_query)
                        ibm_db.bind_param(change, 1, enc)
                        ibm_db.bind_param(change, 2, customer.uuid)

                        ibm_db.execute(change)

                        send_mail = session['EMAIL']

                        # sending the acknowledgement mail to the customer
                        mail.sendEmail(
                            f'Customer Care Registry', 
                            f'''Welcome {session['FIRST_NAME']}! <br/>
                                It seems you have changed your password! <br/>
                                If it is not you, kindly report to us <br/>
                                Thank you!!
                            ''',
                            [f'{send_mail}']
                        )

                        # password is changed
                        # now logging out the customer and re-directing to login page
                        logout_user()
                        session.clear()
                        
                        return render_template(
                            'login.html',
                            email = customer.email,
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
                    # alerting the customer
                    to_show = True
                    password = new1 = new2
                    msg = "Password not changed! Please try again"

            return render_template(
                'cust change.html',
                id = 3,
                password = password,
                new1 = new1,
                new2 = new2,
                to_show = to_show,
                message = msg
            )

        return render_template('cust change.html', id = 3)

    else:
        return redirect(url_for('blue_print.logout'))

@cust.route('/customer/about')
@login_required
def about():
    return render_template('cust about.html', id = 4)

@cust.route('/customer/support', methods = ['GET', 'POST'])
@login_required
def support():
    '''
        Collecting the feedback of the customer
    '''
    from .views import customer

    message = ""

    if(hasattr(customer, 'first_name')):
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
                    ibm_db.bind_param(stmt, 3, "Customer")
                    ibm_db.bind_param(stmt, 4, customer.first_name)
                    ibm_db.bind_param(stmt, 5, feed)

                    ibm_db.execute(stmt)

                    # feedback is inserted
                    # Thanking the customer for the feedback
                    message = "Thank you for your feedback! Keep using CCR"

                except:
                    # something happened while sumbitting the feedback
                    message = "Feedback not submitted! Please Try Again"

            return render_template(
                'cust support.html',
                id = 5,
                to_show = True,
                message = message
            )

        return render_template('cust support.html', id = 5)

    else:
        return redirect(url_for('blue_print.logout'))

@cust.route('/customer/close/<ticket_id>/')
@login_required
def close(ticket_id):
    '''
        Customer can close the ticket 
        :param ticket_id ID of the ticket that should be closed
    '''
    from .views import customer

    if(hasattr(customer, 'uuid')):
        # query to close the ticket
        close_ticket = '''
            UPDATE tickets SET query_status = ? WHERE ticket_id = ?
        '''

        stmt = ibm_db.prepare(conn, close_ticket)
        ibm_db.bind_param(stmt, 1, "CLOSED")
        ibm_db.bind_param(stmt, 2, ticket_id)
        ibm_db.execute(stmt)

        # sending the acknowledgement mail to the customer
        send_mail = session['EMAIL']
        mail.sendEmail(
            f'Customer Care Registry', 
            f'''You have closed a ticket <br/>
                <strong>Closed Ticket ID : {ticket_id}</strong> <br/>
                <br/>
                Thank you!
            ''',
            [f'{send_mail}']
        )

        return redirect(url_for('customer.tickets'))

    else:
        # logging out
        return redirect(url_for('blue_print.logout'))


