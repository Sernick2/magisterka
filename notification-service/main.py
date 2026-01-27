import pika, os, time

# Czekamy chwilę, aż RabbitMQ wstanie
time.sleep(10)

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
params = pika.URLParameters(RABBIT_URL)
connection = pika.BlockingConnection(params)
channel = connection.channel()

# Tworzymy kolejkę
channel.queue_declare(queue='order_notifications')

def callback(ch, method, properties, body):
    print(f" [x] POWIADOMIENIE: Nowe zamówienie odebrane! Treść: {body.decode()}")
    print(" [x] Wysyłanie e-maila do klienta... (symulacja)")

channel.basic_consume(queue='order_notifications', on_message_callback=callback, auto_ack=True)

print(' [*] Notification Service oczekuje na wiadomości...')
channel.start_consuming()