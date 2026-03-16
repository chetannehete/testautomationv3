package com.example.orderservice.repository;

import com.example.orderservice.entity.Order;
import com.example.orderservice.entity.OrderStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Spring Data JPA repository for Order entity.
 *
 * Provides standard CRUD operations plus custom queries
 * for order retrieval and filtering.
 *
 * @author Engineering Team
 */
@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {

    /**
     * Find all orders by status.
     *
     * @param status the order status
     * @return list of matching orders
     */
    List<Order> findByStatus(OrderStatus status);

    /**
     * Find all orders for a specific customer.
     *
     * @param customerId the customer ID
     * @return list of customer orders
     */
    List<Order> findByCustomerId(Long customerId);

    /**
     * Find orders created between two dates.
     *
     * @param startDate start of date range
     * @param endDate end of date range
     * @return list of matching orders
     */
    @Query("SELECT o FROM Order o WHERE o.createdAt BETWEEN :startDate AND :endDate")
    List<Order> findOrdersBetweenDates(
            @Param("startDate") LocalDateTime startDate,
            @Param("endDate") LocalDateTime endDate);

    /**
     * Check if an order exists for a given customer.
     *
     * @param orderId the order ID
     * @param customerId the customer ID
     * @return true if the order belongs to the customer
     */
    boolean existsByIdAndCustomerId(Long orderId, Long customerId);

    /**
     * Find the most recent order for a customer.
     *
     * @param customerId the customer ID
     * @return the most recent order, if any
     */
    Optional<Order> findFirstByCustomerIdOrderByCreatedAtDesc(Long customerId);
}
