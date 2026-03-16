package com.example.orderservice.entity;

/**
 * Enumeration of possible order statuses.
 */
public enum OrderStatus {
    CREATED,
    CONFIRMED,
    PROCESSING,
    SHIPPED,
    DELIVERED,
    CANCELLED,
    REFUNDED
}
