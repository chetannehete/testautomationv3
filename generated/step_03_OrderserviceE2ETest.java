// === File: orderserviceE2ETest.java ===
package com.example.orderservice.e2e;

import com.example.orderservice.dto.OrderRequest;
import com.example.orderservice.dto.OrderResponse;
import com.example.orderservice.model.Order;
import com.example.orderservice.repository.OrderRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;
import org.testcontainers.containers.KafkaContainer;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;
import static org.awaitility.Awaitility.await;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@ActiveProfiles("e2e") // Use a specific profile for E2E tests if needed
@Tag("e2e")
@DisplayName("orderservice End-to-End Tests")
class OrderserviceE2ETest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>(DockerImageName.parse("postgres:15-alpine"))
            .withDatabaseName("e2edb")
            .withUsername("e2euser")
            .withPassword("e2epass");

    @Container
    static KafkaContainer kafka = new KafkaContainer(DockerImageName.parse("confluentinc/cp-kafka:7.4.0"));

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
        registry.add("spring.jpa.hibernate.ddl-auto", () -> "create-drop"); // Ensure clean schema for each run
        // Disable cache for testing purposes if it interferes with direct DB reads
        registry.add("spring.cache.type", () -> "none");
    }

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private ObjectMapper objectMapper; // For debugging and inspecting Kafka messages if needed

    // Shared state for CRUD flow
    private static Long createdOrderId;
    private static Long customerIdForFlow;
    private static String uniqueAddress;

    @BeforeAll
    static void setupCommon() {
        customerIdForFlow = 123L;
        uniqueAddress = "E2E Test Address - " + UUID.randomUUID();
    }

    @AfterEach
    void cleanup() {
        // Ensures clean state after each test method, especially for non-CRUD tests
        orderRepository.deleteAll();
    }

    private HttpHeaders createJsonHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        return headers;
    }

    private OrderRequest buildOrderRequest(Long customerId, String address) {
        return OrderRequest.builder()
                .customerId(customerId)
                .productIds(List.of(101L, 102L))
                .quantityMap(Map.of(101L, 2, 102L, 1))
                .deliveryAddress(address)
                .build();
    }

    @Nested
    @DisplayName("User Flow: Create, Read, Update, Delete Order")
    class OrderLifecycleTests {

        @Test
        @Order(1)
        @DisplayName("Given a valid order request, When POST /api/v1/orders, Then order is created with status 201 and persisted")
        @Transactional // Ensures order creation is part of a transaction for clean database state
        void test_1_should_CreateOrder_When_ValidRequest() {
            // Given
            OrderRequest request = buildOrderRequest(customerIdForFlow, uniqueAddress);
            HttpEntity<OrderRequest> entity = new HttpEntity<>(request, createJsonHeaders());

            // When
            ResponseEntity<OrderResponse> response = restTemplate.exchange(
                    "/api/v1/orders", HttpMethod.POST, entity, OrderResponse.class);

            // Then
            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().getCustomerId()).isEqualTo(customerIdForFlow);
            assertThat(response.getBody().getStatus()).isEqualTo("CREATED");
            assertThat(response.getBody().getDeliveryAddress()).isEqualTo(uniqueAddress);

            createdOrderId = response.getBody().getOrderId(); // Save for subsequent tests
            assertThat(createdOrderId).isNotNull();

            // [E2E-H07] Database state verification
            await().atMost(5, TimeUnit.SECONDS).untilAsserted(() -> {
                Optional<Order> savedOrder = orderRepository.findById(createdOrderId);
                assertThat(savedOrder).isPresent();
                assertThat(savedOrder.get().getCustomerId()).isEqualTo(customerIdForFlow);
                assertThat(savedOrder.get().getStatus()).isEqualTo("CREATED");
                assertThat(savedOrder.get().getDeliveryAddress()).isEqualTo(uniqueAddress);
            });
        }

        @Test
        @Order(2)
        @DisplayName("Given an existing order, When GET /api/v1/orders/{orderId}, Then order details are returned with status 200")
        void test_2_should_GetOrder_When_ExistingOrderId() {
            // Given: order created in test_1_should_CreateOrder_When_ValidRequest
            assertThat(createdOrderId).isNotNull(); // Ensure previous test ran and set ID

            // When
            ResponseEntity<OrderResponse> response = restTemplate.exchange(
                    "/api/v1/orders/{orderId}", HttpMethod.GET, null, OrderResponse.class, createdOrderId);

            // Then
            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().getOrderId()).isEqualTo(createdOrderId);
            assertThat(response.getBody().getCustomerId()).isEqualTo(customerIdForFlow);
            assertThat(response.getBody().getStatus()).isEqualTo("CREATED");
            assertThat(response.getBody().getDeliveryAddress()).isEqualTo(uniqueAddress);
        }

        @Test
        @Order(3)
        @DisplayName("Given multiple orders exist, When GET /api/v1/orders/allOrders, Then a list of orders is returned with status 200")
        @Transactional
        void test_3_should_GetAllOrders_When_OrdersExist() throws JsonProcessingException {
            // Given: order created in test_1
            // Create another order for this test
            String anotherUniqueAddress = "Another E2E Test Address - " + UUID.randomUUID();
            OrderRequest anotherRequest = buildOrderRequest(customerIdForFlow + 1, anotherUniqueAddress);
            restTemplate.postForEntity("/api/v1/orders", new HttpEntity<>(anotherRequest, createJsonHeaders()), OrderResponse.class);

            // When
            ResponseEntity<List<OrderResponse>> response = restTemplate.exchange(
                    "/api/v1/orders/allOrders?page=0&size=10",
                    HttpMethod.GET,
                    null,
                    new ParameterizedTypeReference<List<OrderResponse>>() {});

            // Then
            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody()).hasSize(2);
            assertThat(response.getBody().stream().anyMatch(o -> o.getOrderId().equals(createdOrderId))).isTrue();
            assertThat(response.getBody().stream().anyMatch(o -> o.getDeliveryAddress().equals(anotherUniqueAddress))).isTrue();
        }

        @Test
        @Order(4)
        @DisplayName("Given an existing order, When PUT /api/v1/orders/{orderId}, Then order is updated with status 200 and persisted")
        @Transactional
        void test_4_should_UpdateOrder_When_ExistingOrderIdAndValidRequest() {
            // Given: order created in test_1
            assertThat(createdOrderId).isNotNull();
            String updatedAddress = "Updated E2E Address - " + UUID.randomUUID();
            OrderRequest updateRequest = buildOrderRequest(customerIdForFlow, updatedAddress); // Customer ID should generally not change

            HttpEntity<OrderRequest> entity = new HttpEntity<>(updateRequest, createJsonHeaders());

            // When
            ResponseEntity<OrderResponse> response = restTemplate.exchange(
                    "/api/v1/orders/{orderId}", HttpMethod.PUT, entity, OrderResponse.class, createdOrderId);

            // Then
            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().getOrderId()).isEqualTo(createdOrderId);
            assertThat(response.getBody().getDeliveryAddress()).isEqualTo(updatedAddress);

            // [E2E-H07] Database state verification
            await().atMost(5, TimeUnit.SECONDS).untilAsserted(() -> {
                Optional<Order> updatedOrder = orderRepository.findById(createdOrderId);
                assertThat(updatedOrder).isPresent();
                assertThat(updatedOrder.get().getDeliveryAddress()).isEqualTo(updatedAddress);
            });
        }

        @Test
        @Order(5)
        @DisplayName("Given an existing order with 'CREATED' status, When PATCH /api/v1/orders/{orderId}/cancel, Then order status is 'CANCELLED' with status 200 and persisted")
        @Transactional
        void test_5_should_CancelOrder_When_ExistingOrderIdAndCancellable() {
            // Given: order created in test_1, updated in test_4
            // Ensure status is CREATED or a cancellable status
            assertThat(createdOrderId).isNotNull();
            Order orderToCancel = orderRepository.findById(createdOrderId).get();
            orderToCancel.setStatus("CREATED"); // Manually set to cancellable status for this flow
            orderRepository.saveAndFlush(orderToCancel);


            HttpEntity<Void> entity = new HttpEntity<>(createJsonHeaders());

            // When
            ResponseEntity<OrderResponse> response = restTemplate.exchange(
                    "/api/v1/orders/{orderId}/cancel", HttpMethod.PATCH, entity, OrderResponse.class, createdOrderId);

            // Then
            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().getOrderId()).isEqualTo(createdOrderId);
            assertThat(response.getBody().getStatus()).isEqualTo("CANCELLED");

            // [E2E-H07] Database state verification
            await().atMost(5, TimeUnit.SECONDS).untilAsserted(() -> {
                Optional<Order> cancelledOrder = orderRepository.findById(createdOrderId);
                assertThat(cancelledOrder).isPresent();
                assertThat(cancelledOrder.get().getStatus()).isEqualTo("CANCELLED");
            });
        }

        @Test
        @Order(6)
        @DisplayName("Given an existing order, When DELETE /api/v1/orders/{orderId}, Then order is deleted with status 204 and removed from database")
        @Transactional
        void test_6_should_DeleteOrder_When_ExistingOrderId() {
            // Given: order created in test_1, cancelled in test_5
            assertThat(createdOrderId).isNotNull();

            // When
            ResponseEntity<Void> response = restTemplate.exchange(
                    "/api/v1/orders/{orderId}", HttpMethod.DELETE, null, Void.class, createdOrderId);

            // Then
            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);

            // [E2E-H07] Database state verification
            await().atMost(5, TimeUnit.SECONDS).untilAsserted(() -> {
                Optional<Order> deletedOrder = orderRepository.findById(createdOrderId);
                assertThat(deletedOrder).isNotPresent();
            });
        }
    }

    @Nested
    @DisplayName("Error Handling and Edge Cases")
    class ErrorAndEdgeCaseTests {

        @Test
        @DisplayName("Given a non-existent order ID, When GET /api/v1/orders/{orderId}, Then return 404 NOT FOUND")
        void should_Return404_When_GetNonExistentOrder() {
            // Given
            Long nonExistentOrderId = 9999L;

            // When
            ResponseEntity<Map> response = restTemplate.exchange(
                    "/api/v1/orders/{orderId}", HttpMethod.GET, null, Map.class, nonExistentOrderId);

            // Then
            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody()).containsKeys("timestamp", "status", "message");
            assertThat(response.getBody().get("status")).isEqualTo(404);
        }

        @Test
        @DisplayName("Given an invalid order request (null customerId), When POST /api/v1/orders, Then return 400 BAD REQUEST")
        void should_Return400_When_InvalidCreateRequest() {
            // Given
            OrderRequest invalidRequest = OrderRequest.builder()
                    .customerId(null) // Invalid field
                    .productIds(List.of(1L))
                    .quantityMap(Map.of(1L, 1))
                    .deliveryAddress("Invalid Address")
                    .build();
            HttpEntity<OrderRequest> entity = new HttpEntity<>(invalidRequest, createJsonHeaders());

            // When
            ResponseEntity<Map> response = restTemplate.exchange(
                    "/api/v1/orders", HttpMethod.POST, entity, Map.class);

            // Then
            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody()).containsKeys("timestamp", "status", "message");
            assertThat(response.getBody().get("status")).isEqualTo(400);
            assertThat(response.getBody().get("message").toString()).contains("customerId must not be null");
        }

        @Test
        @Transactional
        @DisplayName("Given an order in a non-cancellable state (DELIVERED), When PATCH /api/v1/orders/{orderId}/cancel, Then return 409 CONFLICT")
        void should_Return409_When_AttemptToCancelNonCancellableOrder() {
            // Given
            Order deliveredOrder = orderRepository.save(Order.builder()
                    .customerId(UUID.randomUUID().getLeastSignificantBits())
                    .status("DELIVERED")
                    .totalAmount(200.0)
                    .deliveryAddress("Delivered Address")
                    .build());

            HttpEntity<Void> entity = new HttpEntity<>(createJsonHeaders());

            // When
            ResponseEntity<Map> response = restTemplate.exchange(
                    "/api/v1/orders/{orderId}/cancel", HttpMethod.PATCH, entity, Map.class, deliveredOrder.getId());

            // Then
            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody()).containsKeys("timestamp", "status", "message");
            assertThat(response.getBody().get("status")).isEqualTo(409);
            assertThat(response.getBody().get("message").toString()).contains("Order status prevents cancellation");

            // Verify DB state remains unchanged
            await().atMost(3, TimeUnit.SECONDS).untilAsserted(() -> {
                Optional<Order> dbOrder = orderRepository.findById(deliveredOrder.getId());
                assertThat(dbOrder).isPresent();
                assertThat(dbOrder.get().getStatus()).isEqualTo("DELIVERED");
            });
        }

        @Test
        @DisplayName("Given a valid order request, When POST /api/v1/orders twice, Then two distinct orders are created (not idempotent)")
        @Transactional
        void should_CreateTwoOrders_When_PostRequestTwice() {
            // Given
            Long customerId = UUID.randomUUID().getLeastSignificantBits();
            String address = "Idempotency Test Address - " + UUID.randomUUID();
            OrderRequest request = buildOrderRequest(customerId, address);
            HttpEntity<OrderRequest> entity = new HttpEntity<>(request, createJsonHeaders());

            // When
            ResponseEntity<OrderResponse> response1 = restTemplate.exchange(
                    "/api/v1/orders", HttpMethod.POST, entity, OrderResponse.class);
            ResponseEntity<OrderResponse> response2 = restTemplate.exchange(
                    "/api/v1/orders", HttpMethod.POST, entity, OrderResponse.class);

            // Then
            assertThat(response1.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(response2.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(response1.getBody()).isNotNull();
            assertThat(response2.getBody()).isNotNull();
            assertThat(response1.getBody().getOrderId()).isNotEqualTo(response2.getBody().getOrderId());

            // Verify DB state
            await().atMost(5, TimeUnit.SECONDS).untilAsserted(() -> {
                List<Order> orders = orderRepository.findByCustomerId(customerId);
                assertThat(orders).hasSize(2);
            });
        }

        @Test
        @DisplayName("Given an existing order, When PUT /api/v1/orders/{orderId} twice with same update, Then order is updated once (idempotent)")
        @Transactional
        void should_UpdateOrderOnce_When_PutRequestTwice() {
            // Given
            Long customerId = UUID.randomUUID().getLeastSignificantBits();
            Order initialOrder = orderRepository.save(Order.builder()
                    .customerId(customerId)
                    .status("CREATED")
                    .totalAmount(10.0)
                    .deliveryAddress("Initial Address")
                    .build());
            Long orderId = initialOrder.getId();

            String updatedAddress = "Updated Address for Idempotency - " + UUID.randomUUID();
            OrderRequest updateRequest = buildOrderRequest(customerId, updatedAddress);
            HttpEntity<OrderRequest> entity = new HttpEntity<>(updateRequest, createJsonHeaders());

            // When
            ResponseEntity<OrderResponse> response1 = restTemplate.exchange(
                    "/api/v1/orders/{orderId}", HttpMethod.PUT, entity, OrderResponse.class, orderId);
            ResponseEntity<OrderResponse> response2 = restTemplate.exchange(
                    "/api/v1/orders/{orderId}", HttpMethod.PUT, entity, OrderResponse.class, orderId);

            // Then
            assertThat(response1.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response2.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response1.getBody()).isNotNull();
            assertThat(response2.getBody()).isNotNull();
            // Both responses should reflect the same updated state
            assertThat(response1.getBody().getDeliveryAddress()).isEqualTo(updatedAddress);
            assertThat(response2.getBody().getDeliveryAddress()).isEqualTo(updatedAddress);

            // Verify DB state: only one record and it's updated
            await().atMost(5, TimeUnit.SECONDS).untilAsserted(() -> {
                Optional<Order> dbOrder = orderRepository.findById(orderId);
                assertThat(dbOrder).isPresent();
                assertThat(dbOrder.get().getDeliveryAddress()).isEqualTo(updatedAddress);
                List<Order> orders = orderRepository.findByCustomerId(customerId);
                assertThat(orders).hasSize(1); // Still only one order, just updated
            });
        }
    }
}