# Prompt: Step 04/06 -- DOCUMENTATION

---

## Chain Context

| Field | Value |
|-------|-------|
| **Invoked By** | `00_master_prompt.md` |
| **Step** | 04 of 06 |
| **Previous Step** | `03_..._prompt.md` |
| **Next Step** | `05_..._prompt.md` |

Once this step is complete, output: `[STEP 04 COMPLETE] -- [one-line summary]` and proceed to Step 05.

---

## Purpose
Generate comprehensive Markdown documentation for orderservice

## Conditional Trigger
> Project has 8 classes across 6 packages

## Target Classes
OrderController, Order, OrderStatus, GlobalExceptionHandler, ResourceNotFoundException, OrderEventProducer, OrderRepository, OrderService

---

## Hard Rules (Mandatory)
- **[DOC-H01]** Use Markdown format with proper heading hierarchy (# -> ## -> ### -> ####).
- **[DOC-H02]** Include these sections: Overview, Architecture, Components, API Reference, Configuration, Build & Run.
- **[DOC-H03]** Document every REST endpoint with method, path, request/response body, and status codes.
- **[DOC-H04]** Include a data flow diagram (Mermaid syntax) showing how data moves through layers.
- **[DOC-H05]** Document all configuration properties with their types and defaults.
- **[DOC-H06]** Include a table of service responsibilities (Service -> What it does -> Dependencies).
- **[DOC-H07]** Write for mixed audience: junior devs, senior engineers, architects, QA engineers.
- **[DOC-H08]** Include a dependency diagram (Mermaid) showing inter-service and inter-component dependencies.
- **[DOC-H09]** Document all Spring profiles and their effect on application behavior.
- **[DOC-H10]** Include a troubleshooting section with common errors and their fixes.
- **[DOC-H11]** The generated documentation must be a single self-contained Markdown file.

## Soft Rules (Recommended)
- **[DOC-S01]** Add sequence diagrams for complex multi-service flows.
- **[DOC-S02]** Include code examples for key configurations.
- **[DOC-S03]** Add a 'Getting Started' quick-start section.
- **[DOC-S04]** Document error codes and their meanings.
- **[DOC-S05]** Include a glossary of domain terms.
- **[DOC-S06]** Include curl examples for every REST endpoint.
- **[DOC-S07]** Add a 'Known Limitations' section.
- **[DOC-S08]** Include a changelog template for tracking future changes.

---

## Execution Steps
1. Analyze project structure and identify main packages
2. Describe the high-level architecture and layer interactions
3. Create a component inventory with responsibilities
4. Document all REST API endpoints in tabular format with curl examples
5. Describe the data model and entity relationships
6. List all configuration properties with defaults
7. Generate Mermaid data flow and dependency diagrams
8. Write build and run instructions
9. Document error handling patterns and troubleshooting tips

---

## Prompt Template

You are a principal software architect. Generate comprehensive technical documentation in Markdown for the following Spring Boot microservice.

## Project Information
Project: orderservice
Total Classes: 8
Controllers: 1
Services: 1
Repositories: 1
Entities: 1
Packages: com.example.orderservice.controller, com.example.orderservice.entity, com.example.orderservice.exception, com.example.orderservice.messaging, com.example.orderservice.repository, com.example.orderservice.service

Feature Flags:
  Database: Yes (JPA)
  REST API: Yes
  Messaging: Kafka
  Security: No
  Scheduling: No
  Caching: Yes
  Validation: Yes
  Feign Client: No
  Circuit Breaker: No

Components:
  - [rest_controller] OrderController (6 endpoints) (1 dependencies)
  - [entity] Order
  - [unknown] OrderStatus
  - [exception_handler] GlobalExceptionHandler
  - [unknown] ResourceNotFoundException (2 dependencies)
  - [component] OrderEventProducer (1 dependencies)
  - [repository] OrderRepository
  - [service] OrderService (3 dependencies)


## Requirements

### Mandatory (Hard Rules)
[HARD] [DOC-H01] Use Markdown format with proper heading hierarchy (# -> ## -> ### -> ####).
[HARD] [DOC-H02] Include these sections: Overview, Architecture, Components, API Reference, Configuration, Build & Run.
[HARD] [DOC-H03] Document every REST endpoint with method, path, request/response body, and status codes.
[HARD] [DOC-H04] Include a data flow diagram (Mermaid syntax) showing how data moves through layers.
[HARD] [DOC-H05] Document all configuration properties with their types and defaults.
[HARD] [DOC-H06] Include a table of service responsibilities (Service -> What it does -> Dependencies).
[HARD] [DOC-H07] Write for mixed audience: junior devs, senior engineers, architects, QA engineers.
[HARD] [DOC-H08] Include a dependency diagram (Mermaid) showing inter-service and inter-component dependencies.
[HARD] [DOC-H09] Document all Spring profiles and their effect on application behavior.
[HARD] [DOC-H10] Include a troubleshooting section with common errors and their fixes.
[HARD] [DOC-H11] The generated documentation must be a single self-contained Markdown file.

### Recommended (Soft Rules)
[SOFT] [DOC-S01] Add sequence diagrams for complex multi-service flows.
[SOFT] [DOC-S02] Include code examples for key configurations.
[SOFT] [DOC-S03] Add a 'Getting Started' quick-start section.
[SOFT] [DOC-S04] Document error codes and their meanings.
[SOFT] [DOC-S05] Include a glossary of domain terms.
[SOFT] [DOC-S06] Include curl examples for every REST endpoint.
[SOFT] [DOC-S07] Add a 'Known Limitations' section.
[SOFT] [DOC-S08] Include a changelog template for tracking future changes.

## Required Document Structure

```
# {Project Name} -- Technical Documentation

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


---

*Generated by MD Agent Prompt Orchestrator v2.0*
