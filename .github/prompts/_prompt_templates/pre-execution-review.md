Certainly. Here is the complete version as Markdown that you can paste directly at the beginning of a Codex prompt.

# Pre-Execution Review — Do Not Modify Code Yet

Before implementing, modifying, installing, or executing anything, read this **entire prompt from beginning to end** and perform a **pre-execution review**.

During this review, analyze both the prompt and the existing codebase, where applicable.

---

## 1. Requirements Review

Identify any:

* Contradictory requirements
* Inconsistent requirements
* Ambiguous or underspecified requirements
* Duplicate or overlapping requirements
* Requirements that appear technically incompatible
* Missing information required to implement the solution correctly
* Assumptions you would otherwise need to make

---

## 2. Architecture and Existing Code Review

Review the relevant existing code, project structure, interfaces, models, APIs, configuration, and established patterns before proposing implementation changes.

Identify:

* Conflicts between this prompt and the existing architecture
* Existing functionality that should be reused rather than duplicated
* Changes that could break existing interfaces or behavior
* Backward-compatibility concerns
* Opportunities where the requested implementation should follow an existing project pattern
* Architectural decisions in the prompt that may create unnecessary coupling, duplication, or technical debt

Do not redesign the architecture merely because you prefer another approach. Flag architectural concerns and explain them before implementation.

---

## 3. Dependency and Environment Review

Determine whether the implementation requires any:

* New Python packages
* Package upgrades or downgrades
* External libraries
* Databases or database changes
* Docker services
* Operating-system software
* Environment variables
* API keys or credentials
* Configuration changes
* External services
* Development tools

For every new dependency, explain:

1. Why it is required
2. The recommended package/software and version, when relevant
3. Whether an existing dependency can provide the same functionality
4. Any compatibility concerns with the project's current environment

**Do not install, upgrade, downgrade, or remove dependencies without my approval.**

---

## 4. Implementation Risk Review

Identify anything that could affect:

* Existing functionality
* API compatibility
* Data models or schemas
* Database migrations
* Error handling
* Security
* Performance
* Concurrency or asynchronous processing
* Testing
* Deployment
* Configuration
* Observability/logging

Distinguish between:

* **Blocking issues** — must be resolved before implementation
* **Non-blocking recommendations** — can be considered separately and should not prevent implementation unless I choose to address them

---

## 5. Pre-Execution Response

If you identify any blocking issues, contradictions, missing information, required corrections, or required dependency/environment changes:

**STOP. Do not implement anything.**

Provide a concise report organized as:

### Blocking Issues

List anything that prevents safe or correct implementation.

### Questions / Clarifications

List any information you need from me before proceeding.

### Required Dependencies or Environment Changes

List any software, packages, configuration, environment variables, services, or other prerequisites that must be added or changed.

### Recommended Corrections

Identify specific changes that should be made to this prompt or the proposed design.

### Non-Blocking Recommendations

List improvements that may be beneficial but are not required for implementation.

For each issue, reference the relevant requirement or section of this prompt when possible.

Then **STOP and wait for me** to:

* Make the requested corrections
* Perform any required installations
* Answer your questions
* Modify the requirements
* Explicitly authorize you to make the necessary changes

Do not begin implementation until I explicitly respond with authorization such as:

> **Proceed with implementation.**

---

## 6. If No Blocking Issues Exist

If the prompt is internally consistent, sufficiently specified, compatible with the existing project, and requires no unapproved dependency or environment changes, provide:

### Understanding

Briefly summarize your understanding of the requested implementation.

### Expected Changes

Identify the major components and files you expect to:

* Create
* Modify
* Remove, if applicable

### Assumptions

List any non-blocking assumptions you intend to make.

### Dependencies

Confirm whether:

* No new dependencies are required

or

* New dependencies are recommended but not required

Then **STOP and wait for my authorization**.

Do not begin implementation until I explicitly respond:

> **Proceed with implementation.**

---

## 7. Implementation Phase

After I authorize implementation:

* Follow the reviewed requirements as the source of truth.
* Preserve existing behavior unless the prompt explicitly requires changing it.
* Prefer existing project patterns, utilities, abstractions, and dependencies over introducing new ones.
* Do not silently change requirements or architectural decisions.
* Do not introduce new dependencies without approval.
* Maintain backward compatibility unless explicitly instructed otherwise.
* Add or update appropriate tests for the implemented behavior.
* Run the relevant tests, linting, formatting, and static/type checks already configured for the project.
* Report any failures that cannot safely be corrected without changing the agreed requirements.

### Newly Discovered Blocking Issues

If a **new blocking issue** is discovered during implementation that was not identified during the pre-execution review:

1. Stop implementation at the safest reasonable point.
2. Explain the issue.
3. Explain why it blocks or materially changes the agreed implementation.
4. Describe the available options for resolving it.
5. Wait for my direction before continuing.

Do not make an architectural or requirements decision on my behalf merely because implementation has already started.

---

# Project-Specific Engineering Constraints

Before reviewing the implementation request, also determine and respect the project's existing engineering conventions.

Where applicable, inspect the project to determine:

* Python version
* Framework and framework version
* FastAPI version
* Pydantic version
* Sync vs. async conventions
* Dependency injection patterns
* Service/provider/repository layering
* Existing domain models
* Existing API conventions
* Existing exception and error-handling patterns
* Logging conventions
* Database technology and access patterns
* Migration framework
* Configuration management
* Environment variable conventions
* Testing framework
* Mocking conventions
* Linting and formatting configuration
* Static/type checking configuration
* Docker/container conventions
* Existing shared utilities and abstractions

Prefer existing project conventions unless this prompt explicitly requires a different approach.

If the requested implementation conflicts with an established project convention, **flag the conflict during the pre-execution review rather than silently choosing one approach.**

---

# Execution Gate

The following rule takes precedence over the implementation instructions that follow:

> **Do not modify code, create files, install software, change dependencies, run migrations, or execute implementation steps until the pre-execution review is complete and I explicitly authorize implementation.**

The remainder of this prompt describes the implementation I want reviewed.

---

# Implementation Request

**[INSERT THE ACTUAL IMPLEMENTATION PROMPT HERE]**

This version is what I'd use as a reusable **standard preamble** for larger Codex tasks. The `# Implementation Request` section gives you a clean boundary: keep the preamble essentially unchanged and paste each new service specification underneath it.
