package com.example.orderservice.messaging;

import com.example.orderservice.entity.Order;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

/**
 * Kafka event producer for order lifecycle events.
 *
 * Publishes order events to dedicated Kafka topics for
 * downstream consumers (notifications, analytics, etc.).
 *
 * @author Engineering Team
 */
@Component
public class OrderEventProducer {

    private static final String TOPIC_ORDER_CREATED = "order-created";
    private static final String TOPIC_ORDER_UPDATED = "order-updated";
    private static final String TOPIC_ORDER_CANCELLED = "order-cancelled";
    private static final String TOPIC_ORDER_DELETED = "order-deleted";

    private final KafkaTemplate<String, Object> kafkaTemplate;

    public OrderEventProducer(KafkaTemplate<String, Object> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    /**
     * Publish an order-created event.
     *
     * @param order the created order
     */
    public void publishOrderCreated(Order order) {
        kafkaTemplate.send(TOPIC_ORDER_CREATED, order.getId().toString(), order);
    }

    /**
     * Publish an order-updated event.
     *
     * @param order the updated order
     */
    public void publishOrderUpdated(Order order) {
        kafkaTemplate.send(TOPIC_ORDER_UPDATED, order.getId().toString(), order);
    }

    /**
     * Publish an order-cancelled event.
     *
     * @param order the cancelled order
     */
    public void publishOrderCancelled(Order order) {
        kafkaTemplate.send(TOPIC_ORDER_CANCELLED, order.getId().toString(), order);
    }

    /**
     * Publish an order-deleted event.
     *
     * @param orderId the deleted order ID
     */
    public void publishOrderDeleted(Long orderId) {
        kafkaTemplate.send(TOPIC_ORDER_DELETED, orderId.toString(), orderId);
    }
}
