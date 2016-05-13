# Web Server

This project handles the logic between the Users and the WS server. It's made with Flask, Flask-admin for the admin,
Flask-login to handle the login, and jquery for the UI

## Views

url                       | description
--------------------------|------------
/login                    | Login page for operators
/chat                     | Main view to handle clients
/chats                    | History of conversations
/send_message             | Page to send bulk messages to contacts loaded on the admin, can also send custom messages
/index                    | Welcome Page
/admin/                   | Admin page
/admin/login/             | Login page restricted to admins
/admin/user/              | CRUD of the users of the system (admins and operators)
/admin/contact/           | CRUD of the contacts, (which are used on the send_message screen)
/admin/message/           | CRUD of the messages, (which are used on the send_message screen)
/admin/outgoingmessages/  | History of the messages send by the operators to the clients
/admin/incomingmessages/  | History of the messages received by the operators from the clients

