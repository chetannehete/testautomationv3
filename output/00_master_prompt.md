# MASTER ORCHESTRATOR PROMPT

> **Role:** Root of the nested prompt hierarchy -- invokes all child prompts sequentially.
> **Project:** orderservice
> **Child Prompts:** 6

---

You are a senior software engineer, QA lead, and architect working on the **orderservice** Spring Boot microservice.

You are executing a full, automated test and documentation generation session. This master prompt is the **root of a nested prompt hierarchy** -- it drives 6 child prompts in order. Work through every step sequentially without skipping.

---

## Project Summary

**Project:** orderservice
**Total Classes:** 8 | **Controllers:** 1 | **Services:** 1 | **Repositories:** 1

### Feature Matrix
| Feature | Detected |
|---------|----------|
| REST Controllers   | Yes (1) |
| Database / JPA     | Yes (JPA) |
| Messaging          | Kafka |
| Security           | No |
| Caching            | Yes |
| Validation         | Yes |
| Exception Handling | Yes |
| Scheduling         | No |

### Component Inventory
| Class | Type | Endpoints | Dependencies |
|-------|------|-----------|--------------|
| OrderController | rest_controller | 6 endpoint(s) | OrderService |
| Order | entity | -- | -- |
| OrderStatus | unknown | -- | -- |
| GlobalExceptionHandler | exception_handler | -- | -- |
| ResourceNotFoundException | unknown | -- | String, Throwable |
| OrderEventProducer | component | -- | KafkaTemplate<String, Object> |
| OrderRepository | repository | -- | -- |
| OrderService | service | -- | OrderRepository, OrderMapper, OrderEventProducer |

---

## Global Rules (Apply to ALL Steps)

### Mandatory
[HARD] [GL-H01] Use Java 17+ features and idioms throughout all generated code.
[HARD] [GL-H02] All generated Java files must be fully compilable without modification.
[HARD] [GL-H03] Process sub-tasks strictly in the order listed in the Invocation Chain.
[HARD] [GL-H04] After each step output: [STEP N COMPLETE] -- [one-line summary].
[HARD] [GL-H05] Do not skip any step, even if output seems similar to a previous step.
[HARD] [GL-H06] Each child prompt file contains full details, hard rules, and templates for its step.
[HARD] [GL-H07] Use org.springframework.boot:spring-boot-starter-test as the primary test dependency.
[HARD] [GL-H08] All generated code must follow Google Java Style Guide formatting.
[HARD] [GL-H09] Include correct package declaration in every generated Java file, matching the source class.

### Recommended
[SOFT] [GL-S01] After all steps complete, produce a final summary table: Step | Output | Status.
[SOFT] [GL-S02] If a step fails or must be skipped, explain why before moving to the next.
[SOFT] [GL-S03] Keep each step's output in a clearly labelled section.
[SOFT] [GL-S04] Add TODO comments in generated code for areas needing project-specific customization.
[SOFT] [GL-S05] Include a README banner in the first generated file listing all output artifacts.

---

## Invocation Chain -- 6 Child Prompts

Execute each child prompt **in the order listed below**. For full rules and code templates, open the corresponding file.

| Step | File | Type | Purpose | Target |
|------|------|------|---------|--------|
| 01 | `01_unit_test_prompt.md` | Unit Test | Generate JUnit5 + Mockito unit tests for 5 class(es) | OrderController, GlobalExceptionHandler, OrderEventProducer (+2 more) |
| 02 | `02_integration_test_prompt.md` | Integration Test | Generate Spring Boot integration tests for 2 component(s) | OrderController, OrderRepository |
| 03 | `03_e2e_test_prompt.md` | E2E Test | Generate end-to-end tests for orderservice | OrderController |
| 04 | `04_documentation_prompt.md` | Documentation | Generate comprehensive Markdown documentation for orderservice | OrderController, Order, OrderStatus (+5 more) |
| 05 | `05_c4_architecture_prompt.md` | C4 Architecture | Generate C4 architecture diagrams (PlantUML) for orderservice | OrderController, Order, OrderStatus (+5 more) |
| 06 | `06_run_arguments_prompt.md` | Run Arguments | Generate runtime execution arguments for orderservice | Project-level |

---

## Inline Sub-Task Summaries

The summaries below give you enough context to understand each step. Always open the child file for the complete rules and templates before generating output.

### Step 01 -- Generate JUnit5 + Mockito unit tests for 5 class(es)
> **File:** `01_unit_test_prompt.md` | **Trigger:** 5 testable Spring Boot class(es) detected

**Hard Rules (18)** (top 3 shown):
  - [HARD] [UT-H01] Use JUnit5 annotations only (@Test, @BeforeEach, @AfterEach, @DisplayName). Do NOT use JUnit4.
  - [HARD] [UT-H02] Use Mockito (@Mock, @InjectMocks, @ExtendWith(MockitoExtension.class)) for ALL injected dependencies.
  - [HARD] [UT-H03] Follow the Arrange-Act-Assert (AAA) pattern in every test method. Add // Arrange, // Act, // Assert comments.
  - (+15 more hard rules in child file)

**Soft Rules:** 12 additional recommendations in child file.

**First Execution Step:** 1. Read the Class Inventory (5 classes) and identify all public methods per class

### Step 02 -- Generate Spring Boot integration tests for 2 component(s)
> **File:** `02_integration_test_prompt.md` | **Trigger:** 2 component(s) require integration testing

**Hard Rules (14)** (top 3 shown):
  - [HARD] [IT-H01] Use @SpringBootTest for full context tests. Use @WebMvcTest for controller slice tests. Use @DataJpaTest for repository slice tests.
  - [HARD] [IT-H02] Use @AutoConfigureMockMvc and MockMvc for REST API tests.
  - [HARD] [IT-H03] Use @DataJpaTest with @AutoConfigureTestDatabase for repository tests.
  - (+11 more hard rules in child file)

**Soft Rules:** 9 additional recommendations in child file.

**First Execution Step:** 1. Read the Component Inventory (2 components)

### Step 03 -- Generate end-to-end tests for orderservice
> **File:** `03_e2e_test_prompt.md` | **Trigger:** Project has 1 controllers with 6 endpoints

**Hard Rules (10)** (top 3 shown):
  - [HARD] [E2E-H01] Use @SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT).
  - [HARD] [E2E-H02] Use TestRestTemplate or WebTestClient for real HTTP calls (not MockMvc).
  - [HARD] [E2E-H03] Test complete user flows end-to-end, not isolated units.
  - (+7 more hard rules in child file)

**Soft Rules:** 6 additional recommendations in child file.

**First Execution Step:** 1. Map all endpoints into user-facing scenarios

### Step 04 -- Generate comprehensive Markdown documentation for orderservice
> **File:** `04_documentation_prompt.md` | **Trigger:** Project has 8 classes across 6 packages

**Hard Rules (11)** (top 3 shown):
  - [HARD] [DOC-H01] Use Markdown format with proper heading hierarchy (# -> ## -> ### -> ####).
  - [HARD] [DOC-H02] Include these sections: Overview, Architecture, Components, API Reference, Configuration, Build & Run.
  - [HARD] [DOC-H03] Document every REST endpoint with method, path, request/response body, and status codes.
  - (+8 more hard rules in child file)

**Soft Rules:** 8 additional recommendations in child file.

**First Execution Step:** 1. Analyze project structure and identify main packages

### Step 05 -- Generate C4 architecture diagrams (PlantUML) for orderservice
> **File:** `05_c4_architecture_prompt.md` | **Trigger:** Project has 8 classes with inter-component dependencies

**Hard Rules (9)** (top 3 shown):
  - [HARD] [C4-H01] Use PlantUML syntax with C4-PlantUML library (!include C4_*).
  - [HARD] [C4-H02] Generate Context diagram (System -> External Systems).
  - [HARD] [C4-H03] Generate Container diagram (showing application containers and data stores).
  - (+6 more hard rules in child file)

**Soft Rules:** 6 additional recommendations in child file.

**First Execution Step:** 1. Identify the system boundary and external actors

### Step 06 -- Generate runtime execution arguments for orderservice
> **File:** `06_run_arguments_prompt.md` | **Trigger:** Project analysis completed -- run arguments always generated

**Hard Rules (8)** (top 3 shown):
  - [HARD] [RUN-H01] Provide CLI commands using `java -jar` format.
  - [HARD] [RUN-H02] Include Spring profile activation (--spring.profiles.active=).
  - [HARD] [RUN-H03] Include essential JVM parameters (-Xms, -Xmx, -XX:+UseG1GC).
  - (+5 more hard rules in child file)

**Soft Rules:** 6 additional recommendations in child file.

**First Execution Step:** 1. Identify required environment variables from configuration

---

## Session Execution Instructions

```
FOR i = 01 TO 06:
  1. Open child file listed in Step i of the Invocation Chain
  2. Read all Hard Rules and Soft Rules in that file
  3. Generate the required output (Java file / Markdown / PlantUML)
  4. Output: [STEP i COMPLETE] -- [one-line description of what was produced]
  5. GOTO Step i+1
END FOR
```

After Step 06, produce a final session summary:

```
## Session Complete -- orderservice
| Step | Child File | Output Artifact | Status |
|------|-----------|-----------------|--------|
| 01   | ...       | ...             | DONE   |
...
```

**Begin with Step 01 now.**


---

*Generated by MD Agent Prompt Orchestrator v2.0 -- Master Prompt*
