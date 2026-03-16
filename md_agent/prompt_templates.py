"""
Prompt Templates for the Nested Prompt Generation System.

DESIGN PRINCIPLE: Each builder produces exactly ONE GenericPrompt per prompt type.
The prompt is REUSABLE across all classes of that category.  It contains:
  - A generic template body with class-agnostic rules and structure
  - A class inventory section listing every relevant class discovered
  - Hard Rules (mandatory LLM constraints)
  - Soft Rules (recommended best practices)
  - Step-by-step execution plan

This means the orchestrator outputs exactly ONE file per prompt type
(e.g., one unit_test_prompt.md, one integration_test_prompt.md, etc.)
instead of one file per class.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from md_agent.models import (
    ClassInfo,
    CodebaseAnalysis,
    ComponentType,
    EndpointInfo,
    GeneratedPrompt,
    PromptRule,
    PromptType,
    SpringComponent,
)


# ======================================================================
#  UNIT TEST PROMPT  (one prompt for ALL testable components)
# ======================================================================

def build_unit_test_prompt(
    components: List[SpringComponent],
    analysis: CodebaseAnalysis,
) -> GeneratedPrompt:
    """
    Build a SINGLE generic prompt for generating JUnit5 + Mockito unit
    tests that covers ALL testable Spring Boot classes.

    The prompt contains a class inventory so the LLM knows which
    classes to generate tests for, but the rules and template are
    universal and class-agnostic.
    """

    # -- Class inventory table ------------------------------------------
    inventory_rows = []
    all_target_names: List[str] = []
    for comp in components:
        cls = comp.class_info
        all_target_names.append(cls.name)
        dep_list = ", ".join(d.type for d in comp.dependencies) if comp.dependencies else "None"
        method_sigs = []
        for m in cls.methods:
            params = ", ".join(f"{p.type} {p.name}" for p in m.parameters)
            exc = f" throws {', '.join(m.exceptions)}" if m.exceptions else ""
            method_sigs.append(f"{' '.join(m.modifiers)} {m.return_type} {m.name}({params}){exc}")
        methods_str = "; ".join(method_sigs) if method_sigs else "None"
        inventory_rows.append(
            f"| {cls.name} | {cls.package or 'default'} | "
            f"{comp.component_type.value} | {dep_list} | "
            f"{len(cls.methods)} | {methods_str} |"
        )

    inventory_table = "\n".join(inventory_rows)
    total_classes = len(components)

    # -- Hard Rules (class-agnostic) ------------------------------------
    hard_rules = [
        PromptRule("UT-H01", "Use JUnit5 annotations only (@Test, @BeforeEach, @AfterEach, @DisplayName). Do NOT use JUnit4.", True),
        PromptRule("UT-H02", "Use Mockito (@Mock, @InjectMocks, @ExtendWith(MockitoExtension.class)) for ALL injected dependencies.", True),
        PromptRule("UT-H03", "Follow the Arrange-Act-Assert (AAA) pattern in every test method. Add // Arrange, // Act, // Assert comments.", True),
        PromptRule("UT-H04", "Use @DisplayName with descriptive English sentences on every test.", True),
        PromptRule("UT-H05", "Test class name MUST be {ClassName}Test, matching the source class exactly.", True),
        PromptRule("UT-H06", "Each test must be independent. No shared mutable state between tests.", True),
        PromptRule("UT-H07", "Verify void dependency calls using Mockito.verify().", True),
        PromptRule("UT-H08", "Test naming convention: should_ExpectedBehavior_When_Condition().", True),
        PromptRule("UT-H09", "Cover at minimum: happy path, null inputs (for nullable params), boundary values (for numeric params), and exception paths (for declared exceptions).", True),
        PromptRule("UT-H10", "Use assertThrows() for exception testing. Never use try-catch to test exceptions.", True),
        PromptRule("UT-H11", "Never use @SuppressWarnings to hide test warnings.", True),
        PromptRule("UT-H12", "Do NOT use Thread.sleep() in unit tests. Use Awaitility for async testing if needed.", True),
        PromptRule("UT-H13", "Assert with specific matchers (assertEquals, assertTrue, assertFalse). Avoid standalone assertNotNull unless specifically testing for non-null.", True),
        PromptRule("UT-H14", "Each test should focus on one logical assertion (or use assertAll for closely related property assertions).", True),
        PromptRule("UT-H15", "Do NOT initialize mocks manually (e.g., Mockito.mock()). Rely solely on @ExtendWith(MockitoExtension.class) + @Mock.", True),
        PromptRule("UT-H16", "When the exact argument value is knowable, use it in stubbing. Avoid Mockito.any() unless the argument is genuinely irrelevant.", True),
        PromptRule("UT-H17", "Generate one test file per source class listed in the Class Inventory below.", True),
        PromptRule("UT-H18", "Every generated test file must be fully compilable without modification. Include all imports.", True),
    ]

    # -- Soft Rules (class-agnostic) ------------------------------------
    soft_rules = [
        PromptRule("UT-S01", "Use @ParameterizedTest with @ValueSource or @MethodSource for methods accepting multiple valid input variations.", False),
        PromptRule("UT-S02", "Use ArgumentCaptor when verifying complex objects passed to mocks.", False),
        PromptRule("UT-S03", "Group tests using @Nested inner classes, one per method under test.", False),
        PromptRule("UT-S04", "Keep each test method under 20 lines for readability.", False),
        PromptRule("UT-S05", "Use factory methods or test data builders for complex test object construction.", False),
        PromptRule("UT-S06", "Test private methods indirectly through the public API only.", False),
        PromptRule("UT-S07", "Use @Timeout(5) on tests that could run longer than expected to prevent CI hangs.", False),
        PromptRule("UT-S08", "Use AssertJ fluent assertions (assertThat(...).isEqualTo(...)) when available.", False),
        PromptRule("UT-S09", "Use @RepeatedTest for scenarios with non-deterministic behavior.", False),
        PromptRule("UT-S10", "If the class under test uses shared mutable state (e.g., static fields), include a thread-safety test.", False),
        PromptRule("UT-S11", "Prefer verify(mock, times(1)) over verify(mock) for explicit invocation count.", False),
        PromptRule("UT-S12", "Use Mockito.lenient() only when strictly necessary; prefer strict stubbing.", False),
    ]

    # -- Template body (fully generic) ----------------------------------
    template = f"""You are a senior Java test engineer. Generate comprehensive JUnit5 unit tests with Mockito for EVERY class listed in the Class Inventory below.

## Scope

This prompt covers {total_classes} Spring Boot class(es). You MUST generate one complete test file per class.

## Class Inventory

| Class | Package | Component Type | Dependencies | Method Count | Method Signatures |
|-------|---------|----------------|--------------|--------------|-------------------|
{inventory_table}

## Requirements

### Mandatory (Hard Rules)
{_format_rules(hard_rules)}

### Recommended (Soft Rules)
{_format_rules(soft_rules)}

## Generic Test File Structure

For EACH class in the inventory above, produce a test file following this structure:

```java
package {{package}};

import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.*;
import org.mockito.*;
import org.mockito.junit.jupiter.MockitoExtension;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@DisplayName("{{ClassName}} Unit Tests")
class {{ClassName}}Test {{

    @Mock
    private DependencyType dependencyName;  // one @Mock per dependency listed

    @InjectMocks
    private {{ClassName}} {{instanceName}};

    @BeforeEach
    void setUp() {{
        // Common setup if needed
    }}

    @Nested
    @DisplayName("{{methodName}} tests")
    class MethodNameTests {{

        @Test
        @DisplayName("should return expected result when valid input provided")
        void should_ReturnExpected_When_ValidInput() {{
            // Arrange
            // Act
            // Assert
        }}

        @Test
        @DisplayName("should throw exception when null input provided")
        void should_ThrowException_When_NullInput() {{
            // Arrange
            // Act & Assert
            assertThrows(NullPointerException.class, () -> {{
                // call method with null
            }});
        }}
    }}
}}
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
// === File: {{ClassName}}Test.java ===
```

Generate all {total_classes} test file(s) now.
"""

    steps = [
        f"1. Read the Class Inventory ({total_classes} classes) and identify all public methods per class",
        "2. For each class, identify injected dependencies that need @Mock annotations",
        "3. Create @Mock for each dependency and @InjectMocks for the class under test",
        "4. For each public method, create a @Nested test class containing:",
        "   a. Happy-path test with valid inputs",
        "   b. Null-input tests for each nullable parameter",
        "   c. Boundary tests for numeric parameters (0, negative, MAX_VALUE)",
        "   d. Exception tests for each declared exception",
        "5. Verify all void dependency interactions with Mockito.verify()",
        "6. Ensure every test follows AAA pattern with @DisplayName",
        "7. Add @ParameterizedTest where multiple input variations make sense",
        f"8. Output all {total_classes} test files sequentially",
    ]

    trigger = f"{total_classes} testable Spring Boot class(es) detected"

    return GeneratedPrompt(
        prompt_type=PromptType.UNIT_TEST,
        purpose=f"Generate JUnit5 + Mockito unit tests for {total_classes} class(es)",
        hard_rules=hard_rules,
        soft_rules=soft_rules,
        context=inventory_table,
        template_body=template,
        target_classes=all_target_names,
        conditional_trigger=trigger,
        execution_steps=steps,
    )


# ======================================================================
#  INTEGRATION TEST PROMPT  (one prompt covering ALL integration targets)
# ======================================================================

def build_integration_test_prompt(
    components: List[SpringComponent],
    analysis: CodebaseAnalysis,
) -> GeneratedPrompt:
    """
    Build a SINGLE generic prompt for generating Spring Boot integration
    tests covering ALL controllers, repositories, and messaging components.
    """

    features = analysis.features

    # -- Categorize components ------------------------------------------
    api_components = [c for c in components if c.component_type in (
        ComponentType.REST_CONTROLLER, ComponentType.CONTROLLER)]
    db_components = [c for c in components if c.component_type == ComponentType.REPOSITORY]
    msg_components = [c for c in components if c.component_type in (
        ComponentType.MESSAGING_LISTENER, ComponentType.MESSAGING_PRODUCER)]

    all_target_names: List[str] = []

    # -- API section ----------------------------------------------------
    api_section = ""
    if api_components:
        api_rows = []
        for comp in api_components:
            cls = comp.class_info
            all_target_names.append(cls.name)
            endpoints_str = "; ".join(
                f"{ep.http_method} {ep.path} -> {ep.method_name}" for ep in comp.endpoints
            ) if comp.endpoints else "None"
            api_rows.append(f"| {cls.name} | {cls.package or 'default'} | {comp.base_path or '/'} | {endpoints_str} |")
        api_table = "\n".join(api_rows)
        api_section = f"""
### API Controllers

| Class | Package | Base Path | Endpoints |
|-------|---------|-----------|-----------|
{api_table}
"""

    # -- DB section -----------------------------------------------------
    db_section = ""
    if db_components:
        db_rows = []
        for comp in db_components:
            cls = comp.class_info
            all_target_names.append(cls.name)
            methods_str = "; ".join(
                f"{m.return_type} {m.name}({', '.join(p.type for p in m.parameters)})"
                for m in cls.methods
            ) if cls.methods else "Inherited CRUD"
            db_rows.append(f"| {cls.name} | {cls.package or 'default'} | {methods_str} |")
        db_table = "\n".join(db_rows)
        db_section = f"""
### Repositories

| Class | Package | Methods |
|-------|---------|---------|
{db_table}

Database Types: {', '.join(features.database_types) if features.database_types else 'JPA/JDBC'}
"""

    # -- Messaging section ----------------------------------------------
    msg_section = ""
    if msg_components:
        msg_rows = []
        for comp in msg_components:
            cls = comp.class_info
            all_target_names.append(cls.name)
            broker = "Kafka" if features.has_kafka else "RabbitMQ" if features.has_rabbitmq else "Unknown"
            msg_rows.append(f"| {cls.name} | {comp.component_type.value} | {broker} | {len(cls.methods)} |")
        msg_table = "\n".join(msg_rows)
        msg_section = f"""
### Messaging Components

| Class | Type | Broker | Method Count |
|-------|------|--------|--------------|
{msg_table}
"""

    total_targets = len(all_target_names)

    # -- Hard Rules (class-agnostic) ------------------------------------
    hard_rules = [
        PromptRule("IT-H01", "Use @SpringBootTest for full context tests. Use @WebMvcTest for controller slice tests. Use @DataJpaTest for repository slice tests.", True),
        PromptRule("IT-H02", "Use @AutoConfigureMockMvc and MockMvc for REST API tests.", True),
        PromptRule("IT-H03", "Use @DataJpaTest with @AutoConfigureTestDatabase for repository tests.", True),
        PromptRule("IT-H04", "Test class name MUST end with 'IT' (e.g., UserControllerIT, OrderRepositoryIT).", True),
        PromptRule("IT-H05", "Use @Transactional and @Rollback for DB tests to prevent side effects across tests.", True),
        PromptRule("IT-H06", "Use TestContainers (@Testcontainers, @Container) for all external dependencies (DB, Kafka, Redis) when applicable.", True),
        PromptRule("IT-H07", "For API tests: assert HTTP status code, response body structure, and Content-Type header.", True),
        PromptRule("IT-H08", "Use @Sql or explicit test data insertion methods for database seeding.", True),
        PromptRule("IT-H09", "Apply @Timeout on every integration test to prevent CI pipeline hangs.", True),
        PromptRule("IT-H10", "Use @MockBean only for external service dependencies. Never mock the class under test.", True),
        PromptRule("IT-H11", "Validate response Content-Type is 'application/json' for JSON API endpoints.", True),
        PromptRule("IT-H12", "Test error responses return a proper error JSON structure (status, message, timestamp).", True),
        PromptRule("IT-H13", "Generate one test file per source class listed in the Component Inventory.", True),
        PromptRule("IT-H14", "Every generated test file must be fully compilable without modification.", True),
    ]

    # -- Soft Rules (class-agnostic) ------------------------------------
    soft_rules = [
        PromptRule("IT-S01", "Use @TestPropertySource to override application.properties for test isolation.", False),
        PromptRule("IT-S02", "Use @ActiveProfiles('test') for test-specific Spring configuration.", False),
        PromptRule("IT-S03", "Use @Order on tests that form a natural sequence (e.g., create before read).", False),
        PromptRule("IT-S04", "Use @DynamicPropertySource for TestContainers dynamic port binding.", False),
        PromptRule("IT-S05", "Add @Tag('integration') for CI/CD pipeline filtering.", False),
        PromptRule("IT-S06", "Use @Testcontainers annotation with @Container fields for cleaner lifecycle management.", False),
        PromptRule("IT-S07", "Use @AutoConfigureJsonTesters for type-safe response body assertions.", False),
        PromptRule("IT-S08", "Include a concurrent request test to validate thread-safety of controllers.", False),
        PromptRule("IT-S09", "Use WireMock (@WireMockTest) for stubbing external HTTP dependencies.", False),
    ]

    # -- Template body --------------------------------------------------
    template = f"""You are a senior Java test engineer. Generate comprehensive Spring Boot integration tests for ALL components listed in the Component Inventory below.

## Scope

This prompt covers {total_targets} component(s) requiring integration tests.
{api_section}{db_section}{msg_section}

## Requirements

### Mandatory (Hard Rules)
{_format_rules(hard_rules)}

### Recommended (Soft Rules)
{_format_rules(soft_rules)}

## Test Structure Templates

### For API Controllers (use @WebMvcTest or @SpringBootTest)

```java
@WebMvcTest({{ControllerClass}}.class)
@DisplayName("{{ControllerClass}} Integration Tests")
class {{ControllerClass}}IT {{

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private ServiceDependency serviceDependency;

    @Test
    @DisplayName("GET /path should return 200 with expected body")
    void should_Return200_When_ValidGetRequest() throws Exception {{
        // Arrange
        when(serviceDependency.findAll()).thenReturn(List.of(...));

        // Act & Assert
        mockMvc.perform(get("/path")
                .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$[0].field").value("expected"));
    }}
}}
```

### For Repositories (use @DataJpaTest)

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
@DisplayName("{{RepositoryClass}} Integration Tests")
class {{RepositoryClass}}IT {{

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {{
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
    }}

    @Autowired
    private {{RepositoryClass}} repository;

    @Test
    @DisplayName("should save and retrieve entity")
    void should_SaveAndRetrieve_When_ValidEntity() {{
        // Arrange
        // Act
        // Assert
    }}
}}
```

### For Messaging (use @SpringBootTest with EmbeddedKafka or TestContainers)

```java
@SpringBootTest
@EmbeddedKafka(partitions = 1, topics = {{"topic-name"}})
@DisplayName("{{MessagingClass}} Integration Tests")
class {{MessagingClass}}IT {{

    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    @Test
    @DisplayName("should consume message successfully")
    void should_ConsumeMessage_When_ValidMessagePublished() {{
        // Arrange
        // Act
        // Assert
    }}
}}
```

## Coverage Requirements

For each component in the inventory:
  - API Controllers: test every endpoint (success + error responses), validate status codes, headers, and body
  - Repositories: test CRUD operations, custom queries, edge cases (empty result, duplicate key)
  - Messaging: test message consumption, production, error handling, and deserialization

## Output

Produce ALL integration test files sequentially. Separate each with:
```
// === File: {{ClassName}}IT.java ===
```

Generate all {total_targets} integration test file(s) now.
"""

    steps = [
        f"1. Read the Component Inventory ({total_targets} components)",
        "2. Identify the test slice annotation for each component type",
        "3. Set up TestContainers or embedded resources as needed",
        "4. For API controllers: test every endpoint with MockMvc",
        "5. For repositories: test CRUD operations and custom queries",
        "6. For messaging: test message production and consumption",
        "7. Test error handling and edge cases for each component",
        f"8. Output all {total_targets} integration test files sequentially",
    ]

    return GeneratedPrompt(
        prompt_type=PromptType.INTEGRATION_TEST,
        purpose=f"Generate Spring Boot integration tests for {total_targets} component(s)",
        hard_rules=hard_rules,
        soft_rules=soft_rules,
        context=f"API: {len(api_components)}, DB: {len(db_components)}, Messaging: {len(msg_components)}",
        template_body=template,
        target_classes=all_target_names,
        conditional_trigger=f"{total_targets} component(s) require integration testing",
        execution_steps=steps,
    )


# ======================================================================
#  E2E TEST PROMPT
# ======================================================================

def build_e2e_test_prompt(
    analysis: CodebaseAnalysis,
) -> GeneratedPrompt:
    """Build a single prompt for generating end-to-end test scenarios."""

    features = analysis.features
    controllers = [c for c in analysis.components if c.component_type in (
        ComponentType.REST_CONTROLLER, ComponentType.CONTROLLER
    )]
    all_endpoints = []
    for c in controllers:
        for ep in c.endpoints:
            all_endpoints.append(f"{ep.http_method} {ep.path} -> {c.class_info.name}.{ep.method_name}")

    endpoint_list = "\n".join(f"  - {e}" for e in all_endpoints) if all_endpoints else "  (no endpoints detected)"

    context = f"""Project: {analysis.project_name}
Total Classes: {features.total_classes}
Controllers: {features.controller_count}
Services: {features.service_count}
Repositories: {features.repository_count}
Database: {'Yes (' + ', '.join(features.database_types) + ')' if features.has_database else 'No'}
Messaging: {'Kafka' if features.has_kafka else 'RabbitMQ' if features.has_rabbitmq else 'No'}
Security: {'Yes' if features.has_security else 'No'}

Endpoints:
{endpoint_list}
"""

    hard_rules = [
        PromptRule("E2E-H01", "Use @SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT).", True),
        PromptRule("E2E-H02", "Use TestRestTemplate or WebTestClient for real HTTP calls (not MockMvc).", True),
        PromptRule("E2E-H03", "Test complete user flows end-to-end, not isolated units.", True),
        PromptRule("E2E-H04", "Include authentication setup if Spring Security is enabled.", True),
        PromptRule("E2E-H05", "Test both success and failure paths for every flow.", True),
        PromptRule("E2E-H06", "Use TestContainers for ALL external dependencies (database, message broker, cache).", True),
        PromptRule("E2E-H07", "Include database state verification after each write operation, not just HTTP response checks.", True),
        PromptRule("E2E-H08", "Test idempotency: calling the same create/update request twice must be safe or correctly rejected.", True),
        PromptRule("E2E-H09", "Use unique test data per test run (e.g., UUID-based) to prevent shared-state flakiness.", True),
        PromptRule("E2E-H10", "Every generated test file must be fully compilable without modification.", True),
    ]

    soft_rules = [
        PromptRule("E2E-S01", "Define test scenarios as user stories (Given/When/Then).", False),
        PromptRule("E2E-S02", "Test CRUD lifecycle: Create -> Read -> Update -> Delete.", False),
        PromptRule("E2E-S03", "Include response time assertions (response time < X ms) for performance-critical endpoints.", False),
        PromptRule("E2E-S04", "Test pagination and large result sets if applicable.", False),
        PromptRule("E2E-S05", "Include cleanup/teardown that runs regardless of test outcome (use @AfterAll).", False),
        PromptRule("E2E-S06", "Test concurrent access scenarios for shared resources.", False),
    ]

    template = f"""You are a senior QA engineer. Generate comprehensive end-to-end tests for the following Spring Boot microservice.

## Project Overview
{context}

## Requirements

### Mandatory (Hard Rules)
{_format_rules(hard_rules)}

### Recommended (Soft Rules)
{_format_rules(soft_rules)}

## Test Scenarios to Cover
1. Full CRUD lifecycle for each main resource
2. Error handling (invalid inputs, not found, unauthorized)
3. Data validation flows
4. Cross-service interactions (if applicable)
{'5. Authentication and authorization flows' if features.has_security else ''}
{'6. Message publication and consumption flows' if features.has_messaging else ''}

## Test Structure Template

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@DisplayName("{analysis.project_name} End-to-End Tests")
class {analysis.project_name}E2ETest {{

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {{
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
    }}

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    @Order(1)
    @DisplayName("should create resource successfully")
    void should_CreateResource_When_ValidRequest() {{
        // Given
        // When
        // Then
    }}
}}
```

## Output Format
- Produce a single Java test file: `{analysis.project_name}E2ETest.java`
- Use Given/When/Then comments for scenario documentation
- Include test data setup and teardown

Generate the complete E2E test file now.
"""

    steps = [
        "1. Map all endpoints into user-facing scenarios",
        "2. Define happy-path E2E flows (CRUD lifecycle)",
        "3. Define error scenarios (4xx, 5xx responses)",
        "4. Set up full application context with TestContainers",
        "5. Implement authentication if security is present",
        "6. Execute scenarios using TestRestTemplate",
        "7. Assert on HTTP responses and database state",
    ]

    return GeneratedPrompt(
        prompt_type=PromptType.E2E_TEST,
        purpose=f"Generate end-to-end tests for {analysis.project_name}",
        hard_rules=hard_rules,
        soft_rules=soft_rules,
        context=context,
        template_body=template,
        target_classes=[c.class_info.name for c in controllers],
        conditional_trigger=f"Project has {features.controller_count} controllers with {features.total_endpoints} endpoints",
        execution_steps=steps,
    )


# ======================================================================
#  DOCUMENTATION PROMPT
# ======================================================================

def build_documentation_prompt(
    analysis: CodebaseAnalysis,
) -> GeneratedPrompt:
    """Build a single prompt for generating technical Markdown documentation."""

    features = analysis.features

    # Build component inventory
    component_summary = []
    for comp in analysis.components:
        cls = comp.class_info
        ep_count = len(comp.endpoints)
        dep_count = len(comp.dependencies)
        line = f"  - [{comp.component_type.value}] {cls.name}"
        if ep_count:
            line += f" ({ep_count} endpoints)"
        if dep_count:
            line += f" ({dep_count} dependencies)"
        component_summary.append(line)

    context = f"""Project: {analysis.project_name}
Total Classes: {features.total_classes}
Controllers: {features.controller_count}
Services: {features.service_count}
Repositories: {features.repository_count}
Entities: {features.entity_count}
Packages: {', '.join(features.packages[:10])}

Feature Flags:
  Database: {'Yes (' + ', '.join(features.database_types) + ')' if features.has_database else 'No'}
  REST API: {'Yes' if features.has_rest_controllers else 'No'}
  Messaging: {'Kafka' if features.has_kafka else 'RabbitMQ' if features.has_rabbitmq else 'No'}
  Security: {'Yes' if features.has_security else 'No'}
  Scheduling: {'Yes' if features.has_scheduling else 'No'}
  Caching: {'Yes' if features.has_caching else 'No'}
  Validation: {'Yes' if features.has_validation else 'No'}
  Feign Client: {'Yes' if features.has_feign_client else 'No'}
  Circuit Breaker: {'Yes' if features.has_circuit_breaker else 'No'}

Components:
{chr(10).join(component_summary)}
"""

    hard_rules = [
        PromptRule("DOC-H01", "Use Markdown format with proper heading hierarchy (# -> ## -> ### -> ####).", True),
        PromptRule("DOC-H02", "Include these sections: Overview, Architecture, Components, API Reference, Configuration, Build & Run.", True),
        PromptRule("DOC-H03", "Document every REST endpoint with method, path, request/response body, and status codes.", True),
        PromptRule("DOC-H04", "Include a data flow diagram (Mermaid syntax) showing how data moves through layers.", True),
        PromptRule("DOC-H05", "Document all configuration properties with their types and defaults.", True),
        PromptRule("DOC-H06", "Include a table of service responsibilities (Service -> What it does -> Dependencies).", True),
        PromptRule("DOC-H07", "Write for mixed audience: junior devs, senior engineers, architects, QA engineers.", True),
        PromptRule("DOC-H08", "Include a dependency diagram (Mermaid) showing inter-service and inter-component dependencies.", True),
        PromptRule("DOC-H09", "Document all Spring profiles and their effect on application behavior.", True),
        PromptRule("DOC-H10", "Include a troubleshooting section with common errors and their fixes.", True),
        PromptRule("DOC-H11", "The generated documentation must be a single self-contained Markdown file.", True),
    ]

    soft_rules = [
        PromptRule("DOC-S01", "Add sequence diagrams for complex multi-service flows.", False),
        PromptRule("DOC-S02", "Include code examples for key configurations.", False),
        PromptRule("DOC-S03", "Add a 'Getting Started' quick-start section.", False),
        PromptRule("DOC-S04", "Document error codes and their meanings.", False),
        PromptRule("DOC-S05", "Include a glossary of domain terms.", False),
        PromptRule("DOC-S06", "Include curl examples for every REST endpoint.", False),
        PromptRule("DOC-S07", "Add a 'Known Limitations' section.", False),
        PromptRule("DOC-S08", "Include a changelog template for tracking future changes.", False),
    ]

    template = f"""You are a principal software architect. Generate comprehensive technical documentation in Markdown for the following Spring Boot microservice.

## Project Information
{context}

## Requirements

### Mandatory (Hard Rules)
{_format_rules(hard_rules)}

### Recommended (Soft Rules)
{_format_rules(soft_rules)}

## Required Document Structure

```
# {{Project Name}} -- Technical Documentation

## 1. Overview
   - Purpose and scope
   - Key technologies used

## 2. Architecture
   - High-level architecture description
   - Layer diagram (Controller -> Service -> Repository -> Database)
   - Data flow (Mermaid diagram)
   - Dependency diagram (Mermaid)

## 3. Components
   - Table: Component | Type | Responsibility | Dependencies
   - Detailed description of each service class

## 4. API Reference
   - Table: Method | Path | Request Body | Response | Status Codes
   - Detailed endpoint documentation with curl examples

## 5. Data Model
   - Entity descriptions
   - Relationship diagram (if applicable)

## 6. Configuration
   - Application properties table
   - Spring profiles and their effects
   - Environment variables

## 7. Build & Run
   - Prerequisites
   - Build commands
   - Run commands with profiles
   - Docker support (if applicable)

## 8. Error Handling
   - Error response format
   - Common error codes

## 9. Troubleshooting
   - Common errors and fixes
   - Debug tips
```

Generate the complete documentation now.
"""

    steps = [
        "1. Analyze project structure and identify main packages",
        "2. Describe the high-level architecture and layer interactions",
        "3. Create a component inventory with responsibilities",
        "4. Document all REST API endpoints in tabular format with curl examples",
        "5. Describe the data model and entity relationships",
        "6. List all configuration properties with defaults",
        "7. Generate Mermaid data flow and dependency diagrams",
        "8. Write build and run instructions",
        "9. Document error handling patterns and troubleshooting tips",
    ]

    return GeneratedPrompt(
        prompt_type=PromptType.DOCUMENTATION,
        purpose=f"Generate comprehensive Markdown documentation for {analysis.project_name}",
        hard_rules=hard_rules,
        soft_rules=soft_rules,
        context=context,
        template_body=template,
        target_classes=[c.class_info.name for c in analysis.components],
        conditional_trigger=f"Project has {features.total_classes} classes across {len(features.packages)} packages",
        execution_steps=steps,
    )


# ======================================================================
#  C4 ARCHITECTURE PROMPT
# ======================================================================

def build_c4_architecture_prompt(
    analysis: CodebaseAnalysis,
) -> GeneratedPrompt:
    """Build a single prompt for generating C4 architecture diagrams in PlantUML."""

    features = analysis.features

    # Build dependency graph summary
    dep_lines = []
    for cls_name, deps in analysis.class_dependency_graph.items():
        if deps:
            dep_lines.append(f"  {cls_name} -> {', '.join(deps)}")

    dep_graph_str = "\n".join(dep_lines) if dep_lines else "  (no dependencies detected)"

    # Component breakdown
    comp_by_type: Dict[str, List[str]] = {}
    for comp in analysis.components:
        ct = comp.component_type.value
        comp_by_type.setdefault(ct, []).append(comp.class_info.name)

    comp_breakdown = "\n".join(
        f"  {ct}: {', '.join(names)}" for ct, names in comp_by_type.items()
    )

    context = f"""Project: {analysis.project_name}
Total Classes: {features.total_classes}

Component Breakdown:
{comp_breakdown}

Dependency Graph:
{dep_graph_str}

External Systems:
  {'Database (' + ', '.join(features.database_types) + ')' if features.has_database else ''}
  {'Kafka Message Broker' if features.has_kafka else ''}
  {'RabbitMQ Message Broker' if features.has_rabbitmq else ''}
  {'External APIs (Feign Client)' if features.has_feign_client else ''}
"""

    hard_rules = [
        PromptRule("C4-H01", "Use PlantUML syntax with C4-PlantUML library (!include C4_*).", True),
        PromptRule("C4-H02", "Generate Context diagram (System -> External Systems).", True),
        PromptRule("C4-H03", "Generate Container diagram (showing application containers and data stores).", True),
        PromptRule("C4-H04", "Generate Component diagram (showing internal components and their relationships).", True),
        PromptRule("C4-H05", "Use standard C4 elements: Person, System, Container, Component, Rel.", True),
        PromptRule("C4-H06", "Include descriptions for every element and relationship.", True),
        PromptRule("C4-H07", "Show data flow direction in relationships.", True),
        PromptRule("C4-H08", "Include deployment diagram if Kubernetes/Docker annotations are detected.", True),
        PromptRule("C4-H09", "Show async communication (messaging) with dashed arrows (Rel_D or similar).", True),
    ]

    soft_rules = [
        PromptRule("C4-S01", "Use color coding: blue for internal components, gray for external systems.", False),
        PromptRule("C4-S02", "Add technology labels to containers (e.g., 'Spring Boot', 'PostgreSQL').", False),
        PromptRule("C4-S03", "Include legends for diagram readability.", False),
        PromptRule("C4-S04", "Show deployment zones if cloud infrastructure is detectable.", False),
        PromptRule("C4-S05", "Include a dynamic diagram for key user workflows.", False),
        PromptRule("C4-S06", "Add boundary boxes for microservice groupings.", False),
    ]

    template = f"""You are a software architect specializing in C4 modeling. Generate C4 architecture diagrams in PlantUML format for the following Spring Boot microservice.

## Project Information
{context}

## Requirements

### Mandatory (Hard Rules)
{_format_rules(hard_rules)}

### Recommended (Soft Rules)
{_format_rules(soft_rules)}

## Required Diagrams

### 1. Context Diagram (Level 1)
Show the system in its environment -- who uses it and what external systems it connects to.

```plantuml
@startuml C4_Context
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml
' Define elements here
@enduml
```

### 2. Container Diagram (Level 2)
Show the high-level technology decisions -- web app, database, message broker, etc.

```plantuml
@startuml C4_Container
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml
' Define elements here
@enduml
```

### 3. Component Diagram (Level 3)
Show internal components -- controllers, services, repositories -- and their relationships.

```plantuml
@startuml C4_Component
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml
' Define elements here
@enduml
```

Generate all three PlantUML diagrams now.
"""

    steps = [
        "1. Identify the system boundary and external actors",
        "2. Map external systems (databases, message brokers, APIs)",
        "3. Create Context diagram with Person and System elements",
        "4. Identify containers (Spring Boot app, data stores, brokers)",
        "5. Create Container diagram with technology labels",
        "6. Map internal components from the dependency graph",
        "7. Create Component diagram showing Controller -> Service -> Repository flow",
        "8. Add relationship descriptions and data flow directions",
    ]

    return GeneratedPrompt(
        prompt_type=PromptType.C4_ARCHITECTURE,
        purpose=f"Generate C4 architecture diagrams (PlantUML) for {analysis.project_name}",
        hard_rules=hard_rules,
        soft_rules=soft_rules,
        context=context,
        template_body=template,
        target_classes=[c.class_info.name for c in analysis.components],
        conditional_trigger=f"Project has {features.total_classes} classes with inter-component dependencies",
        execution_steps=steps,
    )


# ======================================================================
#  RUN ARGUMENTS PROMPT
# ======================================================================

def build_run_arguments_prompt(
    analysis: CodebaseAnalysis,
) -> GeneratedPrompt:
    """Build a single prompt for generating runtime execution arguments."""

    features = analysis.features

    # Collect config properties from all configuration components
    all_config_props = []
    for comp in analysis.components:
        if comp.component_type == ComponentType.CONFIGURATION:
            all_config_props.extend(comp.config_properties)

    config_props_str = "\n".join(f"  - {p}" for p in all_config_props) if all_config_props else "  (none detected)"

    context = f"""Project: {analysis.project_name}
Database: {'Yes (' + ', '.join(features.database_types) + ')' if features.has_database else 'No'}
Messaging: {'Kafka' if features.has_kafka else 'RabbitMQ' if features.has_rabbitmq else 'No'}
Security: {'Yes' if features.has_security else 'No'}
Spring Profiles Detected: {', '.join(features.spring_profiles) if features.spring_profiles else 'none'}

Configuration Properties Found:
{config_props_str}
"""

    hard_rules = [
        PromptRule("RUN-H01", "Provide CLI commands using `java -jar` format.", True),
        PromptRule("RUN-H02", "Include Spring profile activation (--spring.profiles.active=).", True),
        PromptRule("RUN-H03", "Include essential JVM parameters (-Xms, -Xmx, -XX:+UseG1GC).", True),
        PromptRule("RUN-H04", "List all required environment variables with descriptions.", True),
        PromptRule("RUN-H05", "Provide separate commands for dev, staging, and production.", True),
        PromptRule("RUN-H06", "Include Docker run command if containerization is applicable.", True),
        PromptRule("RUN-H07", "Include Kubernetes deployment YAML snippet if applicable.", True),
        PromptRule("RUN-H08", "Include graceful shutdown configuration (server.shutdown=graceful, timeout settings).", True),
    ]

    soft_rules = [
        PromptRule("RUN-S01", "Include Gradle/Maven commands for building the artifact.", False),
        PromptRule("RUN-S02", "Add JMX monitoring flags for production.", False),
        PromptRule("RUN-S03", "Include health check curl commands.", False),
        PromptRule("RUN-S04", "Provide docker-compose example if multiple services are involved.", False),
        PromptRule("RUN-S05", "Add Prometheus metrics endpoint configuration.", False),
        PromptRule("RUN-S06", "Include log-level tuning flags per profile (e.g., --logging.level.root=WARN for prod).", False),
    ]

    template = f"""You are a DevOps engineer. Generate runtime execution arguments and run commands for the following Spring Boot microservice.

## Project Information
{context}

## Requirements

### Mandatory (Hard Rules)
{_format_rules(hard_rules)}

### Recommended (Soft Rules)
{_format_rules(soft_rules)}

## Required Sections

### 1. Environment Variables
Table: Variable | Description | Required | Default | Example

### 2. Spring Profiles
- dev: local development settings
- staging: pre-production settings
- prod: production settings

### 3. JVM Parameters
- Memory settings
- GC configuration
- Debug flags

### 4. CLI Run Commands
```bash
# Development
java -jar ...

# Staging
java -jar ...

# Production
java -jar ...
```

### 5. Docker
```bash
docker run ...
docker-compose up ...
```

### 6. Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
...
```

### 7. Build Commands
```bash
# Gradle
./gradlew build

# Maven
mvn clean package
```

### 8. Graceful Shutdown
- server.shutdown=graceful
- spring.lifecycle.timeout-per-shutdown-phase

Generate all run argument documentation now.
"""

    steps = [
        "1. Identify required environment variables from configuration",
        "2. Determine Spring profiles from codebase analysis",
        "3. Calculate appropriate JVM memory settings for the service size",
        "4. Build CLI commands for each environment",
        "5. Create Docker run commands with environment mapping",
        "6. Create Kubernetes deployment manifest",
        "7. Add build commands for Gradle/Maven",
        "8. Include health check, graceful shutdown, and monitoring commands",
    ]

    return GeneratedPrompt(
        prompt_type=PromptType.RUN_ARGUMENTS,
        purpose=f"Generate runtime execution arguments for {analysis.project_name}",
        hard_rules=hard_rules,
        soft_rules=soft_rules,
        context=context,
        template_body=template,
        target_classes=[],
        conditional_trigger="Project analysis completed -- run arguments always generated",
        execution_steps=steps,
    )


# ======================================================================
#  HELPERS
# ======================================================================

def _format_rules(rules: List[PromptRule]) -> str:
    """Format rules into numbered markdown list. No emojis."""
    lines = []
    for r in rules:
        prefix = "[HARD]" if r.is_hard else "[SOFT]"
        lines.append(f"{prefix} [{r.id}] {r.description}")
    return "\n".join(lines)


def _format_dependencies(deps) -> str:
    """Format dependency list for prompt context."""
    if not deps:
        return "No dependencies to mock."
    lines = []
    for d in deps:
        lines.append(f"- {d.type} {d.field_name} (injected via {d.injection_method})")
    return "\n".join(lines)


# ======================================================================
#  MASTER ORCHESTRATOR PROMPT
# ======================================================================

def build_master_orchestrator_prompt(
    analysis: CodebaseAnalysis,
    child_prompts: List[GeneratedPrompt],
    child_filenames: List[str],
) -> GeneratedPrompt:
    """
    Build the root/master orchestrator prompt.

    This prompt:
    1. Summarises the whole project
    2. Declares global rules that apply across every sub-task
    3. Lists every child prompt in an explicit Invocation Chain table
    4. Provides inline summaries of each child
    5. Instructs the LLM to execute child prompts sequentially
    """
    features = analysis.features

    # -- Project feature table ------------------------------------------
    feature_rows = [
        f"| REST Controllers   | {'Yes (' + str(features.controller_count) + ')' if features.has_rest_controllers else 'No'} |",
        f"| Database / JPA     | {'Yes (' + ', '.join(features.database_types) + ')' if features.has_database else 'No'} |",
        f"| Messaging          | {'Kafka' if features.has_kafka else 'RabbitMQ' if features.has_rabbitmq else 'No'} |",
        f"| Security           | {'Yes' if features.has_security else 'No'} |",
        f"| Caching            | {'Yes' if features.has_caching else 'No'} |",
        f"| Validation         | {'Yes' if features.has_validation else 'No'} |",
        f"| Exception Handling | {'Yes' if features.has_exception_handling else 'No'} |",
        f"| Scheduling         | {'Yes' if features.has_scheduling else 'No'} |",
    ]
    feature_table = "\n".join(feature_rows)

    # -- Component inventory table --------------------------------------
    comp_rows = []
    for comp in analysis.components:
        cls = comp.class_info
        ep_str = f"{len(comp.endpoints)} endpoint(s)" if comp.endpoints else "--"
        dep_str = ", ".join(d.type for d in comp.dependencies) if comp.dependencies else "--"
        comp_rows.append(
            f"| {cls.name} | {comp.component_type.value} | {ep_str} | {dep_str} |"
        )
    comp_table = "\n".join(comp_rows)

    # -- Invocation chain table -----------------------------------------
    chain_rows = []
    for i, (prompt, fname) in enumerate(zip(child_prompts, child_filenames), start=1):
        targets = ", ".join(prompt.target_classes[:3])
        if len(prompt.target_classes) > 3:
            targets += f" (+{len(prompt.target_classes) - 3} more)"
        chain_rows.append(
            f"| {i:02d} | `{fname}` | {prompt.prompt_type.value.replace('_', ' ').title()} "
            f"| {prompt.purpose} | {targets or 'Project-level'} |"
        )
    chain_table = "\n".join(chain_rows)

    # -- Inline sub-task summaries --------------------------------------
    inline_summaries = []
    for i, (prompt, fname) in enumerate(zip(child_prompts, child_filenames), start=1):
        hard_count = len(prompt.hard_rules)
        soft_count = len(prompt.soft_rules)
        first_step = prompt.execution_steps[0] if prompt.execution_steps else "--"
        hard_preview = "\n".join(
            f"  - [HARD] [{r.id}] {r.description}" for r in prompt.hard_rules[:3]
        )
        if len(prompt.hard_rules) > 3:
            hard_preview += f"\n  - (+{len(prompt.hard_rules) - 3} more hard rules in child file)"
        inline_summaries.append(
            f"### Step {i:02d} -- {prompt.purpose}\n"
            f"> **File:** `{fname}` | "
            f"**Trigger:** {prompt.conditional_trigger}\n\n"
            f"**Hard Rules ({hard_count})** (top 3 shown):\n{hard_preview}\n\n"
            f"**Soft Rules:** {soft_count} additional recommendations in child file.\n\n"
            f"**First Execution Step:** {first_step}\n"
        )
    inline_section = "\n".join(inline_summaries)

    # -- Global rules ---------------------------------------------------
    global_hard_rules = [
        PromptRule("GL-H01", "Use Java 17+ features and idioms throughout all generated code.", True),
        PromptRule("GL-H02", "All generated Java files must be fully compilable without modification.", True),
        PromptRule("GL-H03", "Process sub-tasks strictly in the order listed in the Invocation Chain.", True),
        PromptRule("GL-H04", "After each step output: [STEP N COMPLETE] -- [one-line summary].", True),
        PromptRule("GL-H05", "Do not skip any step, even if output seems similar to a previous step.", True),
        PromptRule("GL-H06", "Each child prompt file contains full details, hard rules, and templates for its step.", True),
        PromptRule("GL-H07", "Use org.springframework.boot:spring-boot-starter-test as the primary test dependency.", True),
        PromptRule("GL-H08", "All generated code must follow Google Java Style Guide formatting.", True),
        PromptRule("GL-H09", "Include correct package declaration in every generated Java file, matching the source class.", True),
    ]
    global_soft_rules = [
        PromptRule("GL-S01", "After all steps complete, produce a final summary table: Step | Output | Status.", False),
        PromptRule("GL-S02", "If a step fails or must be skipped, explain why before moving to the next.", False),
        PromptRule("GL-S03", "Keep each step's output in a clearly labelled section.", False),
        PromptRule("GL-S04", "Add TODO comments in generated code for areas needing project-specific customization.", False),
        PromptRule("GL-S05", "Include a README banner in the first generated file listing all output artifacts.", False),
    ]

    # -- Full master prompt template ------------------------------------
    total = len(child_prompts)
    template = f"""You are a senior software engineer, QA lead, and architect working on the **{analysis.project_name}** Spring Boot microservice.

You are executing a full, automated test and documentation generation session. This master prompt is the **root of a nested prompt hierarchy** -- it drives {total} child prompts in order. Work through every step sequentially without skipping.

---

## Project Summary

**Project:** {analysis.project_name}
**Total Classes:** {features.total_classes} | **Controllers:** {features.controller_count} | **Services:** {features.service_count} | **Repositories:** {features.repository_count}

### Feature Matrix
| Feature | Detected |
|---------|----------|
{feature_table}

### Component Inventory
| Class | Type | Endpoints | Dependencies |
|-------|------|-----------|--------------|
{comp_table}

---

## Global Rules (Apply to ALL Steps)

### Mandatory
{_format_rules(global_hard_rules)}

### Recommended
{_format_rules(global_soft_rules)}

---

## Invocation Chain -- {total} Child Prompts

Execute each child prompt **in the order listed below**. For full rules and code templates, open the corresponding file.

| Step | File | Type | Purpose | Target |
|------|------|------|---------|--------|
{chain_table}

---

## Inline Sub-Task Summaries

The summaries below give you enough context to understand each step. Always open the child file for the complete rules and templates before generating output.

{inline_section}
---

## Session Execution Instructions

```
FOR i = 01 TO {total:02d}:
  1. Open child file listed in Step i of the Invocation Chain
  2. Read all Hard Rules and Soft Rules in that file
  3. Generate the required output (Java file / Markdown / PlantUML)
  4. Output: [STEP i COMPLETE] -- [one-line description of what was produced]
  5. GOTO Step i+1
END FOR
```

After Step {total:02d}, produce a final session summary:

```
## Session Complete -- {analysis.project_name}
| Step | Child File | Output Artifact | Status |
|------|-----------|-----------------|--------|
| 01   | ...       | ...             | DONE   |
...
```

**Begin with Step 01 now.**
"""

    execution_steps = [
        "1. Orient: read the Project Summary and Feature Matrix",
        f"2. Apply Global Rules GL-H01 through GL-H09 to all {total} steps",
        "3. Open child file for Step 01 and execute it",
        "4. Confirm with: [STEP 01 COMPLETE] -- [summary]",
        f"5. Continue Step 02 through Step {total:02d} sequentially",
        "6. Produce the final session summary table",
    ]

    return GeneratedPrompt(
        prompt_type=PromptType.MASTER,
        purpose=f"Master orchestrator -- drives {total} sequential child prompts for {analysis.project_name}",
        hard_rules=global_hard_rules,
        soft_rules=global_soft_rules,
        context=f"Project: {analysis.project_name}, {features.total_classes} classes, {total} child prompts",
        template_body=template,
        target_classes=[c.class_info.name for c in analysis.components],
        conditional_trigger="Always generated -- root of the nested prompt hierarchy",
        execution_steps=execution_steps,
    )
