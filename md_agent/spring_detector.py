"""
Spring Boot Pattern Detector

Analyzes parsed Java classes and detects Spring Boot architectural patterns:
- REST Controllers, Services, Repositories, Entities
- Messaging (Kafka, RabbitMQ), Security, Scheduling
- Configuration classes, DTOs, Mappers
- Endpoint extraction, dependency injection detection
- Project-level feature aggregation
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set

from md_agent.models import (
    ClassInfo,
    CodebaseAnalysis,
    ComponentType,
    DependencyInfo,
    EndpointInfo,
    FieldInfo,
    MethodInfo,
    ProjectFeatures,
    SpringComponent,
)


# ── Annotation → ComponentType mapping ──────────────────────────────────

_ANNOTATION_TYPE_MAP: Dict[str, ComponentType] = {
    "RestController": ComponentType.REST_CONTROLLER,
    "Controller": ComponentType.CONTROLLER,
    "Service": ComponentType.SERVICE,
    "Repository": ComponentType.REPOSITORY,
    "Entity": ComponentType.ENTITY,
    "Table": ComponentType.ENTITY,
    "Document": ComponentType.ENTITY,
    "Configuration": ComponentType.CONFIGURATION,
    "ConfigurationProperties": ComponentType.CONFIGURATION,
    "EnableAutoConfiguration": ComponentType.CONFIGURATION,
    "Component": ComponentType.COMPONENT,
    "KafkaListener": ComponentType.MESSAGING_LISTENER,
    "RabbitListener": ComponentType.MESSAGING_LISTENER,
    "JmsListener": ComponentType.MESSAGING_LISTENER,
    "Scheduled": ComponentType.SCHEDULED_TASK,
    "EnableScheduling": ComponentType.SCHEDULED_TASK,
    "EnableWebSecurity": ComponentType.SECURITY_CONFIG,
    "ControllerAdvice": ComponentType.EXCEPTION_HANDLER,
    "RestControllerAdvice": ComponentType.EXCEPTION_HANDLER,
    "SpringBootApplication": ComponentType.APPLICATION,
    "FeignClient": ComponentType.SERVICE,
}

_HTTP_METHOD_ANNOTATIONS: Dict[str, str] = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
    "RequestMapping": "REQUEST",
}

_MESSAGING_IMPORTS = {
    "org.springframework.kafka": "kafka",
    "org.springframework.amqp": "rabbitmq",
    "org.springframework.jms": "jms",
}


# ═══════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════

def analyze_codebase(classes: List[ClassInfo], project_name: str = "project") -> CodebaseAnalysis:
    """
    Perform full codebase analysis: classify each class, detect features,
    extract endpoints and dependencies, and build a dependency graph.
    """
    components: List[SpringComponent] = []
    all_packages: Set[str] = set()
    dep_graph: Dict[str, List[str]] = {}

    for cls in classes:
        component = classify_component(cls)
        components.append(component)
        if cls.package:
            all_packages.add(cls.package)

        # Build dependency graph
        dep_names = [d.type for d in component.dependencies]
        dep_graph[cls.name] = dep_names

    features = detect_project_features(components, classes)
    features.packages = sorted(all_packages)

    return CodebaseAnalysis(
        project_name=project_name,
        components=components,
        features=features,
        class_dependency_graph=dep_graph,
        all_classes=classes,
    )


def classify_component(cls: ClassInfo) -> SpringComponent:
    """Classify a single Java class into its Spring Boot component type."""
    component_type = _detect_component_type(cls)
    endpoints = _extract_endpoints(cls) if component_type in (
        ComponentType.REST_CONTROLLER, ComponentType.CONTROLLER
    ) else []
    dependencies = _extract_dependencies(cls)
    base_path = _extract_base_path(cls)
    profiles = _extract_profiles(cls)
    config_props = _extract_config_properties(cls)
    bean_methods = _extract_bean_methods(cls)

    return SpringComponent(
        class_info=cls,
        component_type=component_type,
        endpoints=endpoints,
        dependencies=dependencies,
        base_path=base_path,
        profiles=profiles,
        config_properties=config_props,
        bean_methods=bean_methods,
    )


def detect_project_features(
    components: List[SpringComponent],
    classes: List[ClassInfo],
) -> ProjectFeatures:
    """Aggregate project-level features from classified components."""
    features = ProjectFeatures()

    all_annotations: Set[str] = set()
    all_imports: Set[str] = set()
    total_endpoints = 0

    for comp in components:
        all_annotations.update(comp.class_info.annotations)
        all_imports.update(comp.class_info.imports)
        total_endpoints += len(comp.endpoints)

        for method in comp.class_info.methods:
            all_annotations.update(method.annotations)

        ct = comp.component_type
        if ct == ComponentType.REST_CONTROLLER:
            features.controller_count += 1
        elif ct == ComponentType.CONTROLLER:
            features.controller_count += 1
        elif ct == ComponentType.SERVICE:
            features.service_count += 1
        elif ct == ComponentType.REPOSITORY:
            features.repository_count += 1
        elif ct == ComponentType.ENTITY:
            features.entity_count += 1

    features.has_rest_controllers = features.controller_count > 0
    features.total_classes = len(classes)
    features.total_endpoints = total_endpoints

    # Database
    jpa_markers = {"Entity", "Table", "Repository", "JpaRepository",
                   "CrudRepository", "PagingAndSortingRepository"}
    features.has_jpa = bool(all_annotations & jpa_markers) or \
        any("javax.persistence" in imp or "jakarta.persistence" in imp for imp in all_imports)
    features.has_database = features.has_jpa or features.repository_count > 0 or \
        any("spring.datasource" in imp or "jdbc" in imp.lower() for imp in all_imports)

    if features.has_jpa:
        features.database_types.append("JPA")
    if any("mongodb" in imp.lower() for imp in all_imports):
        features.database_types.append("MongoDB")
    if any("redis" in imp.lower() for imp in all_imports):
        features.database_types.append("Redis")

    # Messaging
    features.has_kafka = any("kafka" in imp.lower() for imp in all_imports) or \
        "KafkaListener" in all_annotations or "EnableKafka" in all_annotations
    features.has_rabbitmq = any("amqp" in imp.lower() or "rabbit" in imp.lower() for imp in all_imports) or \
        "RabbitListener" in all_annotations or "EnableRabbit" in all_annotations
    features.has_messaging = features.has_kafka or features.has_rabbitmq

    # Security
    features.has_security = "EnableWebSecurity" in all_annotations or \
        any("security" in imp.lower() for imp in all_imports)

    # Scheduling
    features.has_scheduling = "Scheduled" in all_annotations or "EnableScheduling" in all_annotations

    # Caching
    features.has_caching = "Cacheable" in all_annotations or "EnableCaching" in all_annotations

    # Actuator
    features.has_actuator = any("actuator" in imp.lower() for imp in all_imports)

    # Swagger/OpenAPI
    features.has_swagger = any("swagger" in imp.lower() or "openapi" in imp.lower() for imp in all_imports)

    # Validation
    features.has_validation = "Valid" in all_annotations or "Validated" in all_annotations or \
        any("validation" in imp.lower() for imp in all_imports)

    # Exception handling
    features.has_exception_handling = "ControllerAdvice" in all_annotations or \
        "RestControllerAdvice" in all_annotations or "ExceptionHandler" in all_annotations

    # Feign client
    features.has_feign_client = "FeignClient" in all_annotations or \
        any("feign" in imp.lower() for imp in all_imports)

    # Circuit breaker
    features.has_circuit_breaker = "CircuitBreaker" in all_annotations or \
        any("resilience4j" in imp.lower() or "hystrix" in imp.lower() for imp in all_imports)

    return features


# ═══════════════════════════════════════════════════════════════════════
#  INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _detect_component_type(cls: ClassInfo) -> ComponentType:
    """Determine the Spring component type from annotations and naming."""
    # Check class-level annotations first
    for ann in cls.annotations:
        if ann in _ANNOTATION_TYPE_MAP:
            return _ANNOTATION_TYPE_MAP[ann]

    # Check method-level annotations for scheduled tasks, message listeners
    for method in cls.methods:
        for ann in method.annotations:
            if ann in ("Scheduled",):
                return ComponentType.SCHEDULED_TASK
            if ann in ("KafkaListener", "RabbitListener", "JmsListener"):
                return ComponentType.MESSAGING_LISTENER

    # Check extends/implements for repositories
    if cls.extends and any(r in cls.extends for r in
                            ["JpaRepository", "CrudRepository", "MongoRepository",
                             "PagingAndSortingRepository", "ReactiveCrudRepository"]):
        return ComponentType.REPOSITORY

    if cls.implements:
        for iface in cls.implements:
            if any(r in iface for r in ["Repository", "Dao"]):
                return ComponentType.REPOSITORY

    # Convention-based detection from class name suffixes
    name = cls.name
    if name.endswith("Controller") or name.endswith("Resource"):
        return ComponentType.CONTROLLER
    if name.endswith("Service") or name.endswith("ServiceImpl"):
        return ComponentType.SERVICE
    if name.endswith("Repository") or name.endswith("Dao"):
        return ComponentType.REPOSITORY
    if name.endswith("Entity") or name.endswith("Model"):
        return ComponentType.ENTITY
    if name.endswith("Config") or name.endswith("Configuration"):
        return ComponentType.CONFIGURATION
    if name.endswith("Dto") or name.endswith("DTO") or name.endswith("Request") or name.endswith("Response"):
        return ComponentType.DTO
    if name.endswith("Mapper"):
        return ComponentType.MAPPER
    if name.endswith("Filter"):
        return ComponentType.FILTER
    if name.endswith("Interceptor"):
        return ComponentType.INTERCEPTOR
    if name.endswith("Test") or name.endswith("Tests") or name.endswith("IT"):
        return ComponentType.TEST

    # Check for @Test annotation on methods
    for method in cls.methods:
        if "Test" in method.annotations:
            return ComponentType.TEST

    return ComponentType.UNKNOWN


def _extract_endpoints(cls: ClassInfo) -> List[EndpointInfo]:
    """Extract REST API endpoints from a controller class."""
    endpoints: List[EndpointInfo] = []
    base_path = _extract_base_path(cls) or ""

    for method in cls.methods:
        for ann in method.annotations:
            if ann in _HTTP_METHOD_ANNOTATIONS:
                http_method = _HTTP_METHOD_ANNOTATIONS[ann]

                # Extract path from annotation value
                method_path = method.annotation_values.get(ann)
                if method_path:
                    # Clean up quotes if present: "path" -> path
                    method_path = method_path.strip('"').strip("'")
                    # Handle value={}, path={} arrays loosely
                    method_path = method_path.replace("{", "").replace("}", "").split(",")[0].strip()
                    if not method_path.startswith("/"):
                        method_path = "/" + method_path
                else:
                    method_path = _guess_endpoint_path(method, ann)

                full_path = f"{base_path}{method_path}" if method_path else base_path

                # Detect path variables
                path_vars = re.findall(r"\{(\w+)\}", full_path)

                # Detect request body
                request_body = None
                query_params = []
                for param in method.parameters:
                    if "RequestBody" in getattr(param, "annotations", []):
                        request_body = param.type
                    # Parameters with @RequestParam
                    if param.type not in ("HttpServletRequest", "HttpServletResponse",
                                          "Model", "BindingResult"):
                        if param.name not in path_vars:
                            query_params.append(param.name)

                endpoints.append(EndpointInfo(
                    http_method=http_method,
                    path=full_path or f"/{method.name}",
                    method_name=method.name,
                    request_body_type=request_body,
                    response_type=method.return_type,
                    path_variables=path_vars,
                    query_params=query_params,
                ))

    return endpoints


def _extract_base_path(cls: ClassInfo) -> Optional[str]:
    """Extract base path from @RequestMapping on the class."""
    if "RequestMapping" in cls.annotations:
        val = cls.annotation_values.get("RequestMapping")
        if val:
            val = val.strip('\"\'').replace("{", "").replace("}", "").split(",")[0].strip()
            if not val.startswith("/"):
                val = "/" + val
            return val
        
        # Heuristic: if class name is XyzController, base path is /xyz
        name = cls.name.replace("Controller", "").replace("Resource", "")
        return f"/{name[0].lower()}{name[1:]}" if name else "/"
    return None


def _guess_endpoint_path(method: MethodInfo, annotation: str) -> str:
    """Guess a reasonable endpoint path from method name."""
    name = method.name
    # Common REST patterns
    if name.startswith("get") and name != "get":
        resource = name[3:]
        return f"/{resource[0].lower()}{resource[1:]}"
    if name.startswith("find"):
        resource = name[4:]
        return f"/{resource[0].lower()}{resource[1:]}" if resource else ""
    if name.startswith("create") or name.startswith("save"):
        return ""
    if name.startswith("update"):
        resource = name[6:]
        return f"/{{{resource[0].lower()}{resource[1:]}Id}}" if resource else "/{id}"
    if name.startswith("delete"):
        resource = name[6:]
        return f"/{{{resource[0].lower()}{resource[1:]}Id}}" if resource else "/{id}"
    return f"/{name}"


def _extract_dependencies(cls: ClassInfo) -> List[DependencyInfo]:
    """Extract injected dependencies from constructors and @Autowired fields."""
    deps: List[DependencyInfo] = []
    seen_types: Set[str] = set()

    # Constructor injection
    for ctor in cls.constructors:
        for param in ctor.parameters:
            if param.type not in seen_types:
                deps.append(DependencyInfo(
                    field_name=param.name,
                    type=param.type,
                    injection_method="constructor",
                ))
                seen_types.add(param.type)

    # Field injection (@Autowired)
    for f in cls.fields:
        if "Autowired" in f.annotations or "Inject" in f.annotations:
            if f.type not in seen_types:
                deps.append(DependencyInfo(
                    field_name=f.name,
                    type=f.type,
                    injection_method="field",
                ))
                seen_types.add(f.type)

    # If no constructor injection found, check field types that look like services
    if not deps:
        service_suffixes = ("Service", "Repository", "Client", "Producer",
                            "Sender", "Handler", "Mapper", "Template")
        for f in cls.fields:
            if any(f.type.endswith(s) for s in service_suffixes):
                if f.type not in seen_types:
                    deps.append(DependencyInfo(
                        field_name=f.name,
                        type=f.type,
                        injection_method="inferred",
                    ))
                    seen_types.add(f.type)

    return deps


def _extract_profiles(cls: ClassInfo) -> List[str]:
    """Extract Spring profiles from @Profile annotation."""
    profiles = []
    if "Profile" in cls.annotations:
        val = cls.annotation_values.get("Profile")
        if val:
            # Clean up: "dev", "prod" -> dev, prod
            cleaned = val.replace("{", "").replace("}", "").replace('"', '').replace("'", "")
            profiles = [p.strip() for p in cleaned.split(",") if p.strip()]
        else:
            # Heuristic
            if cls.name.lower().endswith("dev"):
                profiles.append("dev")
            elif cls.name.lower().endswith("prod"):
                profiles.append("prod")
            elif cls.name.lower().endswith("test"):
                profiles.append("test")
    return profiles


def _extract_config_properties(cls: ClassInfo) -> List[str]:
    """Extract configuration property prefixes."""
    props = []
    if "ConfigurationProperties" in cls.annotations:
        val = cls.annotation_values.get("ConfigurationProperties")
        if val:
            val = val.strip('\"\'')
            # Extract basic prefix if value is format prefix="foo" or just "foo"
            if "prefix=" in val:
                val = val.split("prefix=")[1].split(",")[0].strip('\"\'')
            props.append(val)
        else:
            # Heuristic from class name
            name = cls.name.replace("Properties", "").replace("Config", "")
            prefix = re.sub(r'([A-Z])', r'.\1', name).lower().strip('.')
            props.append(f"app.{prefix}")

    # Check fields that look like @Value injected
    for f in cls.fields:
        if "Value" in f.annotations:
            val = f.annotation_values.get("Value")
            if val:
                clean_val = val.strip("\"'")
                props.append(f"{clean_val} → {f.name}")
            else:
                props.append(f"${{?}} → {f.name}")

    return props


def _extract_bean_methods(cls: ClassInfo) -> List[str]:
    """Extract @Bean method names from configuration classes."""
    return [m.name for m in cls.methods if "Bean" in m.annotations]
