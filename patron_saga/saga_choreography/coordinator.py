from flask import Flask, request, jsonify
import uuid
import threading
from event_bus import (
    event_bus, saga_state, SagaEvent,
    publish_checkout_initiated, publish_checkout_completed, publish_checkout_failed,
    publish_inventory_reserve_requested, publish_payment_refund_requested,
    publish_inventory_unreserve_requested, publish_order_cancel_requested
)

app = Flask(__name__)


class ChoreographedSagaCoordinator:
    def __init__(self):
        self.setup_event_handlers()

    def setup_event_handlers(self):
        """Setup event handlers for saga coordination"""

        # Subscribe to inventory events
        event_bus.subscribe_to_event(
            SagaEvent.INVENTORY_RESERVED,
            self.handle_inventory_reserved,
            "coordinator_inventory_reserved"
        )

        event_bus.subscribe_to_event(
            SagaEvent.INVENTORY_RESERVE_FAILED,
            self.handle_inventory_reserve_failed,
            "coordinator_inventory_failed"
        )

        # Subscribe to payment events
        event_bus.subscribe_to_event(
            SagaEvent.PAYMENT_PROCESSED,
            self.handle_payment_processed,
            "coordinator_payment_processed"
        )

        event_bus.subscribe_to_event(
            SagaEvent.PAYMENT_FAILED,
            self.handle_payment_failed,
            "coordinator_payment_failed"
        )

        # Subscribe to order events
        event_bus.subscribe_to_event(
            SagaEvent.ORDER_CREATED,
            self.handle_order_created,
            "coordinator_order_created"
        )

        event_bus.subscribe_to_event(
            SagaEvent.ORDER_CREATE_FAILED,
            self.handle_order_create_failed,
            "coordinator_order_failed"
        )

        # Subscribe to inventory commit events
        event_bus.subscribe_to_event(
            SagaEvent.INVENTORY_COMMITTED,
            self.handle_inventory_committed,
            "coordinator_inventory_committed"
        )

        event_bus.subscribe_to_event(
            SagaEvent.INVENTORY_COMMIT_FAILED,
            self.handle_inventory_commit_failed,
            "coordinator_inventory_commit_failed"
        )

        # Subscribe to compensation events
        event_bus.subscribe_to_event(
            SagaEvent.PAYMENT_REFUNDED,
            self.handle_payment_refunded,
            "coordinator_payment_refunded"
        )

        event_bus.subscribe_to_event(
            SagaEvent.INVENTORY_UNRESERVED,
            self.handle_inventory_unreserved,
            "coordinator_inventory_unreserved"
        )

        event_bus.subscribe_to_event(
            SagaEvent.ORDER_CANCELLED,
            self.handle_order_cancelled,
            "coordinator_order_cancelled"
        )

    def initiate_checkout_saga(self, cart_id: str, user_id: str, payment_method: str, billing_address: dict) -> str:
        """Initiate a new checkout saga"""
        saga_id = str(uuid.uuid4())

        # Create saga state
        saga_state.create_saga(saga_id, {
            'cart_id': cart_id,
            'user_id': user_id,
            'payment_method': payment_method,
            'billing_address': billing_address,
            'current_step': 'inventory_reservation'
        })

        # Publish checkout initiated event
        publish_checkout_initiated(
            saga_id, cart_id, user_id, payment_method, billing_address)

        return saga_id

    # Event Handlers for Forward Flow
    def handle_inventory_reserved(self, event):
        """Handle inventory reservation success"""
        data = event['data']
        saga_id = data['saga_id']

        saga = saga_state.get_saga(saga_id)
        if not saga:
            return

        # Update saga state
        saga_state.update_saga(saga_id, 'inventory_reservation', 'completed', {
            'reservation_id': data['reservation_id'],
            'current_step': 'payment_processing'
        })

        # Trigger payment processing
        from event_bus import publish_payment_requested
        publish_payment_requested(
            saga_id,
            saga['data']['cart_id'],
            saga['data'].get('total_amount', 0),
            saga['data']['payment_method'],
            f"{saga['data']['user_id']}@example.com"
        )

    def handle_inventory_reserve_failed(self, event):
        """Handle inventory reservation failure"""
        data = event['data']
        saga_id = data['saga_id']

        saga_state.update_saga(saga_id, 'inventory_reservation', 'failed')
        publish_checkout_failed(
            saga_id, f"Inventory reservation failed: {data['reason']}")

    def handle_payment_processed(self, event):
        """Handle payment processing success"""
        data = event['data']
        saga_id = data['saga_id']

        saga = saga_state.get_saga(saga_id)
        if not saga:
            return

        # Update saga state
        saga_state.update_saga(saga_id, 'payment_processing', 'completed', {
            'payment_id': data['payment_id'],
            'current_step': 'order_creation'
        })

        # Trigger order creation
        from event_bus import publish_order_create_requested
        publish_order_create_requested(
            saga_id,
            saga['data']['cart_id'],
            saga['data']['user_id'],
            data['amount'],
            data['payment_id']
        )

    def handle_payment_failed(self, event):
        """Handle payment processing failure"""
        data = event['data']
        saga_id = data['saga_id']

        saga = saga_state.get_saga(saga_id)
        if not saga:
            return

        saga_state.update_saga(saga_id, 'payment_processing', 'failed')

        # Start compensation - unreserve inventory
        if 'reservation_id' in saga['data']:
            publish_inventory_unreserve_requested(
                saga_id, saga['data']['cart_id'])

        publish_checkout_failed(saga_id, f"Payment failed: {data['reason']}")

    def handle_order_created(self, event):
        """Handle order creation success"""
        data = event['data']
        saga_id = data['saga_id']

        saga = saga_state.get_saga(saga_id)
        if not saga:
            return

        # Update saga state
        saga_state.update_saga(saga_id, 'order_creation', 'completed', {
            'order_id': data['order_id'],
            'current_step': 'inventory_commit'
        })

        # Trigger inventory commit
        from event_bus import publish_inventory_commit_requested
        publish_inventory_commit_requested(saga_id, saga['data']['cart_id'])

    def handle_order_create_failed(self, event):
        """Handle order creation failure"""
        data = event['data']
        saga_id = data['saga_id']

        saga = saga_state.get_saga(saga_id)
        if not saga:
            return

        saga_state.update_saga(saga_id, 'order_creation', 'failed')

        # Start compensation - refund payment and unreserve inventory
        if 'payment_id' in saga['data']:
            publish_payment_refund_requested(
                saga_id, saga['data']['payment_id'], 'Order creation failed')

        if 'reservation_id' in saga['data']:
            publish_inventory_unreserve_requested(
                saga_id, saga['data']['cart_id'])

        publish_checkout_failed(
            saga_id, f"Order creation failed: {data['reason']}")

    def handle_inventory_committed(self, event):
        """Handle inventory commit success - final step"""
        data = event['data']
        saga_id = data['saga_id']

        saga = saga_state.get_saga(saga_id)
        if not saga:
            return

        # Update saga state
        saga_state.update_saga(saga_id, 'inventory_commit', 'completed')
        saga_state.mark_completed(saga_id)

        # Publish success event
        publish_checkout_completed(saga_id, saga['data'].get('order_id'))

    def handle_inventory_commit_failed(self, event):
        """Handle inventory commit failure"""
        data = event['data']
        saga_id = data['saga_id']

        saga = saga_state.get_saga(saga_id)
        if not saga:
            return

        saga_state.update_saga(saga_id, 'inventory_commit', 'failed')

        # Start compensation - cancel order, refund payment, unreserve inventory
        if 'order_id' in saga['data']:
            publish_order_cancel_requested(saga_id, saga['data']['order_id'])

        if 'payment_id' in saga['data']:
            publish_payment_refund_requested(
                saga_id, saga['data']['payment_id'], 'Inventory commit failed')

        publish_checkout_failed(
            saga_id, f"Inventory commit failed: {data['reason']}")

    # Compensation Event Handlers
    def handle_payment_refunded(self, event):
        """Handle payment refund completion"""
        data = event['data']
        saga_id = data['saga_id']

        saga = saga_state.get_saga(saga_id)
        if saga and saga['status'] == 'failed':
            # Check if all compensations are done
            self.check_compensation_completion(saga_id)

    def handle_inventory_unreserved(self, event):
        """Handle inventory unreservation completion"""
        data = event['data']
        saga_id = data['saga_id']

        saga = saga_state.get_saga(saga_id)
        if saga and saga['status'] == 'failed':
            # Check if all compensations are done
            self.check_compensation_completion(saga_id)

    def handle_order_cancelled(self, event):
        """Handle order cancellation completion"""
        data = event['data']
        saga_id = data['saga_id']

        saga = saga_state.get_saga(saga_id)
        if saga and saga['status'] == 'failed':
            # Check if all compensations are done
            self.check_compensation_completion(saga_id)

    def check_compensation_completion(self, saga_id: str):
        """Check if all compensation steps are completed"""
        saga = saga_state.get_saga(saga_id)
        if not saga:
            return

        # For simplicity, mark as compensated after any compensation event
        # In a real implementation, you'd track all compensation steps
        saga_state.mark_compensated(saga_id)


# Initialize coordinator
coordinator = ChoreographedSagaCoordinator()

# API Routes


@app.route('/saga/choreography/checkout', methods=['POST'])
def initiate_choreographed_checkout():
    """Initiate a choreographed checkout saga"""
    try:
        data = request.json
        saga_id = coordinator.initiate_checkout_saga(
            cart_id=data['cart_id'],
            user_id=data['user_id'],
            payment_method=data['payment_method'],
            billing_address=data['billing_address']
        )

        return jsonify({
            'saga_id': saga_id,
            'status': 'initiated',
            'pattern': 'choreography',
            'message': 'Choreographed checkout saga started'
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/saga/choreography/<saga_id>', methods=['GET'])
def get_choreographed_saga_status(saga_id):
    """Get choreographed saga status"""
    saga = saga_state.get_saga(saga_id)
    if not saga:
        return jsonify({'error': 'Saga not found'}), 404

    return jsonify({
        'saga_id': saga_id,
        'status': saga['status'],
        'pattern': 'choreography',
        'current_step': saga['data'].get('current_step'),
        'steps_completed': saga['steps_completed'],
        'steps_failed': saga['steps_failed'],
        'compensation_needed': saga['compensation_needed'],
        'data': saga['data'],
        'created_at': saga['created_at'],
        'updated_at': saga.get('updated_at')
    })


@app.route('/saga/choreography/status', methods=['GET'])
def get_all_choreographed_sagas():
    """Get status of all choreographed sagas"""
    all_sagas = []
    for saga_id, saga in saga_state.states.items():
        all_sagas.append({
            'saga_id': saga_id,
            'status': saga['status'],
            'current_step': saga['data'].get('current_step'),
            'created_at': saga['created_at'],
            'updated_at': saga.get('updated_at')
        })

    return jsonify({
        'pattern': 'choreography',
        'sagas': all_sagas,
        'total': len(all_sagas)
    })


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'saga-choreography-coordinator'})


def start_event_consumer():
    """Start the event consumer in a separate thread"""
    def consume_events():
        try:
            event_bus.connect()
            event_bus.start_consuming()
        except KeyboardInterrupt:
            event_bus.stop_consuming()
            event_bus.close()

    consumer_thread = threading.Thread(target=consume_events)
    consumer_thread.daemon = True
    consumer_thread.start()


if __name__ == '__main__':
    # Start event consumer
    start_event_consumer()

    # Start Flask app
    app.run(host='0.0.0.0', port=3004, debug=True)
