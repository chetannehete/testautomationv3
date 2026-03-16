// === File: OrderControllerIT.java ===
package com.example.orderservice.controller;

import com.example.orderservice.dto.OrderRequest;
import com.example.orderservice.dto.OrderResponse;
import com.example.orderservice.exception.ResourceNotFoundException;
import com.example.orderservice.service.OrderService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.TimeUnit;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(OrderController.class)
@AutoConfigureMockMvc
@DisplayName("OrderController Integration Tests")
@Tag("integration")
class OrderControllerIT {

    private static final String BASE_PATH = "/api/v1/orders";

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private OrderService orderService;

    private OrderRequest sampleOrderRequest() {
        return new OrderRequest(1L, "SKU-TEST-001", 1, 99.99);
    }

    private OrderResponse sampleOrderResponse(Long id, String status) {
        return new OrderResponse(id, 1L, "SKU-TEST-001", 1, 99.99, status, LocalDateTime.now(), LocalDateTime.now());
    }

    @Nested
    @DisplayName("POST /api/v1/orders - createOrder")
    class CreateOrderTests {
        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 201 CREATED and the created order when valid request")
        void should_Return201CreatedAndCreatedOrder_When_ValidRequest() throws Exception {
            // Arrange
            OrderRequest request = sampleOrderRequest();
            OrderResponse response = sampleOrderResponse(1L, "PENDING");
            when(orderService.createOrder(any(OrderRequest.class))).thenReturn(response);

            // Act & Assert
            mockMvc.perform(post(BASE_PATH)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(objectMapper.writeValueAsString(request)))
                    .andExpect(status().isCreated())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.orderId").value(response.orderId()))
                    .andExpect(jsonPath("$.status").value("PENDING"));

            verify(orderService, times(1)).createOrder(any(OrderRequest.class));
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 400 BAD REQUEST when request body is invalid")
        void should_Return400BadRequest_When_RequestBodyIsInvalid() throws Exception {
            // Arrange
            OrderRequest invalidRequest = new OrderRequest(1L, null, 1, 99.99); // Invalid SKU
            when(orderService.createOrder(any(OrderRequest.class))).thenThrow(new IllegalArgumentException("Invalid SKU code"));

            // Act & Assert
            mockMvc.perform(post(BASE_PATH)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(objectMapper.writeValueAsString(invalidRequest)))
                    .andExpect(status().isBadRequest())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.status").value(400))
                    .andExpect(jsonPath("$.message").exists());

            verify(orderService, times(1)).createOrder(any(OrderRequest.class));
        }
    }

    @Nested
    @DisplayName("GET /api/v1/orders/{orderId} - getOrder")
    class GetOrderTests {
        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 200 OK and order details when valid order ID")
        void should_Return200OkAndOrderDetails_When_ValidOrderId() throws Exception {
            // Arrange
            Long orderId = 1L;
            OrderResponse response = sampleOrderResponse(orderId, "PENDING");
            when(orderService.getOrderById(orderId)).thenReturn(response);

            // Act & Assert
            mockMvc.perform(get(BASE_PATH + "/{orderId}", orderId)
                            .contentType(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.orderId").value(orderId))
                    .andExpect(jsonPath("$.status").value("PENDING"));

            verify(orderService, times(1)).getOrderById(orderId);
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 404 NOT FOUND when order ID does not exist")
        void should_Return404NotFound_When_OrderIdDoesNotExist() throws Exception {
            // Arrange
            Long nonExistentOrderId = 99L;
            when(orderService.getOrderById(nonExistentOrderId)).thenThrow(new ResourceNotFoundException("Order not found"));

            // Act & Assert
            mockMvc.perform(get(BASE_PATH + "/{orderId}", nonExistentOrderId)
                            .contentType(MediaType.APPLICATION_JSON))
                    .andExpect(status().isNotFound())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.status").value(404))
                    .andExpect(jsonPath("$.message").value("Order not found"));

            verify(orderService, times(1)).getOrderById(nonExistentOrderId);
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 400 BAD REQUEST when order ID is invalid (e.g., negative)")
        void should_Return400BadRequest_When_OrderIdIsInvalid() throws Exception {
            // Arrange
            Long invalidOrderId = -1L;
            when(orderService.getOrderById(invalidOrderId)).thenThrow(new IllegalArgumentException("Order ID cannot be negative"));

            // Act & Assert
            mockMvc.perform(get(BASE_PATH + "/{orderId}", invalidOrderId)
                            .contentType(MediaType.APPLICATION_JSON))
                    .andExpect(status().isBadRequest())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.status").value(400))
                    .andExpect(jsonPath("$.message").exists());

            verify(orderService, times(1)).getOrderById(invalidOrderId);
        }
    }

    @Nested
    @DisplayName("GET /api/v1/orders/allOrders - getAllOrders")
    class GetAllOrdersTests {
        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 200 OK and a list of orders when no status filter")
        void should_Return200OkAndListOfOrders_When_NoStatusFilter() throws Exception {
            // Arrange
            List<OrderResponse> responses = List.of(sampleOrderResponse(1L, "PENDING"), sampleOrderResponse(2L, "SHIPPED"));
            when(orderService.getAllOrders(null, 0, 10)).thenReturn(responses);

            // Act & Assert
            mockMvc.perform(get(BASE_PATH + "/allOrders")
                            .param("page", "0")
                            .param("size", "10")
                            .contentType(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.length()").value(2))
                    .andExpect(jsonPath("$[0].status").value("PENDING"));

            verify(orderService, times(1)).getAllOrders(null, 0, 10);
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 200 OK and filtered orders when status filter provided")
        void should_Return200OkAndFilteredOrders_When_StatusFilterProvided() throws Exception {
            // Arrange
            List<OrderResponse> responses = List.of(sampleOrderResponse(1L, "PENDING"));
            when(orderService.getAllOrders(eq("PENDING"), any(Integer.class), any(Integer.class))).thenReturn(responses);

            // Act & Assert
            mockMvc.perform(get(BASE_PATH + "/allOrders")
                            .param("status", "PENDING")
                            .param("page", "0")
                            .param("size", "10")
                            .contentType(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.length()").value(1))
                    .andExpect(jsonPath("$[0].status").value("PENDING"));

            verify(orderService, times(1)).getAllOrders("PENDING", 0, 10);
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 200 OK and empty list when no orders match status filter")
        void should_Return200OkAndEmptyList_When_NoOrdersMatchStatusFilter() throws Exception {
            // Arrange
            when(orderService.getAllOrders(eq("COMPLETED"), any(Integer.class), any(Integer.class))).thenReturn(Collections.emptyList());

            // Act & Assert
            mockMvc.perform(get(BASE_PATH + "/allOrders")
                            .param("status", "COMPLETED")
                            .param("page", "0")
                            .param("size", "10")
                            .contentType(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.length()").value(0));

            verify(orderService, times(1)).getAllOrders("COMPLETED", 0, 10);
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 400 BAD REQUEST when invalid pagination parameters")
        void should_Return400BadRequest_When_InvalidPaginationParameters() throws Exception {
            // Arrange
            when(orderService.getAllOrders(any(), eq(-1), anyInt()))
                    .thenThrow(new IllegalArgumentException("Page index must not be less than zero!"));

            // Act & Assert
            mockMvc.perform(get(BASE_PATH + "/allOrders")
                            .param("page", "-1")
                            .param("size", "10")
                            .contentType(MediaType.APPLICATION_JSON))
                    .andExpect(status().isBadRequest())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.status").value(400))
                    .andExpect(jsonPath("$.message").exists());

            verify(orderService, times(1)).getAllOrders(null, -1, 10);
        }
    }

    @Nested
    @DisplayName("PUT /api/v1/orders/{orderId} - updateOrder")
    class UpdateOrderTests {
        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 200 OK and updated order when valid ID and request")
        void should_Return200OkAndUpdatedOrder_When_ValidIdAndRequest() throws Exception {
            // Arrange
            Long orderId = 1L;
            OrderRequest request = new OrderRequest(1L, "UPDATED_SKU", 3, 150.00);
            OrderResponse response = sampleOrderResponse(orderId, "UPDATED");
            when(orderService.updateOrder(eq(orderId), any(OrderRequest.class))).thenReturn(response);

            // Act & Assert
            mockMvc.perform(put(BASE_PATH + "/{orderId}", orderId)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(objectMapper.writeValueAsString(request)))
                    .andExpect(status().isOk())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.orderId").value(orderId))
                    .andExpect(jsonPath("$.status").value("UPDATED"));

            verify(orderService, times(1)).updateOrder(eq(orderId), any(OrderRequest.class));
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 404 NOT FOUND when order ID for update does not exist")
        void should_Return404NotFound_When_OrderIdForUpdateDoesNotExist() throws Exception {
            // Arrange
            Long nonExistentOrderId = 99L;
            OrderRequest request = sampleOrderRequest();
            when(orderService.updateOrder(eq(nonExistentOrderId), any(OrderRequest.class))).thenThrow(new ResourceNotFoundException("Order not found"));

            // Act & Assert
            mockMvc.perform(put(BASE_PATH + "/{orderId}", nonExistentOrderId)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(objectMapper.writeValueAsString(request)))
                    .andExpect(status().isNotFound())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.status").value(404))
                    .andExpect(jsonPath("$.message").value("Order not found"));

            verify(orderService, times(1)).updateOrder(eq(nonExistentOrderId), any(OrderRequest.class));
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 400 BAD REQUEST when update request is invalid")
        void should_Return400BadRequest_When_UpdateRequestIsInvalid() throws Exception {
            // Arrange
            Long orderId = 1L;
            OrderRequest invalidRequest = new OrderRequest(1L, "SKU-TEST-001", 0, 99.99); // Invalid quantity
            when(orderService.updateOrder(eq(orderId), any(OrderRequest.class))).thenThrow(new IllegalArgumentException("Quantity must be positive"));

            // Act & Assert
            mockMvc.perform(put(BASE_PATH + "/{orderId}", orderId)
                            .contentType(MediaType.APPLICATION_JSON)
                            .content(objectMapper.writeValueAsString(invalidRequest)))
                    .andExpect(status().isBadRequest())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.status").value(400))
                    .andExpect(jsonPath("$.message").exists());

            verify(orderService, times(1)).updateOrder(eq(orderId), any(OrderRequest.class));
        }
    }

    @Nested
    @DisplayName("DELETE /api/v1/orders/{orderId} - deleteOrder")
    class DeleteOrderTests {
        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 204 NO CONTENT when valid order ID is deleted")
        void should_Return204NoContent_When_ValidOrderIdIsDeleted() throws Exception {
            // Arrange
            Long orderId = 1L;
            doNothing().when(orderService).deleteOrder(orderId);

            // Act & Assert
            mockMvc.perform(delete(BASE_PATH + "/{orderId}", orderId))
                    .andExpect(status().isNoContent());

            verify(orderService, times(1)).deleteOrder(orderId);
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 404 NOT FOUND when order ID for delete does not exist")
        void should_Return404NotFound_When_OrderIdForDeleteDoesNotExist() throws Exception {
            // Arrange
            Long nonExistentOrderId = 99L;
            doThrow(new ResourceNotFoundException("Order not found")).when(orderService).deleteOrder(nonExistentOrderId);

            // Act & Assert
            mockMvc.perform(delete(BASE_PATH + "/{orderId}", nonExistentOrderId))
                    .andExpect(status().isNotFound())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.status").value(404))
                    .andExpect(jsonPath("$.message").value("Order not found"));

            verify(orderService, times(1)).deleteOrder(nonExistentOrderId);
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 400 BAD REQUEST when order ID is invalid (e.g., negative)")
        void should_Return400BadRequest_When_OrderIdIsInvalid() throws Exception {
            // Arrange
            Long invalidOrderId = -1L;
            doThrow(new IllegalArgumentException("Order ID cannot be negative")).when(orderService).deleteOrder(invalidOrderId);

            // Act & Assert
            mockMvc.perform(delete(BASE_PATH + "/{orderId}", invalidOrderId))
                    .andExpect(status().isBadRequest())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.status").value(400))
                    .andExpect(jsonPath("$.message").exists());

            verify(orderService, times(1)).deleteOrder(invalidOrderId);
        }
    }

    @Nested
    @DisplayName("PATCH /api/v1/orders/{orderId}/cancel - cancelOrder")
    class CancelOrderTests {
        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 200 OK and cancelled order when valid order ID")
        void should_Return200OkAndCancelledOrder_When_ValidOrderId() throws Exception {
            // Arrange
            Long orderId = 1L;
            OrderResponse response = sampleOrderResponse(orderId, "CANCELLED");
            when(orderService.cancelOrder(orderId)).thenReturn(response);

            // Act & Assert
            mockMvc.perform(patch(BASE_PATH + "/{orderId}/cancel", orderId)
                            .contentType(MediaType.APPLICATION_JSON))
                    .andExpect(status().isOk())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.orderId").value(orderId))
                    .andExpect(jsonPath("$.status").value("CANCELLED"));

            verify(orderService, times(1)).cancelOrder(orderId);
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 404 NOT FOUND when order ID for cancel does not exist")
        void should_Return404NotFound_When_OrderIdForCancelDoesNotExist() throws Exception {
            // Arrange
            Long nonExistentOrderId = 99L;
            when(orderService.cancelOrder(nonExistentOrderId)).thenThrow(new ResourceNotFoundException("Order not found"));

            // Act & Assert
            mockMvc.perform(patch(BASE_PATH + "/{orderId}/cancel", nonExistentOrderId)
                            .contentType(MediaType.APPLICATION_JSON))
                    .andExpect(status().isNotFound())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.status").value(404))
                    .andExpect(jsonPath("$.message").value("Order not found"));

            verify(orderService, times(1)).cancelOrder(nonExistentOrderId);
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 409 CONFLICT when order cannot be cancelled due to status")
        void should_Return409Conflict_When_OrderCannotBeCancelled() throws Exception {
            // Arrange
            Long orderId = 1L;
            when(orderService.cancelOrder(orderId)).thenThrow(new IllegalStateException("Order already shipped, cannot be cancelled"));

            // Act & Assert
            mockMvc.perform(patch(BASE_PATH + "/{orderId}/cancel", orderId)
                            .contentType(MediaType.APPLICATION_JSON))
                    .andExpect(status().isConflict())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.status").value(409))
                    .andExpect(jsonPath("$.message").value("Order already shipped, cannot be cancelled"));

            verify(orderService, times(1)).cancelOrder(orderId);
        }

        @Test
        @Timeout(value = 5, unit = TimeUnit.SECONDS)
        @DisplayName("should return 400 BAD REQUEST when order ID is invalid (e.g., negative)")
        void should_Return400BadRequest_When_OrderIdIsInvalid() throws Exception {
            // Arrange
            Long invalidOrderId = -1L;
            when(orderService.cancelOrder(invalidOrderId)).thenThrow(new IllegalArgumentException("Order ID cannot be negative"));

            // Act & Assert
            mockMvc.perform(patch(BASE_PATH + "/{orderId}/cancel", invalidOrderId)
                            .contentType(MediaType.APPLICATION_JSON))
                    .andExpect(status().isBadRequest())
                    .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                    .andExpect(jsonPath("$.status").value(400))
                    .andExpect(jsonPath("$.message").exists());

            verify(orderService, times(1)).cancelOrder(invalidOrderId);
        }
    }
}