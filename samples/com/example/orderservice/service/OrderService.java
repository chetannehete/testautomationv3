package com.example.orderservice.service;

import com.example.orderservice.dto.OrderRequest;
import com.example.orderservice.dto.OrderResponse;
import com.example.orderservice.entity.Order;
import com.example.orderservice.entity.OrderStatus;
import com.example.orderservice.exception.ResourceNotFoundException;
import com.example.orderservice.mapper.OrderMapper;
import com.example.orderservice.repository.OrderRepository;
import com.example.orderservice.messaging.OrderEventProducer;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Core business logic for order management.
 *
 * Handles order creation, retrieval, updating, deletion, and cancellation.
 * Publishes events to Kafka for downstream consumers.
 * Uses caching for frequently accessed orders.
 *
 * @author Engineering Team
 */
@Service
@Transactional
public class OrderService {

    private final OrderRepository orderRepository;
    private final OrderMapper orderMapper;
    private final OrderEventProducer eventProducer;

    public OrderService(OrderRepository orderRepository,
                        OrderMapper orderMapper,
                        OrderEventProducer eventProducer) {
        this.orderRepository = orderRepository;
        this.orderMapper = orderMapper;
        this.eventProducer = eventProducer;
    }

    /**
     * Create a new order from the given request.
     *
     * @param request the order request with items
     * @return the created order response
     */
    public OrderResponse createOrder(OrderRequest request) {
        Order order = orderMapper.toEntity(request);
        order.setStatus(OrderStatus.CREATED);
        order.setCreatedAt(LocalDateTime.now());
        Order saved = orderRepository.save(order);
        eventProducer.publishOrderCreated(saved);
        return orderMapper.toResponse(saved);
    }

    /**
     * Get order by ID with caching.
     *
     * @param id the order ID
     * @return the order response
     * @throws ResourceNotFoundException if not found
     */
    @Cacheable(value = "orders", key = "#id")
    public OrderResponse getOrderById(Long id) throws ResourceNotFoundException {
        Order order = orderRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found: " + id));
        return orderMapper.toResponse(order);
    }

    /**
     * Get all orders with optional status filter.
     *
     * @param status optional status filter
     * @param page page number
     * @param size page size
     * @return list of order responses
     */
    public List<OrderResponse> getAllOrders(String status, int page, int size) {
        List<Order> orders;
        if (status != null && !status.isEmpty()) {
            orders = orderRepository.findByStatus(OrderStatus.valueOf(status.toUpperCase()));
        } else {
            orders = orderRepository.findAll();
        }
        return orders.stream().map(orderMapper::toResponse).collect(Collectors.toList());
    }

    /**
     * Update an existing order.
     *
     * @param id the order ID
     * @param request the update request
     * @return the updated order response
     * @throws ResourceNotFoundException if not found
     */
    public OrderResponse updateOrder(Long id, OrderRequest request) throws ResourceNotFoundException {
        Order existing = orderRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found: " + id));
        orderMapper.updateEntity(existing, request);
        existing.setUpdatedAt(LocalDateTime.now());
        Order saved = orderRepository.save(existing);
        eventProducer.publishOrderUpdated(saved);
        return orderMapper.toResponse(saved);
    }

    /**
     * Delete an order by ID.
     *
     * @param id the order ID
     * @throws ResourceNotFoundException if not found
     */
    public void deleteOrder(Long id) throws ResourceNotFoundException {
        if (!orderRepository.existsById(id)) {
            throw new ResourceNotFoundException("Order not found: " + id);
        }
        orderRepository.deleteById(id);
        eventProducer.publishOrderDeleted(id);
    }

    /**
     * Cancel an active order.
     *
     * @param id the order ID
     * @return the cancelled order
     * @throws ResourceNotFoundException if not found
     * @throws IllegalStateException if order cannot be cancelled
     */
    public OrderResponse cancelOrder(Long id) throws ResourceNotFoundException, IllegalStateException {
        Order order = orderRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found: " + id));
        if (order.getStatus() == OrderStatus.SHIPPED || order.getStatus() == OrderStatus.DELIVERED) {
            throw new IllegalStateException("Cannot cancel order in status: " + order.getStatus());
        }
        order.setStatus(OrderStatus.CANCELLED);
        order.setUpdatedAt(LocalDateTime.now());
        Order saved = orderRepository.save(order);
        eventProducer.publishOrderCancelled(saved);
        return orderMapper.toResponse(saved);
    }

    /**
     * Check if an order belongs to a specific customer.
     *
     * @param orderId the order ID
     * @param customerId the customer ID
     * @return true if the order belongs to the customer
     */
    public boolean isOrderOwnedByCustomer(Long orderId, Long customerId) {
        return orderRepository.existsByIdAndCustomerId(orderId, customerId);
    }
}
