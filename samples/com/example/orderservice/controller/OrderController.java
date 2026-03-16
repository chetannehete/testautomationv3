package com.example.orderservice.controller;

import com.example.orderservice.dto.OrderRequest;
import com.example.orderservice.dto.OrderResponse;
import com.example.orderservice.service.OrderService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;

/**
 * REST API controller for managing customer orders.
 *
 * Provides CRUD operations for orders with validation,
 * pagination, and search capabilities.
 *
 * @author Engineering Team
 * @version 2.0
 */
@RestController
@RequestMapping("/api/v1/orders")
@Validated
public class OrderController {

    private final OrderService orderService;

    /**
     * Constructor injection for OrderService dependency.
     *
     * @param orderService the order service
     */
    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    /**
     * Create a new order.
     *
     * @param request the order creation request with item details
     * @return the created order with HTTP 201
     */
    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(@Valid @RequestBody OrderRequest request) {
        OrderResponse response = orderService.createOrder(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    /**
     * Get an order by its unique identifier.
     *
     * @param orderId the unique order ID
     * @return the order details
     * @throws ResourceNotFoundException if order not found
     */
    @GetMapping("/{orderId}")
    public ResponseEntity<OrderResponse> getOrder(@PathVariable Long orderId) {
        OrderResponse response = orderService.getOrderById(orderId);
        return ResponseEntity.ok(response);
    }

    /**
     * Get all orders with optional filtering by status.
     *
     * @param status optional order status filter
     * @param page page number (zero-based)
     * @param size page size
     * @return list of orders
     */
    @GetMapping
    public ResponseEntity<List<OrderResponse>> getAllOrders(
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        List<OrderResponse> orders = orderService.getAllOrders(status, page, size);
        return ResponseEntity.ok(orders);
    }

    /**
     * Update an existing order.
     *
     * @param orderId the order ID to update
     * @param request the updated order data
     * @return the updated order
     * @throws ResourceNotFoundException if order not found
     */
    @PutMapping("/{orderId}")
    public ResponseEntity<OrderResponse> updateOrder(
            @PathVariable Long orderId,
            @Valid @RequestBody OrderRequest request) {
        OrderResponse response = orderService.updateOrder(orderId, request);
        return ResponseEntity.ok(response);
    }

    /**
     * Delete an order by ID.
     *
     * @param orderId the order ID to delete
     * @return HTTP 204 No Content on success
     * @throws ResourceNotFoundException if order not found
     */
    @DeleteMapping("/{orderId}")
    public ResponseEntity<Void> deleteOrder(@PathVariable Long orderId) {
        orderService.deleteOrder(orderId);
        return ResponseEntity.noContent().build();
    }

    /**
     * Cancel an active order.
     *
     * @param orderId the order ID to cancel
     * @return the cancelled order with updated status
     * @throws IllegalStateException if order cannot be cancelled
     */
    @PatchMapping("/{orderId}/cancel")
    public ResponseEntity<OrderResponse> cancelOrder(@PathVariable Long orderId) {
        OrderResponse response = orderService.cancelOrder(orderId);
        return ResponseEntity.ok(response);
    }
}
