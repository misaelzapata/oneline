# Ws Server       

This project handles the logic between the clients and the operators. It's made with [Tornado](http://www.tornadoweb.org/en/stable/) to handle the web sockets and [Pika](https://pika.readthedocs.io/en/0.10.0/) to handle incoming and outgoing messages throug RabbitMQ queues. Additionally it has an API to send messages.
      
## Endpoints
       
url           | description
--------------|------------
/chat         | Web Socket URL: This handles all the chats for operators.
/send_messages| POST Endpoint: Used to send bulk messages.
/             | Debug web page.

## Chat WS

- Default URL: localhost:8080/chat        
- Listen to contact request:      
```       
{     
    'type':'listen_contact'       
    'contact':'5493516113952@s.whatsapp.net',         
}     
```       
- Send message to contact request:        
```       
{     
    'type':'response_to_contact'      
    'contact':'5493516113952@s.whatsapp.net',         
    'message':'Hi, whats up?'         
}     
```

## Bulk Messages Endpoint Example

JSON

```
{"messages":[{"contact_id":"5730f789a986014e13ca8c1c","message_id":"5730f7c0a986014e13ca8c1e"}, {"contact_id":"5730f789a986014e13ca8c1c","message":"Hola, soy un mensaje."}]}
```

## Debug web page
