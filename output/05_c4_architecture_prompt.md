# Prompt: Step 05/06 -- C4 ARCHITECTURE

---

## Chain Context

| Field | Value |
|-------|-------|
| **Invoked By** | `00_master_prompt.md` |
| **Step** | 05 of 06 |
| **Previous Step** | `04_..._prompt.md` |
| **Next Step** | `06_..._prompt.md` |

Once this step is complete, output: `[STEP 05 COMPLETE] -- [one-line summary]` and proceed to Step 06.

---

## Purpose
Generate C4 architecture diagrams (PlantUML) for orderservice

## Conditional Trigger
> Project has 8 classes with inter-component dependencies

## Target Classes
OrderController, Order, OrderStatus, GlobalExceptionHandler, ResourceNotFoundException, OrderEventProducer, OrderRepository, OrderService

---

## Hard Rules (Mandatory)
- **[C4-H01]** Use PlantUML syntax with C4-PlantUML library (!include C4_*).
- **[C4-H02]** Generate Context diagram (System -> External Systems).
- **[C4-H03]** Generate Container diagram (showing application containers and data stores).
- **[C4-H04]** Generate Component diagram (showing internal components and their relationships).
- **[C4-H05]** Use standard C4 elements: Person, System, Container, Component, Rel.
- **[C4-H06]** Include descriptions for every element and relationship.
- **[C4-H07]** Show data flow direction in relationships.
- **[C4-H08]** Include deployment diagram if Kubernetes/Docker annotations are detected.
- **[C4-H09]** Show async communication (messaging) with dashed arrows (Rel_D or similar).

## Soft Rules (Recommended)
- **[C4-S01]** Use color coding: blue for internal components, gray for external systems.
- **[C4-S02]** Add technology labels to containers (e.g., 'Spring Boot', 'PostgreSQL').
- **[C4-S03]** Include legends for diagram readability.
- **[C4-S04]** Show deployment zones if cloud infrastructure is detectable.
- **[C4-S05]** Include a dynamic diagram for key user workflows.
- **[C4-S06]** Add boundary boxes for microservice groupings.

---

## Execution Steps
1. Identify the system boundary and external actors
2. Map external systems (databases, message brokers, APIs)
3. Create Context diagram with Person and System elements
4. Identify containers (Spring Boot app, data stores, brokers)
5. Create Container diagram with technology labels
6. Map internal components from the dependency graph
7. Create Component diagram showing Controller -> Service -> Repository flow
8. Add relationship descriptions and data flow directions

---

## Prompt Template

You are a software architect specializing in C4 modeling. Generate C4 architecture diagrams in PlantUML format for the following Spring Boot microservice.

## Project Information
Project: orderservice
Total Classes: 8

Component Breakdown:
  rest_controller: OrderController
  entity: Order
  unknown: OrderStatus, ResourceNotFoundException
  exception_handler: GlobalExceptionHandler
  component: OrderEventProducer
  repository: OrderRepository
  service: OrderService

Dependency Graph:
  OrderController -> OrderService
  ResourceNotFoundException -> String, Throwable
  OrderEventProducer -> KafkaTemplate<String, Object>
  OrderService -> OrderRepository, OrderMapper, OrderEventProducer

External Systems:
  Database (JPA)
  Kafka Message Broker
  
  


## Requirements

### Mandatory (Hard Rules)
[HARD] [C4-H01] Use PlantUML syntax with C4-PlantUML library (!include C4_*).
[HARD] [C4-H02] Generate Context diagram (System -> External Systems).
[HARD] [C4-H03] Generate Container diagram (showing application containers and data stores).
[HARD] [C4-H04] Generate Component diagram (showing internal components and their relationships).
[HARD] [C4-H05] Use standard C4 elements: Person, System, Container, Component, Rel.
[HARD] [C4-H06] Include descriptions for every element and relationship.
[HARD] [C4-H07] Show data flow direction in relationships.
[HARD] [C4-H08] Include deployment diagram if Kubernetes/Docker annotations are detected.
[HARD] [C4-H09] Show async communication (messaging) with dashed arrows (Rel_D or similar).

### Recommended (Soft Rules)
[SOFT] [C4-S01] Use color coding: blue for internal components, gray for external systems.
[SOFT] [C4-S02] Add technology labels to containers (e.g., 'Spring Boot', 'PostgreSQL').
[SOFT] [C4-S03] Include legends for diagram readability.
[SOFT] [C4-S04] Show deployment zones if cloud infrastructure is detectable.
[SOFT] [C4-S05] Include a dynamic diagram for key user workflows.
[SOFT] [C4-S06] Add boundary boxes for microservice groupings.

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


---

*Generated by MD Agent Prompt Orchestrator v2.0*
