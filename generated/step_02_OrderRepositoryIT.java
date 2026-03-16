// === File: OrderRepositoryIT.java ===
package com.example.orderservice.repository;

import com.example.orderservice.model.Order;
import com.example.orderservice.model.OrderStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.transaction.annotation.Transactional;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
@DisplayName("OrderRepository Integration Tests")
@Tag("integration")
class OrderRepositoryIT {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine")
            .withDatabaseName("testdb")
            .withUsername("testuser")
            .withPassword("testpass");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.jpa.hibernate.ddl-auto", () -> "create-drop"); // Ensures schema is created for each test run
    }

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private TestEntityManager entityManager;

    private Order order1;
    private Order order2;
    private Order order3;

    @BeforeEach
    @Transactional
    void setUp() {
        // Clear repository to ensure test isolation
        orderRepository.deleteAll();
        entityManager.flush();

        order1 = Order.builder()
                .customerId(100L)
                .skuCode("SKU-001")
                .quantity(1)
                .totalPrice(BigDecimal.valueOf(10.00))
                .status(OrderStatus.PENDING)
                .createdAt(LocalDateTime.of(2023, 1, 1, 10, 0))
                .build();

        order2 = Order.builder()
                .customerId(100L)
                .skuCode("SKU-002")
                .quantity(2)
                .totalPrice(BigDecimal.valueOf(20.00))
                .status(OrderStatus.SHIPPED)
                .createdAt(LocalDateTime.of(2023, 1, 2, 11, 0))
                .build();

        order3 = Order.builder()
                .customerId(200L)
                .skuCode("SKU-003")
                .quantity(1)
                .totalPrice(BigDecimal.valueOf(15.00))
                .status(OrderStatus.PENDING)
                .createdAt(LocalDateTime.of(2023, 1, 3, 12, 0))
                .build();

        entityManager.persistAndFlush(order1);
        entityManager.persistAndFlush(order2);
        entityManager.persistAndFlush(order3);
    }

    @Test
    @Timeout(value = 5, unit = TimeUnit.SECONDS)
    @DisplayName("should save an order successfully")
    @Transactional
    void should_SaveOrderSuccessfully() {
        // Arrange
        Order newOrder = Order.builder()
                .customerId(300L)
                .skuCode("SKU-004")
                .quantity(5)
                .totalPrice(BigDecimal.valueOf(50.00))
                .status(OrderStatus.DELIVERED)
                .createdAt(LocalDateTime.now())
                .build();

        // Act
        Order savedOrder = orderRepository.save(newOrder);
        entityManager.flush(); // Ensure it's committed

        // Assert
        assertNotNull(savedOrder.getId());
        assertEquals(newOrder.getCustomerId(), savedOrder.getCustomerId());
        assertEquals(newOrder.getSkuCode(), savedOrder.getSkuCode());

        Optional<Order> foundOrder = orderRepository.findById(savedOrder.getId());
        assertTrue(foundOrder.isPresent());
        assertEquals(savedOrder, foundOrder.get());
    }


    @Nested
    @DisplayName("findByStatus tests")
    class FindByStatusTests {
        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return all orders with PENDING status")
        @Transactional
        void should_ReturnAllOrders_When_StatusIsPending() {
            // Act
            List<Order> pendingOrders = orderRepository.findByStatus(OrderStatus.PENDING);

            // Assert
            assertEquals(2, pendingOrders.size());
            assertTrue(pendingOrders.contains(order1));
            assertTrue(pendingOrders.contains(order3));
            assertFalse(pendingOrders.contains(order2));
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return empty list when no orders with given status")
        @Transactional
        void should_ReturnEmptyList_When_NoOrdersWithGivenStatus() {
            // Act
            List<Order> deliveredOrders = orderRepository.findByStatus(OrderStatus.DELIVERED);

            // Assert
            assertTrue(deliveredOrders.isEmpty());
        }
    }

    @Nested
    @DisplayName("findByCustomerId tests")
    class FindByCustomerIdTests {
        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return all orders for customer 100L")
        @Transactional
        void should_ReturnAllOrders_When_CustomerIdIs100() {
            // Act
            List<Order> customerOrders = orderRepository.findByCustomerId(100L);

            // Assert
            assertEquals(2, customerOrders.size());
            assertTrue(customerOrders.contains(order1));
            assertTrue(customerOrders.contains(order2));
            assertFalse(customerOrders.contains(order3));
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return empty list when no orders for non-existent customer")
        @Transactional
        void should_ReturnEmptyList_When_NoOrdersForNonExistentCustomer() {
            // Act
            List<Order> customerOrders = orderRepository.findByCustomerId(999L);

            // Assert
            assertTrue(customerOrders.isEmpty());
        }
    }

    @Nested
    @DisplayName("findOrdersBetweenDates tests")
    class FindOrdersBetweenDatesTests {
        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return orders created between specific dates")
        @Transactional
        void should_ReturnOrders_When_CreatedBetweenSpecificDates() {
            // Arrange
            LocalDateTime startDate = LocalDateTime.of(2023, 1, 1, 0, 0);
            LocalDateTime endDate = LocalDateTime.of(2023, 1, 2, 23, 59);

            // Act
            List<Order> orders = orderRepository.findOrdersBetweenDates(startDate, endDate);

            // Assert
            assertEquals(2, orders.size());
            assertTrue(orders.contains(order1));
            assertTrue(orders.contains(order2));
            assertFalse(orders.contains(order3));
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return empty list when no orders in date range")
        @Transactional
        void should_ReturnEmptyList_When_NoOrdersInDateRange() {
            // Arrange
            LocalDateTime startDate = LocalDateTime.of(2024, 1, 1, 0, 0);
            LocalDateTime endDate = LocalDateTime.of(2024, 1, 2, 23, 59);

            // Act
            List<Order> orders = orderRepository.findOrdersBetweenDates(startDate, endDate);

            // Assert
            assertTrue(orders.isEmpty());
        }
    }

    @Nested
    @DisplayName("existsByIdAndCustomerId tests")
    class ExistsByIdAndCustomerIdTests {
        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return true when order exists for ID and customer ID")
        @Transactional
        void should_ReturnTrue_When_OrderExistsForIdAndCustomerId() {
            // Act
            boolean exists = orderRepository.existsByIdAndCustomerId(order1.getId(), order1.getCustomerId());

            // Assert
            assertTrue(exists);
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return false when order ID exists but customer ID does not match")
        @Transactional
        void should_ReturnFalse_When_OrderIdExistsButCustomerIdDoesNotMatch() {
            // Act
            boolean exists = orderRepository.existsByIdAndCustomerId(order1.getId(), 999L);

            // Assert
            assertFalse(exists);
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return false when order ID does not exist")
        @Transactional
        void should_ReturnFalse_When_OrderIdDoesNotExist() {
            // Act
            boolean exists = orderRepository.existsByIdAndCustomerId(99L, order1.getCustomerId());

            // Assert
            assertFalse(exists);
        }
    }

    @Nested
    @DisplayName("findFirstByCustomerIdOrderByCreatedAtDesc tests")
    class FindFirstByCustomerIdOrderByCreatedAtDescTests {
        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return the latest order for customer 100L")
        @Transactional
        void should_ReturnLatestOrder_When_CustomerIdIs100() {
            // Act
            Optional<Order> latestOrder = orderRepository.findFirstByCustomerIdOrderByCreatedAtDesc(100L);

            // Assert
            assertTrue(latestOrder.isPresent());
            assertEquals(order2.getId(), latestOrder.get().getId()); // order2 created later than order1
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return empty optional when no orders for customer")
        @Transactional
        void should_ReturnEmptyOptional_When_NoOrdersForCustomer() {
            // Act
            Optional<Order> latestOrder = orderRepository.findFirstByCustomerIdOrderByCreatedAtDesc(999L);

            // Assert
            assertFalse(latestOrder.isPresent());
        }
    }
}