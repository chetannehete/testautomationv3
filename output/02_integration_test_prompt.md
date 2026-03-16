# Prompt: Step 02/06 -- INTEGRATION TEST

---

## Chain Context

| Field | Value |
|-------|-------|
| **Invoked By** | `00_master_prompt.md` |
| **Step** | 02 of 06 |
| **Previous Step** | `01_..._prompt.md` |
| **Next Step** | `03_..._prompt.md` |

Once this step is complete, output: `[STEP 02 COMPLETE] -- [one-line summary]` and proceed to Step 03.

---

## Purpose
Generate Spring Boot integration tests for 2 component(s)

## Conditional Trigger
> 2 component(s) require integration testing

## Target Classes
OrderController, OrderRepository

---

## Hard Rules (Mandatory)
- **[IT-H01]** Use @SpringBootTest for full context tests. Use @WebMvcTest for controller slice tests. Use @DataJpaTest for repository slice tests.
- **[IT-H02]** Use @AutoConfigureMockMvc and MockMvc for REST API tests.
- **[IT-H03]** Use @DataJpaTest with @AutoConfigureTestDatabase for repository tests.
- **[IT-H04]** Test class name MUST end with 'IT' (e.g., UserControllerIT, OrderRepositoryIT).
- **[IT-H05]** Use @Transactional and @Rollback for DB tests to prevent side effects across tests.
- **[IT-H06]** Use TestContainers (@Testcontainers, @Container) for all external dependencies (DB, Kafka, Redis) when applicable.
- **[IT-H07]** For API tests: assert HTTP status code, response body structure, and Content-Type header.
- **[IT-H08]** Use @Sql or explicit test data insertion methods for database seeding.
- **[IT-H09]** Apply @Timeout on every integration test to prevent CI pipeline hangs.
- **[IT-H10]** Use @MockBean only for external service dependencies. Never mock the class under test.
- **[IT-H11]** Validate response Content-Type is 'application/json' for JSON API endpoints.
- **[IT-H12]** Test error responses return a proper error JSON structure (status, message, timestamp).
- **[IT-H13]** Generate one test file per source class listed in the Component Inventory.
- **[IT-H14]** Every generated test file must be fully compilable without modification.

## Soft Rules (Recommended)
- **[IT-S01]** Use @TestPropertySource to override application.properties for test isolation.
- **[IT-S02]** Use @ActiveProfiles('test') for test-specific Spring configuration.
- **[IT-S03]** Use @Order on tests that form a natural sequence (e.g., create before read).
- **[IT-S04]** Use @DynamicPropertySource for TestContainers dynamic port binding.
- **[IT-S05]** Add @Tag('integration') for CI/CD pipeline filtering.
- **[IT-S06]** Use @Testcontainers annotation with @Container fields for cleaner lifecycle management.
- **[IT-S07]** Use @AutoConfigureJsonTesters for type-safe response body assertions.
- **[IT-S08]** Include a concurrent request test to validate thread-safety of controllers.
- **[IT-S09]** Use WireMock (@WireMockTest) for stubbing external HTTP dependencies.

---

## Execution Steps
1. Read the Component Inventory (2 components)
2. Identify the test slice annotation for each component type
3. Set up TestContainers or embedded resources as needed
4. For API controllers: test every endpoint with MockMvc
5. For repositories: test CRUD operations and custom queries
6. For messaging: test message production and consumption
7. Test error handling and edge cases for each component
8. Output all 2 integration test files sequentially

---

## Prompt Template

You are a senior Java test engineer. Generate comprehensive Spring Boot integration tests for ALL components listed in the Component Inventory below.

## Scope

This prompt covers 2 component(s) requiring integration tests.

### API Controllers

| Class | Package | Base Path | Endpoints |
|-------|---------|-----------|-----------|
| OrderController | com.example.orderservice.controller | /api/v1/orders | POST /api/v1/orders -> createOrder; GET /api/v1/orders/orderId -> getOrder; GET /api/v1/orders/allOrders -> getAllOrders; PUT /api/v1/orders/orderId -> updateOrder; DELETE /api/v1/orders/orderId -> deleteOrder; PATCH /api/v1/orders/orderId/cancel -> cancelOrder |

### Repositories

| Class | Package | Methods |
|-------|---------|---------|
| OrderRepository | com.example.orderservice.repository | List<Order> findByStatus(OrderStatus); List<Order> findByCustomerId(Long); List<Order> findOrdersBetweenDates(LocalDateTime, LocalDateTime); boolean existsByIdAndCustomerId(Long, Long); Optional<Order> findFirstByCustomerIdOrderByCreatedAtDesc(Long) |

Database Types: JPA


## Requirements

### Mandatory (Hard Rules)
[HARD] [IT-H01] Use @SpringBootTest for full context tests. Use @WebMvcTest for controller slice tests. Use @DataJpaTest for repository slice tests.
[HARD] [IT-H02] Use @AutoConfigureMockMvc and MockMvc for REST API tests.
[HARD] [IT-H03] Use @DataJpaTest with @AutoConfigureTestDatabase for repository tests.
[HARD] [IT-H04] Test class name MUST end with 'IT' (e.g., UserControllerIT, OrderRepositoryIT).
[HARD] [IT-H05] Use @Transactional and @Rollback for DB tests to prevent side effects across tests.
[HARD] [IT-H06] Use TestContainers (@Testcontainers, @Container) for all external dependencies (DB, Kafka, Redis) when applicable.
[HARD] [IT-H07] For API tests: assert HTTP status code, response body structure, and Content-Type header.
[HARD] [IT-H08] Use @Sql or explicit test data insertion methods for database seeding.
[HARD] [IT-H09] Apply @Timeout on every integration test to prevent CI pipeline hangs.
[HARD] [IT-H10] Use @MockBean only for external service dependencies. Never mock the class under test.
[HARD] [IT-H11] Validate response Content-Type is 'application/json' for JSON API endpoints.
[HARD] [IT-H12] Test error responses return a proper error JSON structure (status, message, timestamp).
[HARD] [IT-H13] Generate one test file per source class listed in the Component Inventory.
[HARD] [IT-H14] Every generated test file must be fully compilable without modification.

### Recommended (Soft Rules)
[SOFT] [IT-S01] Use @TestPropertySource to override application.properties for test isolation.
[SOFT] [IT-S02] Use @ActiveProfiles('test') for test-specific Spring configuration.
[SOFT] [IT-S03] Use @Order on tests that form a natural sequence (e.g., create before read).
[SOFT] [IT-S04] Use @DynamicPropertySource for TestContainers dynamic port binding.
[SOFT] [IT-S05] Add @Tag('integration') for CI/CD pipeline filtering.
[SOFT] [IT-S06] Use @Testcontainers annotation with @Container fields for cleaner lifecycle management.
[SOFT] [IT-S07] Use @AutoConfigureJsonTesters for type-safe response body assertions.
[SOFT] [IT-S08] Include a concurrent request test to validate thread-safety of controllers.
[SOFT] [IT-S09] Use WireMock (@WireMockTest) for stubbing external HTTP dependencies.

## Test Structure Templates

### For API Controllers (use @WebMvcTest or @SpringBootTest)

```java
@WebMvcTest({ControllerClass}.class)
@DisplayName("{ControllerClass} Integration Tests")
class {ControllerClass}IT {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ServiceDependency serviceDependency;

    @Test
    @DisplayName("GET /path should return 200 with expected body")
    void should_Return200_When_ValidGetRequest() throws Exception {
        // Arrange
        when(serviceDependency.findAll()).thenReturn(List.of(...));

        // Act & Assert
        mockMvc.perform(get("/path")
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$[0].field").value("expected"));
    }
}
```

### For Repositories (use @DataJpaTest)

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
@DisplayName("{RepositoryClass} Integration Tests")
class {RepositoryClass}IT {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
    }

    @Autowired
    private {RepositoryClass} repository;

    @Test
    @DisplayName("should save and retrieve entity")
    void should_SaveAndRetrieve_When_ValidEntity() {
        // Arrange
        // Act
        // Assert
    }
}
```

### For Messaging (use @SpringBootTest with EmbeddedKafka or TestContainers)

```java
@SpringBootTest
@EmbeddedKafka(partitions = 1, topics = {"topic-name"})
@DisplayName("{MessagingClass} Integration Tests")
class {MessagingClass}IT {

    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    @Test
    @DisplayName("should consume message successfully")
    void should_ConsumeMessage_When_ValidMessagePublished() {
        // Arrange
        // Act
        // Assert
    }
}
```

## Coverage Requirements

For each component in the inventory:
  - API Controllers: test every endpoint (success + error responses), validate status codes, headers, and body
  - Repositories: test CRUD operations, custom queries, edge cases (empty result, duplicate key)
  - Messaging: test message consumption, production, error handling, and deserialization

## Output

Produce ALL integration test files sequentially. Separate each with:
```
// === File: {ClassName}IT.java ===
```

Generate all 2 integration test file(s) now.


---

*Generated by MD Agent Prompt Orchestrator v2.0*
