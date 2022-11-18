from flask import render_template, Blueprint, request, session, redirect, url_for
import ibm_db
from datetime import datetime
import time

chat = Blueprint("chat_bp", __name__)

@chat.route('/chat/<ticket_id>/<receiver_name>/', methods = ['GET', 'POST'])
def address(ticket_id, receiver_name):
    '''
        Address Column - Agent and Customer chats with one another

        : param ticket_id ID of the ticket for which the chat is being opened
        : param receiver_name Name of the one who receives the texts, may be Agent / Customer
    '''
    # common page for both the customer and the agent
    # so cannot use login_required annotation
    # so to know who signed in, we have to use the session
    user = ""
    sender_id = ""
    value = ""
    can_trust = False
    post_url = f'/chat/{ticket_id}/{receiver_name}/'

    if session['LOGGED_IN_AS'] is not None:
        if session['LOGGED_IN_AS'] == "CUSTOMER":
            # checking if the customer is really logged in
            # by checking, if the customer has uuid attribute
            from .views import customer

            if(hasattr(customer, 'uuid')):
                user = "CUSTOMER"
                sender_id = customer.uuid
                can_trust = True

            else:
                # logging out the so called customer
                return redirect(url_for('blue_print.logout'))

        elif session['LOGGED_IN_AS'] == "AGENT":
            # checking if the agent is really logged in
            # by checking, if the agent has uuid aatribute
            from .views import agent

            if (hasattr(agent, 'uuid')):
                user = "AGENT"
                sender_id = agent.uuid
                can_trust = True

        else:
            # Admin is the one who logged in
            # admin should not see the chats, sp directly logging the admin out
            return redirect(url_for('blue_print.logout'))

        to_show = False
        message = ""

        if can_trust:
            # importing the connection string 
            from .views import conn

            if request.method == 'POST':
                # chats are enabled, only if the ticket is OPEN
                # getting the data collected from the customer / agent
                myMessage = request.form.get('message-box')

                if len(myMessage) == 0:
                    to_show = True
                    message = "Type something!"

                else:
                    # inserting the message in the database

                    # query to insert the message in the database
                    message_insert_query = '''
                        INSERT INTO chat 
                            (chat_id, sender_id, message, sent_at)
                        VALUES
                            (?, ?, ?, ?)
                    '''
                        
                    try:
                        stmt = ibm_db.prepare(conn, message_insert_query)
                        ibm_db.bind_param(stmt, 1, ticket_id)
                        ibm_db.bind_param(stmt, 2, sender_id)
                        ibm_db.bind_param(stmt, 3, myMessage)
                        ibm_db.bind_param(stmt, 4, datetime.now())

                        ibm_db.execute(stmt)

                    except:
                        to_show = True
                        message = "Please send again!"

                return redirect(post_url)
                    
            else:
                # method is GET
                # retrieving all the messages, if exist from the database
                msgs_to_show = False

                # query to get all the messages for this ticket
                get_messages_query = '''
                    SELECT * FROM chat 
                        WHERE chat_id = ?
                    ORDER BY sent_at ASC
                '''

                # query to check if the ticket is still OPEN 
                query_status_check = '''
                    SELECT query_status FROM tickets WHERE ticket_id = ?
                '''

                try:
                    # first checking if the ticket is OPEN
                    check = ibm_db.prepare(conn, query_status_check)
                    ibm_db.bind_param(check, 1, ticket_id)
                    ibm_db.execute(check)

                    value = "True" if ibm_db.fetch_assoc(check)['QUERY_STATUS'] == "OPEN" else "False"

                    # getting all the messages concerned with this ticket
                    stmt = ibm_db.prepare(conn, get_messages_query)
                    ibm_db.bind_param(stmt, 1, ticket_id)
                    ibm_db.execute(stmt)

                    messages = ibm_db.fetch_assoc(stmt)
                    messages_list = []

                    while messages != False:
                        messages_list.append(messages)
                        print(messages)
                        
                        messages = ibm_db.fetch_assoc(stmt)

                    # then some messages exist in this chat
                    if len(messages_list) > 0:
                        msgs_to_show = True

                    elif len(messages_list) == 0 and value == "True":
                        # ticket is OPEN
                        # but no messages are sent b/w the customer and the agent
                        msgs_to_show = False
                        to_show = True
                        message = f'Start the conversation with the {"Customer" if user ==  "AGENT" else "Agent"}'

                except:
                    to_show = True
                    message = "Something happened! Try Again"

                return render_template(
                    'address.html',
                    to_show = to_show,
                    message = message,
                    id = ticket_id,
                    chats = messages_list,
                    msgs_to_show = msgs_to_show,
                    sender_id = sender_id,
                    name = receiver_name,
                    user = user,
                    post_url = post_url,
                    value = value
                )

    else:
        # logging out whoever came inside the link
        return redirect(url_for('blue_print.logout'), user = user)