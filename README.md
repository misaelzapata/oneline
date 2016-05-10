# OneLine

A project to provide client support via WhatsApp.

## Getting Started

This project consists in 3 sub services: Yowsup Stack, Ws Server and Web.

* Yowsup Stack: Provides the WhatsApp comunication layer.
* Ws Server: Provides the logic managing messages between clients and operators.
* Web: It's the front end for the operators and also the admins.

In order to run this project you will need to have installed RabbitMQ, MongoDB, Python 2.7 and Virtualenv.

### Installing

Get a copy of the code, make a virtualenv for each layer and install their dependencies:

```sh
$ git clone https://github.com/misaelzapata/oneline.git
$ # Yowsup Stack
$ cd oneline/yowsup_stack
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
$ deactivate
$ # WsServer
$ cd ../ws_server
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
$ deactivate
$ # Web
$ cd ../web
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
$ deactivate
$ cd ..
```

Now you will need to get the [yowsup](https://github.com/tgalal/yowsup/wiki/yowsup-cli-2.0) credentials and save them in 'yowsup_stack/credentials.json'.

```
[
    ["5493511234567", "password"]
]
```

Also update the config.py file in each layer.

### Running

To run each layer using their own previously created envs. Is recomended to run them using 'screen' or some way to visualize each layer while is running to see logs.

Yowsup Stack:
```sh
$ cd yowsup_stack
$ source env/bin/activate
$ python stack_v1.py
```

WsServer:
```sh
$ cd ws_server
$ source env/bin/activate
$ python run.py
```

Web:
```sh
$ cd web
$ source env/bin/activate
$ python app.py
```

If all is fine, now you can go to (http://localhost:5000/).

## Yowsup Stack

See docs here: [link]

## Ws Server

See docs here: [link]

## Web

See docs here: [link]

## RabbitMQ Queues

- Incoming messages from users: 'incoming_messages', format example:
```
{
    '_id':'5719a2b721c93725aa60cb5b'
    'contact':'5493516113952@s.whatsapp.net', 
    'message':'Hi!', 
    'status':'unread', 
    'created':'2016-04-26T10:51:52.634835',
    'modified':'2016-04-26T10:51:52.634835'
}
```

- Outgoing messages to users: 'outgoing_messages', format example:
```
{
    '_id':'5719a2b721c93725aa60c357'
    'contact':'5493516113952@s.whatsapp.net', 
    'message':'Hi, whats up?', 
    'sent':false 
}
```
