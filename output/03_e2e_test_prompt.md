# Prompt: Step 03/06 -- E2E TEST

---

## Chain Context

| Field | Value |
|-------|-------|
| **Invoked By** | `00_master_prompt.md` |
| **Step** | 03 of 06 |
| **Previous Step** | `02_..._prompt.md` |
| **Next Step** | `04_..._prompt.md` |

Once this step is complete, output: `[STEP 03 COMPLETE] -- [one-line summary]` and proceed to Step 04.

---

## Purpose
Generate end-to-end tests for orderservice

## Conditional Trigger
> Project has 1 controllers with 6 endpoints

## Target Classes
OrderController

---

## Hard Rules (Mandatory)
- **[E2E-H01]** Use @SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT).
- **[E2E-H02]** Use TestRestTemplate or WebTestClient for real HTTP calls (not MockMvc).
- **[E2E-H03]** Test complete user flows end-to-end, not isolated units.
- **[E2E-H04]** Include authentication setup if Spring Security is enabled.
- **[E2E-H05]** Test both success and failure paths for every flow.
- **[E2E-H06]** Use TestContainers for ALL external dependencies (database, message broker, cache).
- **[E2E-H07]** Include database state verification after each write operation, not just HTTP response checks.
- **[E2E-H08]** Test idempotency: calling the same create/update request twice must be safe or correctly rejected.
- **[E2E-H09]** Use unique test data per test run (e.g., UUID-based) to prevent shared-state flakiness.
- **[E2E-H10]** Every generated test file must be fully compilable without modification.

## Soft Rules (Recommended)
- **[E2E-S01]** Define test scenarios as user stories (Given/When/Then).
- **[E2E-S02]** Test CRUD lifecycle: Create -> Read -> Update -> Delete.
- **[E2E-S03]** Include response time assertions (response time < X ms) for performance-critical endpoints.
- **[E2E-S04]** Test pagination and large result sets if applicable.
- **[E2E-S05]** Include cleanup/teardown that runs regardless of test outcome (use @AfterAll).
- **[E2E-S06]** Test concurrent access scenarios for shared resources.

---

## Execution Steps
1. Map all endpoints into user-facing scenarios
2. Define happy-path E2E flows (CRUD lifecycle)
3. Define error scenarios (4xx, 5xx responses)
4. Set up full application context with TestContainers
5. Implement authentication if security is present
6. Execute scenarios using TestRestTemplate
7. Assert on HTTP responses and database state

---

## Prompt Template

You are a senior QA engineer. Generate comprehensive end-to-end tests for the following Spring Boot microservice.

## Project Overview
Project: orderservice
Total Classes: 8
Controllers: 1
Services: 1
Repositories: 1
Database: Yes (JPA)
Messaging: Kafka
Security: No

Endpoints:
  - POST /api/v1/orders -> OrderController.createOrder
  - GET /api/v1/orders/orderId -> OrderController.getOrder
  - GET /api/v1/orders/allOrders -> OrderController.getAllOrders
  - PUT /api/v1/orders/orderId -> OrderController.updateOrder
  - DELETE /api/v1/orders/orderId -> OrderController.deleteOrder
  - PATCH /api/v1/orders/orderId/cancel -> OrderController.cancelOrder


## Requirements

### Mandatory (Hard Rules)
[HARD] [E2E-H01] Use @SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT).
[HARD] [E2E-H02] Use TestRestTemplate or WebTestClient for real HTTP calls (not MockMvc).
[HARD] [E2E-H03] Test complete user flows end-to-end, not isolated units.
[HARD] [E2E-H04] Include authentication setup if Spring Security is enabled.
[HARD] [E2E-H05] Test both success and failure paths for every flow.
[HARD] [E2E-H06] Use TestContainers for ALL external dependencies (database, message broker, cache).
[HARD] [E2E-H07] Include database state verification after each write operation, not just HTTP response checks.
[HARD] [E2E-H08] Test idempotency: calling the same create/update request twice must be safe or correctly rejected.
[HARD] [E2E-H09] Use unique test data per test run (e.g., UUID-based) to prevent shared-state flakiness.
[HARD] [E2E-H10] Every generated test file must be fully compilable without modification.

### Recommended (Soft Rules)
[SOFT] [E2E-S01] Define test scenarios as user stories (Given/When/Then).
[SOFT] [E2E-S02] Test CRUD lifecycle: Create -> Read -> Update -> Delete.
[SOFT] [E2E-S03] Include response time assertions (response time < X ms) for performance-critical endpoints.
[SOFT] [E2E-S04] Test pagination and large result sets if applicable.
[SOFT] [E2E-S05] Include cleanup/teardown that runs regardless of test outcome (use @AfterAll).
[SOFT] [E2E-S06] Test concurrent access scenarios for shared resources.

## Test Scenarios to Cover
1. Full CRUD lifecycle for each main resource
2. Error handling (invalid inputs, not found, unauthorized)
3. Data validation flows
4. Cross-service interactions (if applicable)

6. Message publication and consumption flows

## Test Structure Template

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@DisplayName("orderservice End-to-End Tests")
class orderserviceE2ETest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
    }

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    @Order(1)
    @DisplayName("should create resource successfully")
    void should_CreateResource_When_ValidRequest() {
        // Given
        // When
        // Then
    }
}
```

## Output Format
- Produce a single Java test file: `orderserviceE2ETest.java`
- Use Given/When/Then comments for scenario documentation
- Include test data setup and teardown

Generate the complete E2E test file now.


---

*Generated by MD Agent Prompt Orchestrator v2.0*
