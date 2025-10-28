# Bluemailer

Email and APN handler for Blueride. Will feed off of AMQP/RabbitMQ.

## About

- Runs RabbitMq to queue emails
- Uses rust code to send email
- Email payloads are of type `json` and shoudl be posted from backend

## Considerations

- Uses `rustls` and native in a mix so will fix later...
- Will probably incorporate some tracing mechanism to make debugging easier

## Testing

```
cat cancel.json  | rabbitmqadmin publish exchange=amq.default routing_key="notification_queue"
cat matched.json | rabbitmqadmin publish exchange=amq.default routing_key="notification_queue"
```

Link: [Github Repo](https://github.com/hack-duke/bluemailer)
