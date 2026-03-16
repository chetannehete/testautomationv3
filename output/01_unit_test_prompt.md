# Prompt: Step 01/06 -- UNIT TEST

---

## Chain Context

| Field | Value |
|-------|-------|
| **Invoked By** | `00_master_prompt.md` |
| **Step** | 01 of 06 |
| **Previous Step** | *(first step)* |
| **Next Step** | `02_..._prompt.md` |

Once this step is complete, output: `[STEP 01 COMPLETE] -- [one-line summary]` and proceed to Step 02.

---

## Purpose
Generate JUnit5 + Mockito unit tests for 5 class(es)

## Conditional Trigger
> 5 testable Spring Boot class(es) detected

## Target Classes
OrderController, GlobalExceptionHandler, OrderEventProducer, OrderRepository, OrderService

---

## Hard Rules (Mandatory)
- **[UT-H01]** Use JUnit5 annotations only (@Test, @BeforeEach, @AfterEach, @DisplayName). Do NOT use JUnit4.
- **[UT-H02]** Use Mockito (@Mock, @InjectMocks, @ExtendWith(MockitoExtension.class)) for ALL injected dependencies.
- **[UT-H03]** Follow the Arrange-Act-Assert (AAA) pattern in every test method. Add // Arrange, // Act, // Assert comments.
- **[UT-H04]** Use @DisplayName with descriptive English sentences on every test.
- **[UT-H05]** Test class name MUST be {ClassName}Test, matching the source class exactly.
- **[UT-H06]** Each test must be independent. No shared mutable state between tests.
- **[UT-H07]** Verify void dependency calls using Mockito.verify().
- **[UT-H08]** Test naming convention: should_ExpectedBehavior_When_Condition().
- **[UT-H09]** Cover at minimum: happy path, null inputs (for nullable params), boundary values (for numeric params), and exception paths (for declared exceptions).
- **[UT-H10]** Use assertThrows() for exception testing. Never use try-catch to test exceptions.
- **[UT-H11]** Never use @SuppressWarnings to hide test warnings.
- **[UT-H12]** Do NOT use Thread.sleep() in unit tests. Use Awaitility for async testing if needed.
- **[UT-H13]** Assert with specific matchers (assertEquals, assertTrue, assertFalse). Avoid standalone assertNotNull unless specifically testing for non-null.
- **[UT-H14]** Each test should focus on one logical assertion (or use assertAll for closely related property assertions).
- **[UT-H15]** Do NOT initialize mocks manually (e.g., Mockito.mock()). Rely solely on @ExtendWith(MockitoExtension.class) + @Mock.
- **[UT-H16]** When the exact argument value is knowable, use it in stubbing. Avoid Mockito.any() unless the argument is genuinely irrelevant.
- **[UT-H17]** Generate one test file per source class listed in the Class Inventory below.
- **[UT-H18]** Every generated test file must be fully compilable without modification. Include all imports.

## Soft Rules (Recommended)
- **[UT-S01]** Use @ParameterizedTest with @ValueSource or @MethodSource for methods accepting multiple valid input variations.
- **[UT-S02]** Use ArgumentCaptor when verifying complex objects passed to mocks.
- **[UT-S03]** Group tests using @Nested inner classes, one per method under test.
- **[UT-S04]** Keep each test method under 20 lines for readability.
- **[UT-S05]** Use factory methods or test data builders for complex test object construction.
- **[UT-S06]** Test private methods indirectly through the public API only.
- **[UT-S07]** Use @Timeout(5) on tests that could run longer than expected to prevent CI hangs.
- **[UT-S08]** Use AssertJ fluent assertions (assertThat(...).isEqualTo(...)) when available.
- **[UT-S09]** Use @RepeatedTest for scenarios with non-deterministic behavior.
- **[UT-S10]** If the class under test uses shared mutable state (e.g., static fields), include a thread-safety test.
- **[UT-S11]** Prefer verify(mock, times(1)) over verify(mock) for explicit invocation count.
- **[UT-S12]** Use Mockito.lenient() only when strictly necessary; prefer strict stubbing.

---

## Execution Steps
1. Read the Class Inventory (5 classes) and identify all public methods per class
2. For each class, identify injected dependencies that need @Mock annotations
3. Create @Mock for each dependency and @InjectMocks for the class under test
4. For each public method, create a @Nested test class containing:
   a. Happy-path test with valid inputs
   b. Null-input tests for each nullable parameter
   c. Boundary tests for numeric parameters (0, negative, MAX_VALUE)
   d. Exception tests for each declared exception
5. Verify all void dependency interactions with Mockito.verify()
6. Ensure every test follows AAA pattern with @DisplayName
7. Add @ParameterizedTest where multiple input variations make sense
8. Output all 5 test files sequentially

---

## Prompt Template

You are a senior Java test engineer. Generate comprehensive JUnit5 unit tests with Mockito for EVERY class listed in the Class Inventory below.

## Scope

This prompt covers 5 Spring Boot class(es). You MUST generate one complete test file per class.

## Class Inventory

| Class | Package | Component Type | Dependencies | Method Count | Method Signatures |
|-------|---------|----------------|--------------|--------------|-------------------|
| OrderController | com.example.orderservice.controller | rest_controller | OrderService | 6 | public ResponseEntity<OrderResponse> createOrder(OrderRequest request); public ResponseEntity<OrderResponse> getOrder(Long orderId); public ResponseEntity<List<OrderResponse>> getAllOrders(String status, int page, int size); public ResponseEntity<OrderResponse> updateOrder(Long orderId, OrderRequest request); public ResponseEntity<Void> deleteOrder(Long orderId); public ResponseEntity<OrderResponse> cancelOrder(Long orderId) |
| GlobalExceptionHandler | com.example.orderservice.exception | exception_handler | None | 3 | public ResponseEntity<Map<String, Object>> handleNotFound(ResourceNotFoundException ex); public ResponseEntity<Map<String, Object>> handleConflict(IllegalStateException ex); public ResponseEntity<Map<String, Object>> handleGeneral(Exception ex) |
| OrderEventProducer | com.example.orderservice.messaging | component | KafkaTemplate<String, Object> | 4 | public void publishOrderCreated(Order order); public void publishOrderUpdated(Order order); public void publishOrderCancelled(Order order); public void publishOrderDeleted(Long orderId) |
| OrderRepository | com.example.orderservice.repository | repository | None | 5 |  List<Order> findByStatus(OrderStatus status);  List<Order> findByCustomerId(Long customerId);  List<Order> findOrdersBetweenDates(LocalDateTime startDate, LocalDateTime endDate);  boolean existsByIdAndCustomerId(Long orderId, Long customerId);  Optional<Order> findFirstByCustomerIdOrderByCreatedAtDesc(Long customerId) |
| OrderService | com.example.orderservice.service | service | OrderRepository, OrderMapper, OrderEventProducer | 7 | public OrderResponse createOrder(OrderRequest request); public OrderResponse getOrderById(Long id) throws ResourceNotFoundException; public List<OrderResponse> getAllOrders(String status, int page, int size); public OrderResponse updateOrder(Long id, OrderRequest request) throws ResourceNotFoundException; public void deleteOrder(Long id) throws ResourceNotFoundException; public OrderResponse cancelOrder(Long id) throws ResourceNotFoundException, IllegalStateException; public boolean isOrderOwnedByCustomer(Long orderId, Long customerId) |

## Requirements

### Mandatory (Hard Rules)
[HARD] [UT-H01] Use JUnit5 annotations only (@Test, @BeforeEach, @AfterEach, @DisplayName). Do NOT use JUnit4.
[HARD] [UT-H02] Use Mockito (@Mock, @InjectMocks, @ExtendWith(MockitoExtension.class)) for ALL injected dependencies.
[HARD] [UT-H03] Follow the Arrange-Act-Assert (AAA) pattern in every test method. Add // Arrange, // Act, // Assert comments.
[HARD] [UT-H04] Use @DisplayName with descriptive English sentences on every test.
[HARD] [UT-H05] Test class name MUST be {ClassName}Test, matching the source class exactly.
[HARD] [UT-H06] Each test must be independent. No shared mutable state between tests.
[HARD] [UT-H07] Verify void dependency calls using Mockito.verify().
[HARD] [UT-H08] Test naming convention: should_ExpectedBehavior_When_Condition().
[HARD] [UT-H09] Cover at minimum: happy path, null inputs (for nullable params), boundary values (for numeric params), and exception paths (for declared exceptions).
[HARD] [UT-H10] Use assertThrows() for exception testing. Never use try-catch to test exceptions.
[HARD] [UT-H11] Never use @SuppressWarnings to hide test warnings.
[HARD] [UT-H12] Do NOT use Thread.sleep() in unit tests. Use Awaitility for async testing if needed.
[HARD] [UT-H13] Assert with specific matchers (assertEquals, assertTrue, assertFalse). Avoid standalone assertNotNull unless specifically testing for non-null.
[HARD] [UT-H14] Each test should focus on one logical assertion (or use assertAll for closely related property assertions).
[HARD] [UT-H15] Do NOT initialize mocks manually (e.g., Mockito.mock()). Rely solely on @ExtendWith(MockitoExtension.class) + @Mock.
[HARD] [UT-H16] When the exact argument value is knowable, use it in stubbing. Avoid Mockito.any() unless the argument is genuinely irrelevant.
[HARD] [UT-H17] Generate one test file per source class listed in the Class Inventory below.
[HARD] [UT-H18] Every generated test file must be fully compilable without modification. Include all imports.

### Recommended (Soft Rules)
[SOFT] [UT-S01] Use @ParameterizedTest with @ValueSource or @MethodSource for methods accepting multiple valid input variations.
[SOFT] [UT-S02] Use ArgumentCaptor when verifying complex objects passed to mocks.
[SOFT] [UT-S03] Group tests using @Nested inner classes, one per method under test.
[SOFT] [UT-S04] Keep each test method under 20 lines for readability.
[SOFT] [UT-S05] Use factory methods or test data builders for complex test object construction.
[SOFT] [UT-S06] Test private methods indirectly through the public API only.
[SOFT] [UT-S07] Use @Timeout(5) on tests that could run longer than expected to prevent CI hangs.
[SOFT] [UT-S08] Use AssertJ fluent assertions (assertThat(...).isEqualTo(...)) when available.
[SOFT] [UT-S09] Use @RepeatedTest for scenarios with non-deterministic behavior.
[SOFT] [UT-S10] If the class under test uses shared mutable state (e.g., static fields), include a thread-safety test.
[SOFT] [UT-S11] Prefer verify(mock, times(1)) over verify(mock) for explicit invocation count.
[SOFT] [UT-S12] Use Mockito.lenient() only when strictly necessary; prefer strict stubbing.

## Generic Test File Structure

For EACH class in the inventory above, produce a test file following this structure:

```java
package {package};

import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.*;
import org.mockito.*;
import org.mockito.junit.jupiter.MockitoExtension;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("{ClassName} Unit Tests")
class {ClassName}Test {

    @Mock
    private DependencyType dependencyName;  // one @Mock per dependency listed

    @InjectMocks
    private {ClassName} {instanceName};

    @BeforeEach
    void setUp() {
        // Common setup if needed
    }

    @Nested
    @DisplayName("{methodName} tests")
    class MethodNameTests {

        @Test
        @DisplayName("should return expected result when valid input provided")
        void should_ReturnExpected_When_ValidInput() {
            // Arrange
            // Act
            // Assert
        }

        @Test
        @DisplayName("should throw exception when null input provided")
        void should_ThrowException_When_NullInput() {
            // Arrange
            // Act & Assert
            assertThrows(NullPointerException.class, () -> {
                // call method with null
            });
        }
    }
}
```

## Coverage Requirements Per Class

For each class in the inventory, generate:
  - 1 happy-path test per public method
  - 1 null-input test per nullable parameter (String, Integer, Long, Object, List, Map, etc.)
  - 1 boundary test per numeric parameter (test with 0, negative, and MAX_VALUE)
  - 1 exception test per declared exception
  - 1 void-method state verification test per void method (verify mock interactions)
  - 1 boolean true/false pair for boolean-returning methods

## Output

Produce ALL test files sequentially. Separate each file with a clear header comment:
```
// === File: {ClassName}Test.java ===
```

Generate all 5 test file(s) now.


---

*Generated by MD Agent Prompt Orchestrator v2.0*
