## OneLine
## RabbitMQ Queues Names

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

## Ws Server

### Endpoints:
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
