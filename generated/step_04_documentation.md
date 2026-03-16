# orderservice -- Technical Documentation

## 1. Overview
The `orderservice` is a Spring Boot microservice responsible for managing customer orders. It provides a RESTful API for creating, retrieving, updating, and deleting orders, integrating with a PostgreSQL database for persistence and Kafka for event-driven communication.

**Purpose and Scope:**
- Manages the full lifecycle of customer orders within an e-commerce ecosystem.
- Exposes a REST API for external systems and client applications to interact with order data.
- Publishes order-related events (creation, update, cancellation, deletion) to Kafka for downstream services.
- Ensures data consistency and provides robust error handling.

**Key Technologies Used:**
- **Spring Boot 3.x:** For rapid application development and simplified configuration.
- **Spring Data JPA & Hibernate:** For database interaction with PostgreSQL.
- **PostgreSQL:** Relational database for persistent storage of order information.
- **Apache Kafka (Spring Kafka):** For asynchronous event publishing.
- **Lombok:** To reduce boilerplate code (getters, setters, constructors).
- **Maven:** For project build and dependency management.
- **JUnit 5 & Mockito:** For unit testing.
- **Testcontainers:** For integration and E2E testing with real dependencies (PostgreSQL, Kafka).
- **Jackson:** For JSON serialization/deserialization.
- **Validation API (Jakarta Bean Validation):** For input data validation.
- **Spring Cache:** For caching frequently accessed data (though not explicitly detailed in inventory, assumed from "Caching: Yes").

## 2. Architecture

### High-level Architecture Description
The `orderservice` is designed as a typical layered microservice following the Domain-Driven Design principles. It exposes a REST API (Controller layer) that interacts with a Service layer. The Service layer contains the core business logic, orchestrating calls to the Repository layer for data persistence and the Messaging layer for event publication. Exception handling is centralized through a GlobalExceptionHandler.

### Layer Diagram (Conceptual)