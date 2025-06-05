import pika
import json
import threading
import logging
from typing import Dict, Callable, Any
from datetime import datetime
import os


class EventBus:
    def __init__(self, rabbitmq_url: str = None):
        self.rabbitmq_url = rabbitmq_url or os.getenv(
            'RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
        self.connection = None
        self.channel = None
        self.event_handlers: Dict[str, list] = {}
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url))
            self.channel = self.connection.channel()

            # Declare exchange for saga events
            self.channel.exchange_declare(
                exchange='saga_events',
                exchange_type='topic',
                durable=True
            )

            self.logger.info("Connected to RabbitMQ")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False

    def publish_event(self, event_type: str, event_data: dict, routing_key: str = None):
        """Publish an event to the event bus"""
        if not self.channel:
            if not self.connect():
                raise Exception("Cannot connect to RabbitMQ")

        event = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': event_data
        }

        routing_key = routing_key or event_type

        try:
            self.channel.basic_publish(
                exchange='saga_events',
                routing_key=routing_key,
                body=json.dumps(event),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )

            self.logger.info(
                f"Published event: {event_type} with routing key: {routing_key}")

        except Exception as e:
            self.logger.error(
                f"Failed to publish event {event_type}: {str(e)}")
            raise

    def subscribe_to_event(self, event_pattern: str, handler: Callable[[dict], None], queue_name: str = None):
        """Subscribe to events matching a pattern"""
        if not self.channel:
            if not self.connect():
                raise Exception("Cannot connect to RabbitMQ")

        # Create queue for this service
        queue_name = queue_name or f"saga_queue_{event_pattern.replace('*', 'wildcard').replace('#', 'all')}"

        result = self.channel.queue_declare(queue=queue_name, durable=True)
        queue_name = result.method.queue

        # Bind queue to exchange with routing key pattern
        self.channel.queue_bind(
            exchange='saga_events',
            queue=queue_name,
            routing_key=event_pattern
        )

        # Store handler
        if event_pattern not in self.event_handlers:
            self.event_handlers[event_pattern] = []
        self.event_handlers[event_pattern].append(handler)

        # Set up consumer
        def callback(ch, method, properties, body):
            try:
                event = json.loads(body)
                self.logger.info(f"Received event: {event['event_type']}")

                # Call all handlers for this pattern
                for h in self.event_handlers.get(event_pattern, []):
                    h(event)

                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                self.logger.error(f"Error processing event: {str(e)}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback
        )

        self.logger.info(
            f"Subscribed to events matching pattern: {event_pattern}")

    def start_consuming(self):
        """Start consuming events"""
        if not self.channel:
            raise Exception("Not connected to RabbitMQ")

        self.logger.info("Starting to consume events...")
        self.channel.start_consuming()

    def stop_consuming(self):
        """Stop consuming events"""
        if self.channel:
            self.channel.stop_consuming()

    def close(self):
        """Close connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()


class SagaEvent:
    """Saga event types and data structures"""

    # Checkout Saga Events
    CHECKOUT_INITIATED = "checkout.initiated"
    INVENTORY_RESERVE_REQUESTED = "inventory.reserve.requested"
    INVENTORY_RESERVED = "inventory.reserved"
    INVENTORY_RESERVE_FAILED = "inventory.reserve.failed"

    PAYMENT_REQUESTED = "payment.requested"
    PAYMENT_PROCESSED = "payment.processed"
    PAYMENT_FAILED = "payment.failed"

    ORDER_CREATE_REQUESTED = "order.create.requested"
    ORDER_CREATED = "order.created"
    ORDER_CREATE_FAILED = "order.create.failed"

    INVENTORY_COMMIT_REQUESTED = "inventory.commit.requested"
    INVENTORY_COMMITTED = "inventory.committed"
    INVENTORY_COMMIT_FAILED = "inventory.commit.failed"

    # Compensation Events
    CHECKOUT_FAILED = "checkout.failed"
    INVENTORY_UNRESERVE_REQUESTED = "inventory.unreserve.requested"
    INVENTORY_UNRESERVED = "inventory.unreserved"
    PAYMENT_REFUND_REQUESTED = "payment.refund.requested"
    PAYMENT_REFUNDED = "payment.refunded"
    ORDER_CANCEL_REQUESTED = "order.cancel.requested"
    ORDER_CANCELLED = "order.cancelled"

    # Success Events
    CHECKOUT_COMPLETED = "checkout.completed"


class SagaState:
    """Track saga state for choreographed pattern"""

    def __init__(self):
        self.states = {}  # saga_id -> state_dict

    def create_saga(self, saga_id: str, initial_data: dict):
        """Create a new saga state"""
        self.states[saga_id] = {
            'saga_id': saga_id,
            'status': 'started',
            'steps_completed': [],
            'steps_failed': [],
            'compensation_needed': False,
            'created_at': datetime.utcnow().isoformat(),
            'data': initial_data
        }

    def update_saga(self, saga_id: str, step: str, status: str, data: dict = None):
        """Update saga state"""
        if saga_id not in self.states:
            return False

        saga = self.states[saga_id]

        if status == 'completed':
            if step not in saga['steps_completed']:
                saga['steps_completed'].append(step)
        elif status == 'failed':
            if step not in saga['steps_failed']:
                saga['steps_failed'].append(step)
            saga['compensation_needed'] = True
            saga['status'] = 'failed'

        if data:
            saga['data'].update(data)

        saga['updated_at'] = datetime.utcnow().isoformat()
        return True

    def get_saga(self, saga_id: str):
        """Get saga state"""
        return self.states.get(saga_id)

    def mark_completed(self, saga_id: str):
        """Mark saga as completed"""
        if saga_id in self.states:
            self.states[saga_id]['status'] = 'completed'
            self.states[saga_id]['updated_at'] = datetime.utcnow().isoformat()

    def mark_compensated(self, saga_id: str):
        """Mark saga as compensated"""
        if saga_id in self.states:
            self.states[saga_id]['status'] = 'compensated'
            self.states[saga_id]['updated_at'] = datetime.utcnow().isoformat()


# Global instances
event_bus = EventBus()
saga_state = SagaState()

# Event publishing helpers


def publish_checkout_initiated(saga_id: str, cart_id: str, user_id: str, payment_method: str, billing_address: dict):
    event_bus.publish_event(
        SagaEvent.CHECKOUT_INITIATED,
        {
            'saga_id': saga_id,
            'cart_id': cart_id,
            'user_id': user_id,
            'payment_method': payment_method,
            'billing_address': billing_address
        }
    )


def publish_inventory_reserve_requested(saga_id: str, cart_id: str, items: list):
    event_bus.publish_event(
        SagaEvent.INVENTORY_RESERVE_REQUESTED,
        {
            'saga_id': saga_id,
            'cart_id': cart_id,
            'items': items
        }
    )


def publish_inventory_reserved(saga_id: str, cart_id: str, reservation_id: str):
    event_bus.publish_event(
        SagaEvent.INVENTORY_RESERVED,
        {
            'saga_id': saga_id,
            'cart_id': cart_id,
            'reservation_id': reservation_id
        }
    )


def publish_inventory_reserve_failed(saga_id: str, cart_id: str, reason: str):
    event_bus.publish_event(
        SagaEvent.INVENTORY_RESERVE_FAILED,
        {
            'saga_id': saga_id,
            'cart_id': cart_id,
            'reason': reason
        }
    )


def publish_payment_requested(saga_id: str, cart_id: str, amount: float, payment_method: str, customer_email: str):
    event_bus.publish_event(
        SagaEvent.PAYMENT_REQUESTED,
        {
            'saga_id': saga_id,
            'cart_id': cart_id,
            'amount': amount,
            'payment_method': payment_method,
            'customer_email': customer_email
        }
    )


def publish_payment_processed(saga_id: str, payment_id: str, amount: float):
    event_bus.publish_event(
        SagaEvent.PAYMENT_PROCESSED,
        {
            'saga_id': saga_id,
            'payment_id': payment_id,
            'amount': amount
        }
    )


def publish_payment_failed(saga_id: str, reason: str):
    event_bus.publish_event(
        SagaEvent.PAYMENT_FAILED,
        {
            'saga_id': saga_id,
            'reason': reason
        }
    )


def publish_order_create_requested(saga_id: str, cart_id: str, user_id: str, total_amount: float, payment_id: str):
    event_bus.publish_event(
        SagaEvent.ORDER_CREATE_REQUESTED,
        {
            'saga_id': saga_id,
            'cart_id': cart_id,
            'user_id': user_id,
            'total_amount': total_amount,
            'payment_id': payment_id
        }
    )


def publish_order_created(saga_id: str, order_id: str):
    event_bus.publish_event(
        SagaEvent.ORDER_CREATED,
        {
            'saga_id': saga_id,
            'order_id': order_id
        }
    )


def publish_order_create_failed(saga_id: str, reason: str):
    event_bus.publish_event(
        SagaEvent.ORDER_CREATE_FAILED,
        {
            'saga_id': saga_id,
            'reason': reason
        }
    )


def publish_inventory_commit_requested(saga_id: str, cart_id: str):
    event_bus.publish_event(
        SagaEvent.INVENTORY_COMMIT_REQUESTED,
        {
            'saga_id': saga_id,
            'cart_id': cart_id
        }
    )


def publish_inventory_committed(saga_id: str, cart_id: str):
    event_bus.publish_event(
        SagaEvent.INVENTORY_COMMITTED,
        {
            'saga_id': saga_id,
            'cart_id': cart_id
        }
    )


def publish_checkout_completed(saga_id: str, order_id: str):
    event_bus.publish_event(
        SagaEvent.CHECKOUT_COMPLETED,
        {
            'saga_id': saga_id,
            'order_id': order_id
        }
    )


def publish_checkout_failed(saga_id: str, reason: str):
    event_bus.publish_event(
        SagaEvent.CHECKOUT_FAILED,
        {
            'saga_id': saga_id,
            'reason': reason
        }
    )

# Compensation event publishers


def publish_payment_refund_requested(saga_id: str, payment_id: str, reason: str):
    event_bus.publish_event(
        SagaEvent.PAYMENT_REFUND_REQUESTED,
        {
            'saga_id': saga_id,
            'payment_id': payment_id,
            'reason': reason
        }
    )


def publish_inventory_unreserve_requested(saga_id: str, cart_id: str):
    event_bus.publish_event(
        SagaEvent.INVENTORY_UNRESERVE_REQUESTED,
        {
            'saga_id': saga_id,
            'cart_id': cart_id
        }
    )


def publish_order_cancel_requested(saga_id: str, order_id: str):
    event_bus.publish_event(
        SagaEvent.ORDER_CANCEL_REQUESTED,
        {
            'saga_id': saga_id,
            'order_id': order_id
        }
    )
