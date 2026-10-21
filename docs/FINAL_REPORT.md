# PhoenixML: An Intelligent MLOps Decision-Support Platform for Model Monitoring, Explainability and Adaptive Maintenance

### A Major Project Report
Submitted in partial fulfillment of the requirements for the degree of
**Bachelor of Technology**
in
**Computer Science and Engineering**

**Submitted By:**
**Shailendra Singh Rathore**
[Enrollment / Roll Number]

**Under the Supervision of:**
**[Supervisor / Guide Name]**
[Supervisor Designation]

**[Department Name]**
**[College/University Name]**
[Submission Month, Year]

---

\\newpage

## Certificate

This is to certify that the project entitled **"PhoenixML: An Intelligent MLOps Decision-Support Platform for Model Monitoring, Explainability and Adaptive Maintenance"**, submitted by **Shailendra Singh Rathore** ([Enrollment / Roll Number]), in partial fulfillment of the requirements for the award of the degree of **Bachelor of Technology in Computer Science and Engineering** from **[College/University Name]**, is an authentic work carried out by him under my supervision and guidance.

To the best of my knowledge, the matter embodied in this project report has not been submitted to any other University / Institute for the award of any degree or diploma.

\\vspace{2cm}

\\noindent
\\begin{tabular}{ll}
\\textbf{Supervisor / Guide:} & \\textbf{Head of Department:} \\\\
[Supervisor / Guide Name] & [HOD Name] \\\\
[Supervisor Designation] & Head, [Department Name] \\\\
[Department Name] & [Department Name] \\\\
[College/University Name] & [College/University Name] \\\\
\\end{tabular}

---

\\newpage

## Declaration

I hereby declare that this project report entitled **"PhoenixML: An Intelligent MLOps Decision-Support Platform for Model Monitoring, Explainability and Adaptive Maintenance"** represents my own original work carried out as part of the undergraduate curriculum.

I confirm that:
1. This work has been composed solely by myself under the guidance of my supervisor.
2. Due references and acknowledgements have been made whenever the work of others has been utilized.
3. No portion of this work has been submitted previously for the award of any degree or diploma in this or any other institution.
4. The software developed, architectural models, mathematical formulas, and experimental evaluations presented herein reflect the actual implementation and testing of the PhoenixML platform.

\\vspace{1.5cm}

\\noindent
**Shailendra Singh Rathore** \\\\
[Enrollment / Roll Number] \\\\
Department of Computer Science and Engineering \\\\
[College/University Name]

---

\\newpage

## Acknowledgement

I express my deepest gratitude to my project supervisor, **[Supervisor / Guide Name]**, [Supervisor Designation], [Department Name], for invaluable guidance, patient mentoring, constructive critique, and continuous encouragement throughout the conception, design, and execution of this project.

I extend my sincere thanks to the Head of the Department, **[HOD Name]**, and all faculty members of the [Department Name] at [College/University Name] for providing the academic foundation, institutional support, and computing infrastructure necessary to bring this work to fruition.

I am also thankful to the open-source software and machine learning engineering communities, whose robust libraries - including FastAPI, SQLAlchemy, Alembic, PostgreSQL, SciPy, Scikit-Learn, and React - formed the reliable technical foundation of PhoenixML.

Finally, I dedicate this report to my family and peers, whose unwavering encouragement, patience, and moral support inspired me throughout this endeavor.

\\vspace{1cm}

\\noindent
**Shailendra Singh Rathore**

---

\\newpage

## Abstract

Machine Learning (ML) models deployed in production environments encounter continuously shifting operational distributions, emerging adversarial evasion techniques, and changing user behaviors. In security-sensitive applications such as spam email classification, dynamic text mutations and vocabulary drift cause unmonitored models to suffer silent performance collapse without throwing traditional software runtime exceptions. While contemporary Machine Learning Operations (MLOps) platforms provide operational telemetry and static threshold alerting, they suffer from a fundamental limitation: **passive alerting without structured decision support**. Current tools alert operators that performance has degraded but fail to diagnose the root cause, quantify multi-factor operational health, or provide actionable guidance regarding appropriate maintenance interventions.

This report presents **PhoenixML**, an intelligent MLOps decision-support platform designed to supervise deployed machine learning models throughout their operational lifecycle. PhoenixML integrates multi-source telemetry ingestion, non-parametric statistical data drift detection using two-sample Kolmogorov-Smirnov (KS) tests, windowed performance-based concept drift detection, and a normalized 0-100 composite health assessment policy that dynamically redistributes weights for missing metrics. To bridge raw telemetry and operational maintenance, PhoenixML introduces an Operational Explainability Layer that synthesizes multi-source diagnostic signals, coupled with the **Adaptive Intelligent Model Decision (AIMD)** engine.

Crucially, PhoenixML operates strictly under a **human-in-the-loop (HITL)** architecture. Rather than performing autonomous retraining, autonomous model rollback, or unconstrained production deployment, the AIMD engine evaluates deterministic rule sets to synthesize explainable recommendations across six standardized maintenance actions (`CONTINUE_MONITORING`, `INCREASED_MONITORING`, `DATA_COLLECTION`, `RETRAIN`, `ROLLBACK`, and `HUMAN_REVIEW`). Every recommendation enforces an invariant safety condition (`requires_human_approval = True`), generating an auditable decision log in an enterprise PostgreSQL repository with state-machine-governed approval transitions (`PENDING`, `APPROVED`, `REJECTED`). The platform provides a modern RESTful API implemented in FastAPI, strict Role-Based Access Control (`ADMIN`, `ML_ENGINEER`, `VIEWER`), and an embedded React 18 single-page operator dashboard served directly via static-file mounts.

The platform was verified through a comprehensive automated test suite consisting of **439 passing tests out of 439 total tests** across **32 dedicated test modules** (100% pass rate, 0 failures, 4 warnings). An operational demonstration using a registered model (`SpamGuard-v1`) confirmed the end-to-end telemetry pipeline: an initial observation yielded an F1-score of 0.92 and a Health Score of 92.3/100 (`HEALTHY`), while a subsequent degraded observation yielded an F1-score of 0.66 and a Health Score of 66.7/100 (`WARNING`), prompting the AIMD engine to emit a deterministic `HUMAN_REVIEW` recommendation that was successfully triaged and approved by an authorized human engineer.

**Keywords:** MLOps, Decision Support Systems, Human-in-the-Loop, Model Monitoring, Explainable AI, Data Drift, Concept Drift, Model Health Assessment, Spam Detection, Software Architecture.

---

\\newpage
## Table of Contents

- [Certificate](#certificate)
- [Declaration](#declaration)
- [Acknowledgement](#acknowledgement)
- [Abstract](#abstract)
- [List of Figures](#list-of-figures)
- [List of Tables](#list-of-tables)
- [List of Abbreviations](#list-of-abbreviations)
- [CHAPTER 1 - INTRODUCTION](#chapter-1-introduction)
  - [1.1 Background](#11-background)
  - [1.2 Problem Statement](#12-problem-statement)
  - [1.3 Motivation](#13-motivation)
  - [1.4 Objectives](#14-objectives)
  - [1.5 Scope](#15-scope)
    - [Included in the Current Implementation Scope:](#included-in-the-current-implementation-scope)
    - [Explicitly Excluded from Current Scope (Future Work):](#explicitly-excluded-from-current-scope-future-work)
  - [1.6 Relevance of the Project](#16-relevance-of-the-project)
  - [1.7 Organization of the Report](#17-organization-of-the-report)
- [CHAPTER 2 - LITERATURE REVIEW & RELATED WORK](#chapter-2-literature-review-related-work)
  - [2.1 Introduction](#21-introduction)
  - [2.2 Machine Learning in Production](#22-machine-learning-in-production)
  - [2.3 Algorithms in Spam Email Detection](#23-algorithms-in-spam-email-detection)
  - [2.4 MLOps and Model Lifecycle Management](#24-mlops-and-model-lifecycle-management)
  - [2.5 Model Performance Monitoring](#25-model-performance-monitoring)
  - [2.6 Data Drift Detection](#26-data-drift-detection)
  - [2.7 Concept Drift Detection](#27-concept-drift-detection)
  - [2.8 Model Explainability in Operations](#28-model-explainability-in-operations)
  - [2.9 Automated and Adaptive Decision Support](#29-automated-and-adaptive-decision-support)
  - [2.10 Comparative Analysis of Existing MLOps Tools](#210-comparative-analysis-of-existing-mlops-tools)
  - [2.11 Research Gap](#211-research-gap)
  - [2.12 Chapter Summary](#212-chapter-summary)
- [CHAPTER 3 - SYSTEM ARCHITECTURE & DESIGN](#chapter-3-system-architecture-design)
  - [3.1 Existing System Overview & Operational Deficiencies](#31-existing-system-overview-operational-deficiencies)
  - [3.2 Proposed System: PhoenixML](#32-proposed-system-phoenixml)
    - [Key Innovations of PhoenixML:](#key-innovations-of-phoenixml)
  - [3.3 Functional Requirements Specification](#33-functional-requirements-specification)
  - [3.4 Non-Functional Requirements Specification](#34-non-functional-requirements-specification)
  - [3.5 User Roles and Access Permissions](#35-user-roles-and-access-permissions)
  - [3.6 Use Case Specifications](#36-use-case-specifications)
    - [UC-1: User Authentication and Session Initialization](#uc-1-user-authentication-and-session-initialization)
    - [UC-2: Model Registration](#uc-2-model-registration)
    - [UC-3: Monitoring Telemetry Ingestion](#uc-3-monitoring-telemetry-ingestion)
    - [UC-4: On-Demand AIMD Model Evaluation](#uc-4-on-demand-aimd-model-evaluation)
    - [UC-5: Human Review and Decision Approval](#uc-5-human-review-and-decision-approval)
  - [3.7 Architectural Principles & Domain Decoupling](#37-architectural-principles-domain-decoupling)
    - [Architectural Benefits of Domain Decoupling:](#architectural-benefits-of-domain-decoupling)
  - [3.8 System Architecture & Primary Components](#38-system-architecture-primary-components)
  - [3.9 Single-Port Web Serving Architecture](#39-single-port-web-serving-architecture)
  - [3.10 High-Level Decision Workflow](#310-high-level-decision-workflow)
  - [3.11 Database Architecture & Relational Schema](#311-database-architecture-relational-schema)
  - [3.12 Security & Authentication Architecture](#312-security-authentication-architecture)
  - [3.13 Chapter Summary](#313-chapter-summary)
- [CHAPTER 4 - MONITORING, DRIFT DETECTION & EXPLAINABILITY](#chapter-4-monitoring-drift-detection-explainability)
  - [4.1 Overview of the Analytical Pipeline](#41-overview-of-the-analytical-pipeline)
  - [4.2 Telemetry Ingestion Subsystem](#42-telemetry-ingestion-subsystem)
  - [4.3 Performance Trajectory Analysis](#43-performance-trajectory-analysis)
  - [4.4 Model Health Assessment Methodology](#44-model-health-assessment-methodology)
    - [Metric Weightings and Operational Rationale](#metric-weightings-and-operational-rationale)
    - [Mathematical Normalization and Dynamic Redistribution](#mathematical-normalization-and-dynamic-redistribution)
  - [4.5 Statistical Data Drift Detection Design](#45-statistical-data-drift-detection-design)
    - [Analytical Policy and Thresholds:](#analytical-policy-and-thresholds)
  - [4.6 Windowed Concept Drift Detection Design](#46-windowed-concept-drift-detection-design)
    - [Labeled Window Comparison:](#labeled-window-comparison)
  - [4.7 Operational Explainability Layer Design](#47-operational-explainability-layer-design)
  - [4.8 Domain Decoupling of the Analytical Components](#48-domain-decoupling-of-the-analytical-components)
  - [4.9 Chapter Summary](#49-chapter-summary)
- [CHAPTER 5 - ADAPTIVE MAINTENANCE & DECISION-SUPPORT SYSTEM](#chapter-5-adaptive-maintenance-decision-support-system)
  - [5.1 Philosophy of Decision Support in MLOps](#51-philosophy-of-decision-support-in-mlops)
  - [5.2 Controlled Maintenance Actions](#52-controlled-maintenance-actions)
  - [5.3 Deterministic Decision Rules & Evaluation Logic](#53-deterministic-decision-rules-evaluation-logic)
  - [5.4 Rollback Safety Invariant & Context Verification](#54-rollback-safety-invariant-context-verification)
  - [5.5 Urgency Priority & Evidence Confidence Classifications](#55-urgency-priority-evidence-confidence-classifications)
  - [5.6 Human-in-the-Loop Approval Workflow](#56-human-in-the-loop-approval-workflow)
    - [State Transition Rules:](#state-transition-rules)
  - [5.7 Decision Persistence and Audit Trail Design](#57-decision-persistence-and-audit-trail-design)
    - [Current Schema Scope vs. Future Audit Extensions:](#current-schema-scope-vs-future-audit-extensions)
  - [5.8 Chapter Summary](#58-chapter-summary)
- [CHAPTER 6 - IMPLEMENTATION DETAILS](#chapter-6-implementation-details)
  - [6.1 Implementation Overview & Layered Organization](#61-implementation-overview-layered-organization)
  - [6.2 Core Software Technology Stack](#62-core-software-technology-stack)
  - [6.3 Decoupled Domain Analytical Engines Implementation](#63-decoupled-domain-analytical-engines-implementation)
  - [6.4 Authentication & RBAC Implementation](#64-authentication-rbac-implementation)
  - [6.5 Model Registry Implementation](#65-model-registry-implementation)
  - [6.6 Monitoring Telemetry Ingestion & Query Implementation](#66-monitoring-telemetry-ingestion-query-implementation)
  - [6.7 Health, Drift & Explainability Subsystems Implementation](#67-health-drift-explainability-subsystems-implementation)
  - [6.8 AIMD Engine & Decision Service Implementation](#68-aimd-engine-decision-service-implementation)
  - [6.9 Single-Port Web Serving & Dashboard Implementation](#69-single-port-web-serving-dashboard-implementation)
  - [6.10 Database Schema & Migration Implementation](#610-database-schema-migration-implementation)
  - [6.11 Automated Testing Implementation & Test Architecture](#611-automated-testing-implementation-test-architecture)
  - [6.12 Chapter Summary](#612-chapter-summary)
- [CHAPTER 7 - RESULTS, DEMONSTRATION & EVALUATION](#chapter-7-results-demonstration-evaluation)
  - [7.1 Evaluation Strategy & Test Environment](#71-evaluation-strategy-test-environment)
  - [7.2 Functional Verification of Platform Subsystems](#72-functional-verification-of-platform-subsystems)
  - [7.3 Authentication & RBAC Enforcement Verification](#73-authentication-rbac-enforcement-verification)
  - [7.4 Model Registry & Ownership Scoping Results](#74-model-registry-ownership-scoping-results)
  - [7.5 Monitoring Ingestion & Health Evaluation Results](#75-monitoring-ingestion-health-evaluation-results)
  - [7.6 Drift Detection & Operational Explainability Results](#76-drift-detection-operational-explainability-results)
  - [7.7 Distinction: Monitored Model vs. PhoenixML MLOps Platform](#77-distinction-monitored-model-vs-phoenixml-mlops-platform)
  - [7.8 Telemetry-Driven Demonstration: SpamGuard-v1](#78-telemetry-driven-demonstration-spamguard-v1)
    - [Stage 1: Initial Healthy Observation](#stage-1-initial-healthy-observation)
    - [Stage 2: Degraded Observation (Simulating Operational Distribution Shift)](#stage-2-degraded-observation-simulating-operational-distribution-shift)
    - [AIMD Evaluation of Degraded Telemetry:](#aimd-evaluation-of-degraded-telemetry)
  - [7.9 Human Approval Workflow Execution Results](#79-human-approval-workflow-execution-results)
  - [7.10 Operator Dashboard & Web UI Operational Results](#710-operator-dashboard-web-ui-operational-results)
  - [7.11 Automated Test Suite Execution Results](#711-automated-test-suite-execution-results)
  - [7.12 Database & Migration Consistency Validation](#712-database-migration-consistency-validation)
  - [7.13 Discussion of Findings](#713-discussion-of-findings)
  - [7.14 Chapter Summary](#714-chapter-summary)
- [CHAPTER 8 - CONCLUSION & FUTURE SCOPE](#chapter-8-conclusion-future-scope)
  - [8.1 Conclusion](#81-conclusion)
  - [8.2 Summary of Contributions](#82-summary-of-contributions)
  - [8.3 Current Limitations](#83-current-limitations)
  - [8.4 Future Enhancements](#84-future-enhancements)
  - [8.5 Concluding Remarks](#85-concluding-remarks)
- [REFERENCES](#references)
- [APPENDIX](#appendix)
  - [A. API Reference Summary](#a-api-reference-summary)
  - [B. Database Schema Reference](#b-database-schema-reference)
  - [C. Configuration & Deployment Instructions](#c-configuration-deployment-instructions)
    - [Local Deployment Instructions:](#local-deployment-instructions)
  - [D. Test Suite Summary](#d-test-suite-summary)
  - [E. Demonstration Walkthrough & Interface Specifications](#e-demonstration-walkthrough-interface-specifications)

---

\newpage
## List of Figures

- Figure 3.1 - PhoenixML High-Level Layered Architecture
- Figure 3.2 - Component Collaboration and Evaluation Pipeline
- Figure 3.3 - PhoenixML High-Level Decision Workflow
- Figure 3.4 - Entity Relationship Diagram (ERD) of Database Schema
- Figure 4.1 - PhoenixML Analytical Monitoring & Explainability Pipeline
- Figure 5.1 - AIMD Decision Rule Evaluation Flow
- Figure 5.2 - Decision Approval State Machine Transitions
- Figure 7.1 - Telemetry Progression and Health Degradation for SpamGuard-v1
- Figure 7.2 - End-to-End Decision Support and Human Approval Execution Sequence
- Figure E.1 - Operator Login View:
- Figure E.2 - Operator Dashboard Overview:
- Figure E.3 - Model Registry View:
- Figure E.4 - Monitoring Observations & Telemetry Visualizations:
- Figure E.5 - Health Score Meter and Status Classification:
- Figure E.6 - Feature Data Drift Statistical Summary:
- Figure E.7 - AIMD Recommendation Review Card:
- Figure E.8 - Diagnostic Explainability & Corroborating Signals:
- Figure E.9 - Human Approval Workflow Modal:
- Figure E.10 - Decision History & Audit Trail Table:
- Figure E.11 - Interactive OpenAPI (Swagger UI) Interface:
- Figure E.12 - PostgreSQL Schema Migration Verification:

---

\newpage
## List of Tables

- Table 2.1 - Illustrative / Literature-Based Characteristics of Spam Detection Algorithms (Not Measured PhoenixML Benchmarks)
- Table 2.2 - General Comparison of MLOps Approaches and PhoenixML
- Table 3.1 - Functional Requirements Specification
- Table 3.2 - Non-Functional Requirements Specification
- Table 3.3 - Role-Based Access Control (RBAC) Matrix
- Table 3.4 - Database Schema Specifications: `users`
- Table 3.5 - Database Schema Specifications: `registered_models`
- Table 3.6 - Database Schema Specifications: `monitoring_observations`
- Table 3.7 - Database Schema Specifications: `decision_logs`
- Table 4.1 - Health Score Metric Weightings and Operational Rationale
- Table 4.2 - Health Status Classification Boundaries
- Table 5.1 - AIMD Recommendation Decision Matrix
- Table 5.2 - AIMD Urgency Priority Levels and SLA
- Table 5.3 - AIMD Evidence Confidence Classifications
- Table 6.1 - Core Software Technology Stack
- Table 7.1 - SpamGuard-v1 Operational Telemetry and Health Evaluation Results
- Table 7.2 - SpamGuard-v1 AIMD Recommendation Output
- Table 7.3 - Comprehensive Automated Test Suite Distribution and Coverage
- Table A.1 - Comprehensive PhoenixML REST API Endpoint Directory
- Table C.1 - Core System Configuration Parameters

---

\newpage
## List of Abbreviations

| Abbreviation | Expanded Operational Meaning |
|:---|:---|
| **ACID** | Atomicity, Consistency, Isolation, Durability |
| **AIMD** | Adaptive Intelligent Model Decision |
| **API** | Application Programming Interface |
| **ASGI** | Asynchronous Server Gateway Interface |
| **AUC** | Area Under the ROC Curve |
| **CI/CD** | Continuous Integration / Continuous Delivery |
| **CORS** | Cross-Origin Resource Sharing |
| **CRUD** | Create, Read, Update, Delete |
| **CSS** | Cascading Style Sheets |
| **CSV** | Comma-Separated Values |
| **DOM** | Document Object Model |
| **DSS** | Decision Support System |
| **ECDF** | Empirical Cumulative Distribution Function |
| **E2E** | End-to-End |
| **ERD** | Entity Relationship Diagram |
| **F1** | Harmonic Mean of Precision and Recall |
| **FN** | False Negative |
| **FP** | False Positive |
| **HITL** | Human-in-the-Loop |
| **HOD** | Head of Department |
| **HTML** | HyperText Markup Language |
| **HTTP** | HyperText Transfer Protocol |
| **HTTPS** | HyperText Transfer Protocol Secure |
| **IDE** | Integrated Development Environment |
| **IEEE** | Institute of Electrical and Electronics Engineers |
| **ISO** | International Organization for Standardization |
| **JSON** | JavaScript Object Notation |
| **JWT** | JSON Web Token |
| **KPI** | Key Performance Indicator |
| **KS** | Kolmogorov-Smirnov |
| **LIME** | Local Interpretable Model-agnostic Explanations |
| **ML** | Machine Learning |
| **MLOps** | Machine Learning Operations |
| **NFR** | Non-Functional Requirement |
| **NLP** | Natural Language Processing |
| **ORM** | Object-Relational Mapping |
| **PK** | Primary Key |
| **RBAC** | Role-Based Access Control |
| **REST** | Representational State Transfer |
| **RFC** | Request for Comments |
| **ROC** | Receiver Operating Characteristic |
| **SHAP** | SHapley Additive exPlanations |
| **SLA** | Service Level Agreement |
| **SPA** | Single Page Application |
| **SQL** | Structured Query Language |
| **SRS** | Software Requirements Specification |
| **SVM** | Support Vector Machine |
| **TN** | True Negative |
| **TOC** | Table of Contents |
| **TP** | True Positive |
| **UI** | User Interface |
| **URI** | Uniform Resource Identifier |
| **URL** | Uniform Resource Locator |
| **UTC** | Coordinated Universal Time |
| **UUID** | Universally Unique Identifier |
| **XAI** | Explainable Artificial Intelligence |

---

\newpage
# CHAPTER 1 - INTRODUCTION

## 1.1 Background

Over the past decade, Machine Learning (ML) has transitioned from an experimental research discipline into the foundational substrate of modern software systems. Enterprise applications across finance, healthcare, autonomous navigation, telecommunications, and cybersecurity increasingly rely on predictive models to automate high-stakes decision-making. Among these operational domains, **spam email detection** represents one of the earliest, most pervasive, and most demanding applications of applied classification. Deployed spam filters process billions of messages daily, safeguarding enterprise networks, corporate communications, and end-user productivity against fraudulent phishing campaigns, malware dissemination, financial scams, and unsolicited bulk messaging.

In classical software engineering, functional correctness is preserved post-deployment so long as system code, execution environments, and computational infrastructure remain stable. Machine learning systems, however, present a fundamentally different operational paradigm. An ML model's behavior is inextricably tied to the data distribution on which it was trained. In real-world environments, this underlying data is not static; it evolves dynamically over time. In the spam filtering domain, adversarial actors continuously alter message text, employ character obfuscation, inject adversarial tokens, modify lexical distributions, and adopt generative language models to bypass deployed classification boundaries. Consequently, high predictive performance observed during offline laboratory validation inevitably degrades in production.

This fundamental characteristic of deployed machine learning has motivated the emergence of **Machine Learning Operations (MLOps)**. MLOps bridges software engineering, data engineering, and machine learning to manage the end-to-end operational lifecycle of models. A robust MLOps pipeline encompasses automated packaging, deployment, continuous telemetry collection, performance monitoring, drift detection, and post-deployment maintenance.

## 1.2 Problem Statement

While standard MLOps platforms provide extensive operational telemetry, visualization dashboards, and metric-triggered threshold alerts, they suffer from a major operational limitation: **passive alerting without structured decision support**.

When a deployed spam detection model begins to degrade, existing platforms notify human operators that a performance drop or statistical distribution shift has occurred (for example, alerting that classification accuracy has dropped by 5% or that feature drift has been detected). However, current tools fail to answer critical maintenance questions:
1. *What is the underlying operational driver of the observed degradation?*
2. *Is the degradation caused by marginal input covariate shift (data drift) or a fundamental change in the adversarial classification boundary (concept drift)?*
3. *Does the detected issue warrant costly model retraining, immediate rollback to a verified stable predecessor, collection of targeted labeled data from shifted subspaces, or simply closer observation?*
4. *Can maintenance interventions be justified through transparent, explainable diagnostic evidence rather than opaque, black-box alerts?*

Because existing systems lack structured decision support, ML engineers and operational teams are left to manually triage complex, multi-source telemetry under severe cognitive load. This leads to erratic decision-making: models are either retrained prematurely at high computational expense on noisy data, or degradation is ignored until critical classification failures damage end-user trust.

## 1.3 Motivation

The motivation behind **PhoenixML** arises directly from the need to transform passive MLOps monitoring into **actionable, explainable, and adaptive decision support**. Rather than treating monitoring, drift detection, health scoring, and maintenance triage as disconnected tasks, an intelligent operational platform must synthesize multi-source telemetry into deterministic, policy-governed maintenance recommendations.

Furthermore, operational safety and regulatory compliance dictate that production machine learning systems must maintain strict **human-in-the-loop (HITL)** governance. Autonomous self-healing systems that retrain, re-route, or roll back production models without human oversight introduce severe operational risks, including catastrophic forgetting, vulnerability to adversarial poisoning during automated retraining, and unexpected service disruptions caused by rolling back to corrupted or incompatible artifacts. Therefore, the goal is not to eliminate human oversight, but to empower human engineers with structured, evidence-based recommendations, deterministic rationale narratives, and auditable approval workflows.

Spam email detection serves as the ideal implementation and evaluation domain for PhoenixML. As an inherently adversarial problem characterized by frequent covariate shifts and continuous concept drift, it exercises every facet of production monitoring, statistical drift tracking, composite health evaluation, and adaptive maintenance decision support.

## 1.4 Objectives

The primary objectives of the PhoenixML project are:

1. **Intelligent MLOps Decision-Support Architecture:** Design and develop a modular, service-oriented platform that supervises deployed machine learning models throughout their post-deployment lifecycle.
2. **Multi-Metric Telemetry Monitoring:** Ingest, structure, and query runtime classification telemetry (accuracy, precision, recall, F1-score, prediction volume, class distribution) across chronologically ordered observation windows.
3. **Statistical Data Drift Detection:** Implement non-parametric two-sample Kolmogorov-Smirnov (KS) tests to detect feature distribution shifts between baseline reference datasets and runtime production observations.
4. **Windowed Concept Drift Detection:** Implement a labeled-window evaluation mechanism that tracks performance degradation across sliding ground-truth evaluation windows as an operational proxy for concept drift.
5. **Weighted Composite Health Assessment:** Develop a robust model health scoring engine that maps classification metrics into a normalized 0-100 operational health score with dynamic weight redistribution for missing metrics and configurable health classifications (`HEALTHY`, `WARNING`, `CRITICAL`, `INSUFFICIENT_DATA`).
6. **Operational Explainability Layer:** Synthesize multi-source analytical signals into structured, prioritized, human-interpretable operational diagnostics using non-causal associative evidence structures.
7. **Adaptive Intelligent Model Decision (AIMD) Engine:** Implement a deterministic, policy-driven decision engine that evaluates multi-factor operational signals to recommend structured maintenance actions (`CONTINUE_MONITORING`, `INCREASED_MONITORING`, `DATA_COLLECTION`, `RETRAIN`, `ROLLBACK`, `HUMAN_REVIEW`).
8. **Rollback Safety and Non-Autonomous Invariants:** Guarantee system safety by enforcing verified rollback targets in registry metadata before recommending rollbacks, and strictly enforcing that all maintenance actions require human approval (`requires_human_approval = True`).
9. **Decision Persistence and Audit Trail:** Maintain an immutable, PostgreSQL-persisted decision log that tracks model condition, evaluation signals, recommendations, and human approval status transitions (`PENDING`, `APPROVED`, `REJECTED`).
10. **Operator Dashboard and Role-Based Access Control:** Deliver an enterprise-grade RESTful API in FastAPI and an interactive React 18 operator dashboard supporting strict Role-Based Access Control (`ADMIN`, `ML_ENGINEER`, `VIEWER`).
11. **Rigorous System Verification:** Validate the entire platform through automated unit, integration, and end-to-end tests, achieving 100% test pass rates across all implemented modules.

## 1.5 Scope

### Included in the Current Implementation Scope:
- **Application Domain:** Spam email classification management and monitoring.
- **Model Registry:** Lifecycle tracking of registered models, algorithms, frameworks, deployment statuses (`DEVELOPMENT`, `ACTIVE`, `ARCHIVED`), and user ownership. Version designations are tracked via model identity naming conventions and historical context dictionaries.
- **Monitoring & Ingestion:** Persistence and chronological querying of runtime monitoring observations.
- **Analytical Pipelines:** Chronological performance trend tracking, two-sample KS-test data drift detection, windowed concept drift detection, and composite health assessment.
- **Explainability & Decision Support:** Diagnostic synthesis and deterministic AIMD recommendation generation.
- **Human Approval Workflow:** Controlled state-machine-governed approval transitions (`PENDING` -> `APPROVED` / `REJECTED`) with strict field immutability.
- **Full-Stack Implementation:** FastAPI backend, SQLAlchemy 2.0 ORM, Alembic relational migrations, PostgreSQL persistence, and React 18 single-page dashboard.
- **Security:** JWT authentication (access and refresh tokens), password hashing with bcrypt, and comprehensive RBAC.

### Explicitly Excluded from Current Scope (Future Work):
- **Autonomous Production Actions:** The platform does **not** autonomously execute model retraining scripts, trigger automated production deployments, or switch production traffic.
- **Real-Time Streaming Pipelines:** Real-time event streaming via Kafka or distributed message queues is outside the current scope; observations are ingested via batch REST APIs.
- **Automated Model Training within PhoenixML:** PhoenixML supervises and monitors deployed/registered models; it does not train models end-to-end from raw email corpora within the application runtime.
- **Black-Box Causal Proofs:** The explainability layer reports associative statistical evidence; it does not claim mathematical causal proof of model failure.
- **Actor-Level Approval Audit Trail:** While the system validates user permissions via RBAC prior to executing approval actions, persisting dedicated reviewer foreign keys and secondary transition timestamps in the database table is scheduled for future audit log enhancements.

## 1.6 Relevance of the Project

In production machine learning, operational maintenance accounts for over 80% of total lifecycle costs and engineering effort. Unmonitored degradation leads to "silent failures" where models make confident yet erroneous predictions, degrading system security and user trust. In spam detection, failure to adapt allows dangerous phishing campaigns to breach corporate networks or causes legitimate communications to be incorrectly quarantined.

PhoenixML provides immediate academic and industrial relevance by presenting a practical, disciplined methodology for post-deployment ML governance. By combining statistical rigors with transparent decision-support rules, PhoenixML bridges the gap between raw monitoring metrics and human operational action. Its modular design serves as a generalizable blueprint for production model maintenance across other mission-critical ML domains such as fraud detection, credit scoring, and automated clinical triage.

## 1.7 Organization of the Report

The remainder of this report is organized into seven subsequent chapters:
- **Chapter 2 (Literature Review & Related Work):** Reviews foundational concepts in MLOps, spam classification algorithms, statistical drift detection, explainability frameworks, and related operational tools.
- **Chapter 3 (System Architecture & Design):** Details system requirements, architectural principles, domain decoupling, single-port web serving, database schema specifications, and security design.
- **Chapter 4 (Monitoring, Drift Detection & Explainability):** Explains the analytical foundations of telemetry ingestion, performance trend analysis, composite health scoring, data drift, concept drift, and operational explainability.
- **Chapter 5 (Adaptive Maintenance & Decision-Support System):** Details the philosophy, rule evaluation matrix, rollback safety invariants, urgency/confidence ratings, and human approval workflow of the AIMD engine.
- **Chapter 6 (Implementation Details):** Presents the technical implementation of backend services, decoupled analytical components, security layers, database migrations, dashboard UI, and automated test architectures.
- **Chapter 7 (Results, Demonstration & Evaluation):** Evaluates platform functionality, verifies RBAC enforcement, presents the end-to-end `SpamGuard-v1` telemetry demonstration, and details automated test suite verification results (439/439 tests across 32 modules).
- **Chapter 8 (Conclusion & Future Scope):** Concludes the report, synthesizes core engineering contributions, identifies current limitations, and outlines future enhancements.

---

\\newpage


# CHAPTER 2 - LITERATURE REVIEW & RELATED WORK

## 2.1 Introduction

The transition of machine learning from exploratory research prototypes to resilient production infrastructure has revealed significant operational challenges. While training high-accuracy models on curated historical datasets is well-understood, sustaining predictive performance in dynamic real-world environments remains a complex engineering problem. This chapter reviews foundational literature on production machine learning, spam email classification algorithms, MLOps paradigms, model performance monitoring, statistical data drift, concept drift, operational explainability, and automated decision support, identifying the critical research gaps that motivate PhoenixML.

## 2.2 Machine Learning in Production

The challenges of deploying machine learning systems in production were famously characterized by Sculley et al. [1] as **"Hidden Technical Debt in Machine Learning Systems."** The authors argued that in real-world ML systems, only a tiny fraction of the overall codebase consists of actual machine learning algorithms; the vast majority is dedicated to data ingestion, feature extraction, resource management, telemetry infrastructure, monitoring, and operational tooling. Sculley et al. highlighted that ML systems create systemic dependencies that make maintenance and debugging uniquely difficult.

Unlike conventional software, which fails predictably through runtime exceptions or crashes, machine learning models experience **silent degradation** [6], [7]. A deployed classifier continues to accept input vectors, execute matrix multiplications, and emit prediction probabilities without throwing runtime errors, even when its predictive accuracy has completely collapsed due to shifts in input distributions [8]. Breck et al. [2] expanded upon this by introducing **"The ML Test Score: A Rubric for ML Production Readiness,"** which established standard benchmarks for validating data pipelines, monitoring model behavior, and automating production readiness testing. Google's published engineering guidelines, *Rules of Machine Learning: Best Practices for ML Engineering* [3], further emphasize that post-deployment monitoring is not an optional operational add-on, but an indispensable prerequisite for production viability.

## 2.3 Algorithms in Spam Email Detection

Spam email detection represents a classic supervised classification problem where an algorithm maps high-dimensional text representations $\mathbf{x} \in \mathbb{R}^d$ to a binary target $y \in \{0, 1\}$ (where 1 represents spam and 0 represents legitimate email/ham). Over two decades of academic research, various classification paradigms have been applied to this domain, as summarized in Table 2.1.

Table 2.1 - Illustrative / Literature-Based Characteristics of Spam Detection Algorithms (Not Measured PhoenixML Benchmarks)

| Algorithm | Classification Accuracy | Illustrative Inference Latency | Interpretability | Computational Cost | Robustness to Concept Drift |
|:---|:---|:---|:---|:---|:---|
| **Naïve Bayes (Multinomial)** | Moderate to High | Ultra-Low ($\le 5$ ms) | High (Conditional Probabilities) | Very Low | Low (Requires regular frequency updates) |
| **Logistic Regression** | High | Low ($\le 10$ ms) | High (Feature Coefficients) | Low | Moderate (Coefficients degrade gradually) |
| **Support Vector Machines (SVM)** | Very High | Moderate ($\le 25$ ms) | Low to Moderate (Kernel dependent) | High | Moderate (Support vectors shift with drift) |
| **Decision Trees** | Moderate | Low ($\le 10$ ms) | High (Visual Decision Paths) | Low | Low (Brittle to threshold shifts) |
| **Random Forests** | Very High | Moderate ($\le 30$ ms) | Moderate (Feature Importance) | Medium | High (Ensemble averages out noise) |
| **Deep Learning (CNN/LSTM/BERT)**| State-of-the-Art | High ($\ge 80$ ms) | Very Low (Black-Box Representations) | Very High | High (Captures semantic context) |

*Note: The latency figures in Table 2.1 represent illustrative order-of-magnitude values documented in academic literature [6], [7] and are presented solely for comparative contextualization; they do not represent experimental benchmarks measured within PhoenixML.*

While advanced ensemble and deep learning models achieve superior initial classification accuracy on static test corpora [8], their operational maintenance in production is substantially more resource-intensive. In contrast, linear and probabilistic classifiers like Multinomial Naïve Bayes and Logistic Regression remain popular in enterprise gateway pipelines due to their computational efficiency, rapid execution, and direct mathematical interpretability. However, regardless of the underlying algorithm, all classifiers inevitably degrade when faced with production distribution shift.

## 2.4 MLOps and Model Lifecycle Management

Machine Learning Operations (MLOps) has emerged as an engineering discipline dedicated to unifying machine learning system development (Dev) and deployment operations (Ops). Drawing upon principles from Continuous Integration and Continuous Delivery (CI/CD) in software engineering, MLOps formalizes the ML lifecycle into standardized stages:
1. **Data Ingestion & Feature Engineering:** Curating, transforming, and validating raw data streams.
2. **Offline Model Training & Validation:** Training candidate models and evaluating them against fixed validation splits.
3. **Model Versioning & Registry:** Cataloging trained model artifacts, hyperparameters, schemas, and deployment statuses via registries such as MLflow [10].
4. **Production Serving:** Exposing models via low-latency REST or gRPC prediction services.
5. **Continuous Telemetry & Monitoring:** Tracking prediction latency, throughput, error rates, and classification performance over time.
6. **Adaptive Maintenance & Retraining:** Re-evaluating, updating, retraining, or replacing deployed models when performance deteriorates.

While MLOps tooling has matured significantly for offline training and initial deployment, the closing of the operational feedback loop - specifically transforming monitoring telemetry into policy-governed maintenance decisions - remains largely manual.

## 2.5 Model Performance Monitoring

Production model performance monitoring tracks key performance indicators (KPIs) over time to ensure operational efficacy. In spam email classification, tracking accuracy alone is notoriously insufficient due to severe class imbalance (where legitimate emails typically outnumber spam messages by significant ratios) [6, 9]. Consequently, comprehensive performance monitoring requires joint tracking of multiple confusion matrix derivatives:
- **Accuracy:** The proportion of total correct predictions:
  $$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$
- **Precision:** The proportion of positive predictions that were true positives:
  $$\text{Precision} = \frac{TP}{TP + FP}$$
  In spam filtering, precision is mission-critical; a low precision indicates that legitimate, critical emails are being misclassified as spam (False Positives), causing severe disruption to users.
- **Recall (Sensitivity):** The proportion of actual positive instances correctly identified:
  $$\text{Recall} = \frac{TP}{TP + FN}$$
  A decline in recall indicates that malicious or spam messages are leaking through into the primary inbox (False Negatives).
- **F1-Score:** The harmonic mean of precision and recall:
  $$\text{F1-Score} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

Tracking these metrics across sliding observation windows provides early indication of degradation. However, calculating ground-truth metrics requires access to verified labels, which are often subject to operational latency.

## 2.6 Data Drift Detection

**Data drift** (also termed *covariate shift*) refers to a change in the marginal probability distribution of the input features $P(\mathbf{X})$ over time, while the conditional probability distribution of the target given the features $P(Y \mid \mathbf{X})$ remains unchanged:
$$P_t(\mathbf{X}) \ne P_0(\mathbf{X}) \quad \text{while} \quad P_t(Y \mid \mathbf{X}) = P_0(Y \mid \mathbf{X})$$

In email spam filtering, data drift frequently manifests as changes in email lengths, shifting vocabulary, seasonal changes in topic distributions, or variations in HTML formatting. Because data drift can be evaluated without ground-truth labels ($Y$), it serves as a critical leading indicator of potential degradation.

Statistical hypothesis testing is the primary mechanism for detecting data drift. For continuous feature distributions, the non-parametric **two-sample Kolmogorov-Smirnov (KS) test** evaluates the null hypothesis $H_0$ that two independent samples are drawn from the same continuous underlying distribution. The KS statistic measures the supremum of the absolute distance between the empirical cumulative distribution functions (ECDFs) of the reference and current distributions:
$$D = \sup_x |F_{\text{ref}}(x) - F_{\text{curr}}(x)|$$

If the computed $p$-value falls below a pre-configured significance threshold (e.g., $\alpha = 0.05$), the null hypothesis is rejected, and feature data drift is flagged.

## 2.7 Concept Drift Detection

**Concept drift** refers to a fundamental shift in the statistical relationship between the input features $\mathbf{X}$ and the target variable $Y$, regardless of whether the input distribution $P(\mathbf{X})$ has changed:
$$P_t(Y \mid \mathbf{X}) \ne P_0(Y \mid \mathbf{X})$$

Concept drift in spam detection is inherently adversarial. Spammers continuously invent new evasion tactics, such as substituting obfuscated characters (e.g., "v!agra" instead of "viagra"), using homoglyphs, embedding text in images, and employing AI-assisted paraphrasing to ensure malicious emails mimic legitimate correspondence. Consequently, tokens and feature combinations that historically indicated legitimate emails may begin to correlate with spam campaigns.

Unlike data drift, true concept drift detection requires access to **ground-truth labels** ($Y$). Because production systems operate in real time, obtaining exhaustive ground-truth labels for every prediction is often impractical. Therefore, production MLOps architectures frequently employ **windowed performance tracking** as an operational proxy for concept drift: when classification metrics across sliding labeled validation batches drop significantly while input feature distributions remain relatively stable, concept drift is inferred.

## 2.8 Model Explainability in Operations

Explainable Artificial Intelligence (XAI) has attracted significant academic focus, primarily through local feature attribution frameworks such as SHAP (SHapley Additive exPlanations) and LIME (Local Interpretable Model-agnostic Explanations) [6]. While SHAP and LIME provide mathematical insights into individual model predictions, **operational explainability** addresses a different engineering challenge: explaining system-level model health and degradation.

In production engineering, explainability must maintain scientific integrity. Diagnostic systems must avoid claiming causal certainty where only observational correlation exists. For example, observing that feature data drift co-occurs with a drop in recall does not mathematically prove that the drifted feature caused the classification errors. A rigorous operational explainability layer must synthesize multi-source telemetry - health scores, performance trends, data drift tests, and concept drift indicators - into prioritized, human-interpretable evidence using precise non-causal associative phrasing.

## 2.9 Automated and Adaptive Decision Support

Traditional industrial monitoring platforms follow a simple alerting model: if a metric crosses a pre-configured threshold, an alert notification (via PagerDuty, Slack, or email) is dispatched to an on-call engineer. However, simple threshold alerts suffer from high false-alarm rates, alert fatigue, and lack of diagnostic context.

Decision Support Systems (DSS) transform raw operational telemetry into structured, prioritized maintenance guidance. In high-stakes enterprise applications, fully autonomous self-healing architectures (where models autonomously retrain and deploy into production without human sign-off) present unacceptable operational liabilities:
1. **Catastrophic Forgetting:** Autonomous retraining on narrow, drifted production batches can cause models to catastrophically forget edge cases and historically verified patterns.
2. **Adversarial Poisoning:** If an attacker recognizes that a system automatically retrains on incoming flagged data, they can deliberately poison the training pipeline by injecting misleading samples.
3. **Unverified Rollback Hazards:** Autonomous rollbacks triggered without verifying the health and structural compatibility of historical model artifacts can cause complete service outages.

Consequently, modern software engineering standards (IEEE Std 1016-2009 [4], ISO/IEC/IEEE 12207 [5]) dictate a strict **Human-in-the-Loop (HITL)** paradigm: the platform provides deterministic, explainable recommendations, but execution requires authorized human approval.

## 2.10 Comparative Analysis of Existing MLOps Tools

Table 2.2 contrasts traditional spam filters and existing MLOps tools against PhoenixML.

Table 2.2 - General Comparison of MLOps Approaches and PhoenixML

| Capability | Traditional Spam Filters | Standard MLOps Platforms (MLflow, Evidently) | Proposed PhoenixML Platform |
|:---|:---|:---|:---|
| **Monitoring Paradigm** | Isolated prediction counting | Passive metric dashboards and threshold alerts | Active multi-source telemetry and health assessment |
| **Statistical Drift Testing** | None | Feature drift tests (Evidently AI) | Integrated 2-sample KS data drift and windowed concept drift |
| **Model Health Scoring** | Single-metric (Accuracy) | Raw metric plots | Weighted composite scoring (0-100) with dynamic redistribution |
| **Operational Explainability** | None | Local Feature Attribution (SHAP) | Systemic Multi-Source Diagnostic Synthesis |
| **Decision Support** | None | None (Manual operator triage) | Deterministic AIMD recommendation engine |
| **Safety Governance** | Ad-hoc manual scripts | Manual script triggers | Strict HITL approval workflow with rollback safety invariants |
| **Decision Auditability** | None | None | Immutable PostgreSQL decision logs and state machine |

While tools such as Evidently AI offer excellent statistical drift detection and MLflow excels at artifact cataloging, they stop short of synthesizing evidence into actionable, policy-governed maintenance decisions.

## 2.11 Research Gap

The literature and tooling review reveals a clear research and engineering gap:
1. **Lack of Integrated Decision Engines:** Existing MLOps tools provide monitoring data but lack a formal decision engine to evaluate multi-factor telemetry.
2. **Absence of Standardized Health Policies:** Most monitoring platforms report raw metrics independently, lacking a normalized composite health score that handles missing metrics gracefully.
3. **Disconnected Operational Governance:** Drift detection, model registries, and maintenance decisions reside in fragmented silos without a unified, auditable human-in-the-loop approval workflow.

## 2.12 Chapter Summary

This chapter reviewed the challenges of machine learning in production, focusing on the vulnerabilities of spam email detection models to data drift and concept drift. It highlighted the limitations of passive monitoring platforms and established the necessity of human-in-the-loop decision-support systems. PhoenixML bridges this operational gap by synthesizing multi-source telemetry into explainable, policy-governed maintenance recommendations.

---

\\newpage


# CHAPTER 3 - SYSTEM ARCHITECTURE & DESIGN

## 3.1 Existing System Overview & Operational Deficiencies

In conventional machine learning deployments, model management and maintenance typically rely on fragmented, ad-hoc operational processes. A machine learning model is trained offline using historical training corpora (such as the Enron or LingSpam email datasets), evaluated against static cross-validation splits, serialized into binary artifacts (e.g., pickle, ONNX, or Joblib files), and wrapped in a web service for real-time inference.

Monitoring in these environments is predominantly passive. Operational teams configure generic infrastructure monitoring tools (such as Prometheus, Grafana, Datadog, or ELK stacks) to record system-level performance indicators, including HTTP request volume, CPU and memory utilization, and 95th-percentile inference latency. Where model-specific metrics are recorded, they are typically limited to simple aggregated prediction counters or periodic script-based evaluations against manually curated test sets.

This operational paradigm suffers from several profound technical deficiencies:
1. **Passive Alerting Without Guidance:** Existing tools generate alert notifications when hardcoded metric thresholds are breached (e.g., "Accuracy < 80%"). However, they provide no actionable guidance regarding the appropriate operational response, forcing engineers to manually diagnose complex root causes.
2. **Decoupled Analytical Signals:** In typical production setups, data drift detection (if implemented at all) runs as an isolated, asynchronous batch job; performance metrics are plotted on separate dashboards; and model registry metadata resides in a disconnected repository. There is no automated synthesis connecting an input distribution shift to an observed performance drop.
3. **Cognitive Overload and Alert Fatigue:** High-frequency, noisy alerts generated by multiple independent monitoring rules lead to alert fatigue. Operational teams frequently ignore warnings until acute classification failures cause significant disruption.
4. **Ad-Hoc, Unaudited Maintenance Decisions:** Maintenance interventions (such as retraining a model or rolling back to an older version) are typically executed via ad-hoc command-line scripts without a formal, auditable record detailing why the intervention was initiated, who approved it, and what telemetry justified the action.
5. **Absence of Safety Guardrails:** Ad-hoc manual rollbacks run the severe risk of pointing production traffic to nonexistent, corrupted, or incompatible model artifacts because rollback targets are not systematically verified against registry state.

## 3.2 Proposed System: PhoenixML

To resolve these limitations, **PhoenixML** introduces an integrated, intelligent MLOps decision-support platform. The proposed system acts as an operational supervision layer that continuously observes deployed machine learning models, evaluates their performance, detects statistical distribution shifts, computes composite health ratings, synthesizes diagnostic explanations, and generates policy-governed maintenance recommendations.

### Key Innovations of PhoenixML:
- **Unified Multi-Source Telemetry Ingestion:** A centralized, relational repository for model metadata, runtime prediction observations, and performance metrics.
- **Dual Drift Detection Engines:** Integrated two-sample Kolmogorov-Smirnov tests for continuous feature data drift and sliding labeled-window comparisons for concept drift proxies.
- **Weighted Multi-Factor Health Assessment:** A robust mathematical health policy that combines classification metrics into a normalized 0-100 score, dynamically redistributing weights for missing metrics to prevent false zero-score penalties.
- **Operational Explainability Layer:** Deterministic synthesis of diagnostic signals into structured, prioritized, human-interpretable evidence summaries.
- **Adaptive Intelligent Model Decision (AIMD) Engine:** A policy-driven engine that recommends six distinct, structured operational actions based on multi-source evidence.
- **Strict Human-in-the-Loop (HITL) Governance:** Complete elimination of unconstrained autonomous production actions. Every recommendation enforces `requires_human_approval = True` and is governed by an auditable approval state machine.
- **Rollback Safety Invariants:** Verification of historical model registry state before permitting rollback recommendations, preventing production outages.

## 3.3 Functional Requirements Specification

The functional requirements define the core operational capabilities that PhoenixML must provide. These are formalized in Table 3.1.

Table 3.1 - Functional Requirements Specification

| Requirement ID | Module | Description | Priority |
|:---|:---|:---|:---|
| **FR-01** | Authentication | The system shall authenticate users via OAuth2 password credentials and issue signed JWT access and refresh tokens. | Critical |
| **FR-02** | User Management | The system shall enforce Role-Based Access Control (RBAC) across three distinct user tiers (`ADMIN`, `ML_ENGINEER`, `VIEWER`). | Critical |
| **FR-03** | Model Registry | The system shall provide CRUD management for spam detection models, storing algorithm, framework, deployment status, and owner. Model version designations are identified via model naming conventions and context dictionaries. | High |
| **FR-04** | Telemetry Ingestion | The system shall ingest and validate runtime monitoring observations containing prediction counts and classification metrics (accuracy, precision, recall, F1). | High |
| **FR-05** | Performance Analysis| The system shall evaluate chronological performance trajectories across observations, detecting degradation exceeding configurable thresholds (default 0.05). | High |
| **FR-06** | Data Drift Detection | The system shall execute two-sample Kolmogorov-Smirnov tests between reference and current feature distributions, outputting KS statistics and p-values. | High |
| **FR-07** | Concept Drift Detection| The system shall compare classification metrics across labeled reference and current windows, detecting performance drops exceeding degradation thresholds. | High |
| **FR-08** | Health Assessment | The system shall evaluate a composite 0-100 health score using weighted metrics (F1: 40%, Precision: 25%, Recall: 25%, Accuracy: 10%) with dynamic weight redistribution. | Critical |
| **FR-09** | Explainability Layer | The system shall synthesize health, performance, data drift, and concept drift observations into structured diagnostic summaries and prioritized primary factors. | High |
| **FR-10** | AIMD Decision Engine | The system shall evaluate multi-factor operational signals against deterministic decision rules, generating structured maintenance recommendations. | Critical |
| **FR-11** | Rollback Safety | The system shall verify the existence and viability of a stable rollback target in model registry context before recommending a `ROLLBACK` action. | Critical |
| **FR-12** | Decision Persistence | The system shall persist all generated recommendations into an immutable `decision_logs` table with `requires_human_approval = True`. | Critical |
| **FR-13** | Approval Workflow | The system shall enforce an auditable approval state machine (`PENDING` -> `APPROVED` / `REJECTED`) restricted by RBAC and ownership. | Critical |
| **FR-14** | Operator Dashboard | The system shall provide consolidated fleet-wide and model-specific telemetry dashboards, KPI summaries, and interactive approval cards. | High |
| **FR-15** | Decision History API | The system shall expose paginated, chronological decision audit trails supporting historical compliance and operational review. | High |

## 3.4 Non-Functional Requirements Specification

The quality attributes and architectural constraints governing PhoenixML are defined in Table 3.2.

Table 3.2 - Non-Functional Requirements Specification

| Requirement ID | Category | Metric / Specification | Priority |
|:---|:---|:---|:---|
| **NFR-01** | Performance | API response latency for telemetry queries and dashboard summaries shall be $\le 2.0$ seconds under standard operational loads. | High |
| **NFR-02** | Evaluation Latency | On-demand AIMD evaluation across monitoring observations shall execute and persist recommendations within $\le 15.0$ seconds. | High |
| **NFR-03** | Data Integrity | All database transactions shall adhere strictly to ACID properties. Cascading deletes shall prevent orphaned telemetry and decision records. | Critical |
| **NFR-04** | Immutability | Persisted decision logs, analytical evidence payloads, rationales, and timestamps shall be strictly immutable post-creation. | Critical |
| **NFR-05** | Security | User passwords shall be hashed using salted bcrypt. All protected endpoints shall validate signed, non-expired JWT tokens. | Critical |
| **NFR-06** | Modularity | Core analytical modules (Health, Performance, Drift, Explainability, AIMD) shall be completely decoupled from web and persistence frameworks. | High |
| **NFR-07** | Extensibility | The architecture shall support extension to multi-model fleets and non-spam machine learning domains without database redesign. | Medium |
| **NFR-08** | Reliability | The system shall handle missing, zero, NaN, and infinite numerical values gracefully without application crashes. | High |
| **NFR-09** | Approval State Integrity | The system shall enforce immutable state transitions (`PENDING` -> `APPROVED`/`REJECTED`) via RBAC. Granular reviewer foreign key and timestamp logging is planned for future audit enhancements. | High |
| **NFR-10** | Usability | The operator frontend shall provide an intuitive dark-mode interface with distinct visual indicators for model health and approval states. | Medium |

## 3.5 User Roles and Access Permissions

PhoenixML defines three distinct user personas under its Role-Based Access Control (RBAC) architecture, detailed in Table 3.3.

Table 3.3 - Role-Based Access Control (RBAC) Matrix

| Operational Capability | Administrator (`ADMIN`) | ML Engineer (`ML_ENGINEER`) | Viewer (`VIEWER`) |
|:---|:---:|:---:|:---:|
| **User Account Management** | Read / Write | Denied (403) | Denied (403) |
| **System-Wide Telemetry Inspection** | Full Global Scope | Own Models Only | Own Models Only |
| **Register / Update Model Metadata** | Permitted (Global) | Permitted (Owned Models) | Denied (403) |
| **Ingest Monitoring Observations** | Permitted (Global) | Permitted (Owned Models) | Denied (403) |
| **Trigger AIMD Evaluation** | Permitted (Global) | Permitted (Owned Models) | Denied (403) |
| **Approve / Reject Recommendations**| Permitted (Global) | Permitted (Owned Models) | Denied (403) |
| **Inspect Decision History** | Permitted (Global) | Permitted (Owned Models) | Permitted (Owned Models)|
| **Access Interactive Dashboard** | Full Access | Full Access | Read-Only |

## 3.6 Use Case Specifications

### UC-1: User Authentication and Session Initialization
- **Primary Actor:** Administrator, ML Engineer, Viewer.
- **Preconditions:** Registered user account exists in database.
- **Main Flow:** User posts credentials to `/api/auth/login`. System validates hash via bcrypt and returns JWT access and refresh tokens. Client initializes session and loads dashboard.
- **Postconditions:** Authenticated session established with assigned role permissions.

### UC-2: Model Registration
- **Primary Actor:** ML Engineer, Administrator.
- **Preconditions:** User is authenticated with `ADMIN` or `ML_ENGINEER` privileges.
- **Main Flow:** User submits model metadata (name, description, framework, algorithm, initial deployment status) to `/api/spam-models`. System assigns unique UUID, associates record with user's ID as owner, and sets status to `DEVELOPMENT`.
- **Postconditions:** Model registered in PostgreSQL and visible in dashboard inventory.

### UC-3: Monitoring Telemetry Ingestion
- **Primary Actor:** External Production Service / ML Engineer.
- **Preconditions:** Registered model exists in active state.
- **Main Flow:** Telemetry payload posted to `/api/spam-models/{id}/monitoring` containing prediction counts, spam/ham distributions, and optional performance metrics. System validates schema via Pydantic and commits record.
- **Postconditions:** Observation saved in `monitoring_observations` table with UTC timestamp.

### UC-4: On-Demand AIMD Model Evaluation
- **Primary Actor:** ML Engineer, Administrator.
- **Preconditions:** Model has at least one monitoring observation record.
- **Main Flow:** User triggers evaluation via `/api/spam-models/{id}/decisions/evaluate`. System retrieves chronological observations, runs performance analysis, evaluates data and concept drift, computes composite health score, synthesizes explainability findings, and runs AIMD decision rules. A recommendation is generated with `requires_human_approval = True` and persisted in `decision_logs` with status `PENDING`.
- **Postconditions:** Recommendation stored and displayed on dashboard for review.

### UC-5: Human Review and Decision Approval
- **Primary Actor:** Authorized ML Engineer (Model Owner) or Administrator.
- **Preconditions:** A decision record exists in `PENDING` state.
- **Main Flow:** User inspects recommendation narrative and evidence summary on the dashboard, clicking either "Approve" or "Reject". System validates role and ownership, verifies state transition invariants, and updates `approval_status` to `APPROVED` or `REJECTED`.
- **Postconditions:** Decision status updated; further modifications strictly prohibited.

## 3.7 Architectural Principles & Domain Decoupling

The architectural design of PhoenixML is rooted in established software engineering literature, specifically the principles of modular decomposition and separation of concerns articulated by Bass et al. [11] and Richards & Ford [12].

A paramount architectural achievement of PhoenixML is the **domain-focused decoupling of its core analytical engines**. In many contemporary web-based data science prototypes, statistical routines and analytical evaluation logic are tightly coupled with web framework request objects (such as FastAPI `Request` or Flask `g`), database ORM models, and active database sessions. This anti-pattern introduces severe liabilities: testing requires mocking complex database states and HTTP contexts, execution latency increases, and analytical algorithms cannot be easily reused in batch jobs or streaming workers.

In PhoenixML, the six core analytical components:
1. `HealthAssessor` (`backend/app/monitoring/health.py`)
2. `PerformanceAnalyzer` (`backend/app/monitoring/performance.py`)
3. `DataDriftDetector` (`backend/app/monitoring/data_drift.py`)
4. `ConceptDriftDetector` (`backend/app/monitoring/concept_drift.py`)
5. `ExplainabilityAnalyzer` (`backend/app/monitoring/explainability.py`)
6. `AIMDDecisionEngine` (`backend/app/decisions/aimd.py`)

are engineered as **pure domain logic components**. They operate exclusively on standard Python data structures and validated Pydantic models. They maintain:
- **Zero Web Dependencies:** Completely free of FastAPI, Starlette, HTTP headers, request handlers, or response objects.
- **Zero Persistence Dependencies:** Completely free of SQLAlchemy ORM models, database engines, database sessions, and SQL transactions.
- **Zero Framework Side-Effects:** Analytical calculations are purely functional, deterministic, and idempotent.

### Architectural Benefits of Domain Decoupling:
- **Exceptional Testability:** Analytical rules, mathematical formulas, drift statistics, and decision matrices can be verified with high-speed unit tests without starting database engines or mocking network connections.
- **High Maintainability:** Upgrading web frameworks (e.g., migrating FastAPI versions) or altering persistence schemas (e.g., modifying database tables) requires zero modifications to the core scientific algorithms.
- **Reusability Across Contexts:** The exact same `AIMDDecisionEngine` and `DataDriftDetector` classes can be executed inside REST handlers, batch CLI utilities, offline Jupyter validation notebooks, or background worker processes without modification.
- **Strict Separation of Concerns:** Service layers handle transaction management and authorization, while domain modules focus exclusively on analytical calculations.

## 3.8 System Architecture & Primary Components

PhoenixML follows a modular, layered architectural style [11, 12], dividing responsibilities into distinct presentation, API, service, analytical, and persistence layers.

```
+-------------------------------------------------------------------------+
|                       PRESENTATION TIER (Browser)                       |
|   React 18 Single Page Application (SPA) - Dark-Mode Operator Dashboard  |
|   Components: KPIGrid | HealthMeter | DecisionReviewBox | Tables        |
+-------------------------------------------------------------------------+
                                     │  HTTPS / JSON REST
                                     ▼
+-------------------------------------------------------------------------+
|                        API & ROUTING TIER (FastAPI)                     |
|   Routers: /api/auth | /api/users | /api/spam-models | /api/dashboard   |
|   Middleware: CORS, Exception Handlers, Pydantic Request Validation     |
+-------------------------------------------------------------------------+
                                     │  Dependency Injection
                                     ▼
+-------------------------------------------------------------------------+
|                         SERVICE & SECURITY TIER                         |
|   AuthService (JWT/Bcrypt) | RBAC Policy Enforcer (require_roles)       |
|   ModelService | MonitoringService | DecisionService | DashboardService |
+-------------------------------------------------------------------------+
                                     │  Clean In-Memory Payloads
                                     ▼
+-------------------------------------------------------------------------+
|                   PURE DOMAIN ANALYTICAL ENGINES (Decoupled)            |
|   HealthAssessor | PerformanceAnalyzer | DataDriftDetector              |
|   ConceptDriftDetector | ExplainabilityAnalyzer | AIMDDecisionEngine    |
+-------------------------------------------------------------------------+
                                     │  SQLAlchemy 2.0 ORM
                                     ▼
+-------------------------------------------------------------------------+
|                         PERSISTENCE TIER (PostgreSQL)                   |
|   Relational Tables: users | registered_models                          |
|                      monitoring_observations | decision_logs            |
+-------------------------------------------------------------------------+
```

Figure 3.1 - PhoenixML High-Level Layered Architecture

Figure 3.2 illustrates the collaboration between components during runtime evaluation:

```
[Operator / API Client] 
       │ 
       ▼ (1) POST /api/spam-models/{id}/decisions/evaluate
[Decision Router] 
       │ 
       ▼ (2) Enforce RBAC & Model Ownership
[Decision Service] 
       ├───► (3) Fetch Historical Observations ───► [Monitoring Repository] ───► [PostgreSQL]
       │
       ├───► (4) Compute Performance Trends    ───► [PerformanceAnalyzer]
       ├───► (5) Evaluate Health Score         ───► [HealthAssessor]
       ├───► (6) Evaluate Data Drift           ───► [DataDriftDetector]
       ├───► (7) Evaluate Concept Drift        ───► [ConceptDriftDetector]
       ├───► (8) Synthesize Explanations       ───► [ExplainabilityAnalyzer]
       │
       ▼ (9) Evaluate Multi-Factor Context
[AIMD Decision Engine] ──► Generates Recommendation (requires_human_approval = True)
       │
       ▼ (10) Persist Recommendation Record (Status: PENDING)
[Decision Repository] ───► [PostgreSQL (decision_logs)]
       │
       ▼ (11) Return 201 Created with Structured Recommendation
[Operator / UI Client]
```

Figure 3.2 - Component Collaboration and Evaluation Pipeline

## 3.9 Single-Port Web Serving Architecture

In enterprise and production setups, frontend single-page applications are commonly built using Node.js toolchains and hosted on external reverse proxies (such as Nginx, Apache, or Cloudflare CDN) that route API calls to backend microservices. However, for academic demonstration, evaluation, and simplified local deployment, this multi-port configuration introduces unnecessary operational overhead, CORS misconfigurations, and environment setup friction.

PhoenixML implements a **single-port embedded web serving architecture**:
- The FastAPI application utilizes Starlette's `StaticFiles` handler to mount the production frontend directory directly on `/ui`:
  ```python
  frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
  if frontend_dir.is_dir():
      app.mount("/ui", StaticFiles(directory=str(frontend_dir), html=True), name="ui")
  ```
- The application defines a dedicated root redirect handler on `/`:
  ```python
  @app.get("/", include_in_schema=False)
  def root_redirect():
      return RedirectResponse(url="/ui/")
  ```
- All REST API endpoints are namespaced cleanly under `/api/` (e.g., `/api/auth`, `/api/spam-models`, `/api/dashboard`), ensuring zero routing collisions between dynamic API endpoints and static assets.
- Cross-Origin Resource Sharing (CORS) middleware is configured to allow both local standalone frontend development (e.g., Node.js live servers) and embedded static serving.

This architecture enables users, evaluators, and academic reviewers to launch the entire platform - API, interactive Swagger documentation (`/docs`), and full operator dashboard (`/ui/`) - using a single Uvicorn server command on a single port (`http://localhost:8000`), completely eliminating external web server dependencies.

## 3.10 High-Level Decision Workflow

Figure 3.3 presents the operational decision workflow executed by PhoenixML:

```
+-------------------------------------------------------------------------+
|                  1. TELEMETRY INGESTION & AGGREGATION                   |
|   Ingest runtime predictions, accuracy, precision, recall, and F1       |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                     2. MULTI-FACETED ANALYSIS                           |
|   ├── Health Assessment: Calculate weighted health score (0-100)        |
|   ├── Performance Trend: Compare sliding observation windows            |
|   ├── Data Drift: Two-sample KS-test on continuous feature distributions|
|   └── Concept Drift: Compare performance across labeled test windows    |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                    3. OPERATIONAL EXPLAINABILITY                        |
|   Synthesize health, drift, and performance into prioritized signals    |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                   4. DETERMINISTIC AIMD EVALUATION                      |
|   Evaluate deterministic rules against synthesized evidence context     |
|   Assign action, urgency priority, evidence confidence, and rationale   |
|   Enforce Rollback Safety Invariant & requires_human_approval = True    |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                     5. DECISION LOG PERSISTENCE                         |
|   Commit recommendation to PostgreSQL decision_logs table               |
|   Initial state: approval_status = PENDING                              |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                  6. HUMAN OPERATOR REVIEW (HITL)                        |
|   Operator reviews rationale, health score, and signals on dashboard    |
|   Operator clicks: [ APPROVE ] or [ REJECT ]                            |
|   System transitions state: PENDING -> APPROVED / REJECTED              |
+-------------------------------------------------------------------------+
```

Figure 3.3 - PhoenixML High-Level Decision Workflow

## 3.11 Database Architecture & Relational Schema

Following relational database design best practices articulated by Elmasri & Navathe [13], PhoenixML utilizes PostgreSQL to guarantee ACID compliance, relational integrity, and long-term auditability.

```
       +-----------------------+
       |         users         |
       +-----------------------+
       | id (UUID, PK)         |
       | email (VARCHAR, UQ)   |
       | username (VARCHAR, UQ)|
       | role (VARCHAR)        |
       | is_active (BOOL)      |
       +-----------------------+
                   │ 1
                   │
                   │ owns (1:N)
                   ▼ N
       +-----------------------+
       |   registered_models   |
       +-----------------------+
       | id (UUID, PK)         |
       | name (VARCHAR)        |
       | framework (VARCHAR)   |
       | algorithm (VARCHAR)   |
       | status (VARCHAR)      |
       | owner_id (UUID, FK)   |
       +-----------------------+
             │ 1             │ 1
             │               │
     has (1:N)      evaluates (1:N)
             │               │
             ▼ N             ▼ N
+-------------------------+  +----------------------------+
| monitoring_observations |  |       decision_logs        |
+-------------------------+  +----------------------------+
| id (UUID, PK)           |  | id (UUID, PK)              |
| model_id (UUID, FK)     |  | model_id (UUID, FK)        |
| observed_at (TIMESTAMPTZ|  | created_at (TIMESTAMPTZ)   |
| accuracy (FLOAT)        |  | health_score (FLOAT)       |
| precision (FLOAT)       |  | health_status (VARCHAR)    |
| recall (FLOAT)          |  | recommended_action (ENUM)  |
| f1_score (FLOAT)        |  | priority (ENUM)            |
| prediction_count (INT)  |  | confidence (FLOAT)         |
+-------------------------+  | rationale (TEXT)           |
                             | explanation (TEXT)         |
                             | supporting_signals (JSON)  |
                             | req_human_approval (BOOL)  |
                             | approval_status (ENUM)     |
                             +----------------------------+
```

Figure 3.4 - Entity Relationship Diagram (ERD) of Database Schema

Tables 3.4 through 3.7 provide the physical database schema specifications.

Table 3.4 - Database Schema Specifications: `users`

| Column Name | Data Type | Constraints | Description |
|:---|:---|:---|:---|
| `id` | UUID | Primary Key, default UUIDv4 | Unique user account identifier |
| `full_name` | VARCHAR(255) | NOT NULL | User's full display name |
| `email` | VARCHAR(255) | UNIQUE, INDEX, NOT NULL | User's registered email address |
| `username` | VARCHAR(255) | UNIQUE, INDEX, NOT NULL | Unique login handle |
| `hashed_password` | VARCHAR(255) | NOT NULL | Salted bcrypt password hash |
| `role` | VARCHAR(50) | NOT NULL, default 'VIEWER' | User role (`ADMIN`, `ML_ENGINEER`, `VIEWER`) |
| `is_active` | BOOLEAN | NOT NULL, default TRUE | Active account flag |
| `is_verified` | BOOLEAN | NOT NULL, default FALSE | Email verification status |
| `created_at` | TIMESTAMPTZ | NOT NULL, default `now()` | Account creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL, default `now()` | Account modification timestamp |
| `last_login` | TIMESTAMPTZ | NULLABLE | Timestamp of most recent authentication |

Table 3.5 - Database Schema Specifications: `registered_models`

| Column Name | Data Type | Constraints | Description |
|:---|:---|:---|:---|
| `id` | UUID | Primary Key, default UUIDv4 | Unique registered model identifier |
| `name` | VARCHAR(255) | INDEX, NOT NULL | Model identifier name (e.g., `SpamGuard-v1`) |
| `description` | VARCHAR(1000) | NULLABLE | Model functional description |
| `framework` | VARCHAR(50) | NOT NULL | Framework (e.g., scikit-learn, PyTorch) |
| `algorithm` | VARCHAR(100) | NULLABLE | Specific classification algorithm |
| `status` | VARCHAR(50) | NOT NULL, default 'DEVELOPMENT' | Status (`DEVELOPMENT`, `ACTIVE`, `ARCHIVED`) |
| `owner_id` | UUID | Foreign Key (`users.id`, CASCADE), INDEX | Owner user identifier |
| `created_at` | TIMESTAMPTZ | NOT NULL, default `now()` | Registration timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL, default `now()` | Metadata modification timestamp |

*Note: The `registered_models` table does not utilize an isolated relational column for versioning; model version designations (such as v1, v2) are identified via model naming conventions and contextual metadata.*

Table 3.6 - Database Schema Specifications: `monitoring_observations`

| Column Name | Data Type | Constraints | Description |
|:---|:---|:---|:---|
| `id` | UUID | Primary Key, default UUIDv4 | Unique observation identifier |
| `model_id` | UUID | Foreign Key (`registered_models.id`, CASCADE), INDEX | Associated registered model |
| `observed_at` | TIMESTAMPTZ | NOT NULL | Observation collection interval timestamp |
| `prediction_count` | INTEGER | NOT NULL, default 0 | Total classification predictions in window |
| `positive_prediction_count`| INTEGER | NOT NULL, default 0 | Positive (spam) predictions in window |
| `negative_prediction_count`| INTEGER | NOT NULL, default 0 | Negative (ham) predictions in window |
| `accuracy` | FLOAT | NULLABLE | Measured classification accuracy |
| `precision` | FLOAT | NULLABLE | Measured classification precision |
| `recall` | FLOAT | NULLABLE | Measured classification recall |
| `f1_score` | FLOAT | NULLABLE | Measured classification F1-score |

Table 3.7 - Database Schema Specifications: `decision_logs`

| Column Name | Data Type | Constraints | Description |
|:---|:---|:---|:---|
| `id` | UUID | Primary Key, default UUIDv4 | Unique decision log record identifier |
| `model_id` | UUID | Foreign Key (`registered_models.id`, CASCADE), INDEX | Associated registered model |
| `created_at` | TIMESTAMPTZ | NOT NULL, default `now()` | Recommendation generation timestamp |
| `health_score` | FLOAT | NULLABLE, Range [0.0, 100.0] | Composite health score at decision time |
| `health_status` | VARCHAR(50) | NULLABLE | Health classification string |
| `recommended_action`| VARCHAR(50) | NOT NULL (Enum `aimdaction`) | Recommended maintenance action |
| `priority` | VARCHAR(50) | NOT NULL (Enum `aimdpriority`) | Urgency priority level |
| `confidence` | FLOAT | NULLABLE, Range [0.0, 1.0] | Normalized evidence confidence score |
| `rationale` | TEXT | NOT NULL | Deterministic human justification narrative |
| `explanation` | TEXT | NULLABLE | Diagnostic summary from explainability layer |
| `supporting_signals`| JSON | NULLABLE | Raw analytical signal payload list |
| `requires_human_approval` | BOOLEAN | NOT NULL, default TRUE | Invariant HITL enforcement flag |
| `approval_status` | VARCHAR(50) | NOT NULL, default 'PENDING' | Status (`PENDING`, `APPROVED`, `REJECTED`) |

## 3.12 Security & Authentication Architecture

PhoenixML adheres to the REST architectural style formulated by Fielding [14] and standardized under RFC 9110 [16]. Security is enforced across all operational layers:
- **Credential Protection:** User passwords submitted during account registration are never stored in plaintext. They are salted and hashed using the bcrypt cryptographic algorithm via Passlib with automatic salt generation and computational work factors.
- **Stateless Token Authentication:** Following RFC 7519 [15], authentication is managed via JSON Web Tokens (JWT). Upon successful credential verification, the authentication service issues an access token (signed using HMAC-SHA256 with a short expiration lifespan of 15-30 minutes) and a long-lived refresh token.
- **Role-Based Authorization:** FastAPI dependency injection enforces RBAC. Protected routes invoke `require_roles(*allowed_roles)`, verifying token signatures, subject identity, expiration timestamps, and role entitlements prior to executing endpoint logic.
- **Tenant & Ownership Scoping:** While `ADMIN` users possess global read/write visibility, `ML_ENGINEER` users are strictly scoped to models they own (`model.owner_id == current_user.id`). Any attempt by an engineer to evaluate, ingest telemetry for, or approve decisions on another engineer's model results in an immediate HTTP 403 Forbidden exception.

## 3.13 Chapter Summary

This chapter detailed the system architecture and design of PhoenixML. It analyzed existing operational deficiencies, formalized functional and non-functional requirements, and detailed the RBAC matrix. The chapter highlighted the foundational domain-focused decoupling of the analytical engines, single-port web serving via FastAPI static mounts, physical PostgreSQL schema specifications, and stateless JWT security architecture.

---

\\newpage


# CHAPTER 4 - MONITORING, DRIFT DETECTION & EXPLAINABILITY

## 4.1 Overview of the Analytical Pipeline

In a resilient production MLOps platform, monitoring cannot be restricted to passive counting of API invocations or recording static latency percentiles. To protect operational reliability in spam email detection, an intelligent platform must observe, quantify, and interpret degradation across three complementary analytical dimensions:
1. **Classification Performance & Trajectory:** Tracking empirical accuracy, precision, recall, and F1-score across chronological observation intervals.
2. **Distributional Drift Detection:** Identifying input covariate shifts (data drift) via statistical hypothesis testing and detecting predictive mapping degradation (concept drift) via labeled window comparisons.
3. **Multi-Metric Health Scoring & Operational Diagnostics:** Synthesizing isolated metrics into a normalized composite health rating and translating multi-source telemetry into prioritized, human-interpretable explanations.

Figure 4.1 illustrates the analytical data flow through the monitoring, drift detection, and explainability subsystems.

```
+-------------------------------------------------------------------------+
|                  RUNTIME TELEMETRY INGESTION PIPELINE                   |
|   Observations: Observed At, Prediction Counts, Metrics (Acc, P, R, F1)|
+-------------------------------------------------------------------------+
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
+------------------+       +-------------------+       +------------------+
| PERFORMANCE      |       | DATA DRIFT        |       | CONCEPT DRIFT    |
| ANALYZER         |       | DETECTOR          |       | DETECTOR         |
| Windowed metric  |       | Two-Sample KS-Test|       | Labeled window   |
| trajectories     |       | on continuous     |       | delta tracking   |
| (Threshold: 0.05)|       | features (a=0.05) |       | (Threshold: 0.05)|
+------------------+       +-------------------+       +------------------+
         │                           │                           │
         └───────────────────────────┼───────────────────────────┘
                                     ▼
                   +-----------------------------------+
                   |         HEALTH ASSESSOR           |
                   | Normalized composite score (0-100)|
                   | Dynamic weight redistribution     |
                   | Status: HEALTHY/WARNING/CRITICAL  |
                   +-----------------------------------+
                                     │
                                     ▼
                   +-----------------------------------+
                   |     EXPLAINABILITY ANALYZER       |
                   | Severity & category prioritization|
                   | Primary factor extraction         |
                   | Non-causal associative diagnostics|
                   +-----------------------------------+
                                     │
                                     ▼
                   +-----------------------------------+
                   | Consolidated Analytical Evidence  |
                   |   (Supplied to AIMD Engine)       |
                   +-----------------------------------+
```

Figure 4.1 - PhoenixML Analytical Monitoring & Explainability Pipeline

## 4.2 Telemetry Ingestion Subsystem

The telemetry ingestion subsystem provides a structured REST interface for recording operational classification observations. In production spam filtering, observations are typically aggregated over sliding operational windows (e.g., hourly batches or daily monitoring cycles) by external ingestion scripts or message consumer workers.

Each observation submitted to `/api/spam-models/{id}/monitoring` conforms to a strict Pydantic validation schema:
- `observed_at`: An ISO 8601 UTC timestamp identifying the collection window.
- `prediction_count`: Total number of email classifications executed within the window.
- `positive_prediction_count`: Number of emails classified as spam ($y_{\text{pred}} = 1$).
- `negative_prediction_count`: Number of emails classified as legitimate ham ($y_{\text{pred}} = 0$).
- `accuracy`, `precision`, `recall`, `f1_score`: Floating-point metrics $\in [0.0, 1.0]$ computed against verified sample labels.

The ingestion handler validates that counts are non-negative and mathematically consistent ($P_{\text{pos}} + P_{\text{neg}} = P_{\text{total}}$), ensures floating-point metrics are sanitized of `NaN` or infinite values, verifies model ownership, and persists the record into the `monitoring_observations` table.

## 4.3 Performance Trajectory Analysis

Single-point metric inspections fail to capture whether a model is experiencing sudden catastrophic collapse or gradual chronic deterioration. PhoenixML implements a chronological **Performance Trend Analyzer** (`backend/app/monitoring/performance.py`).

Given a chronologically ordered sequence of observations $\mathcal{O} = \{o_1, o_2, \dots, o_n\}$ for a registered model, the analyzer compares the most recent observation $o_n$ against the preceding baseline observation $o_{n-1}$ (or a sliding window baseline average). For each monitored metric $m \in \{\text{accuracy}, \text{precision}, \text{recall}, \text{f1\_score}\}$, the metric delta is calculated:
$$\Delta_m = m_{\text{current}} - m_{\text{baseline}}$$

Performance state is categorized according to configurable degradation thresholds:
- **`DEGRADED`:** If any key metric drops by more than the threshold:
  $$\Delta_m \le -\tau_{\text{perf}} \quad (\text{default } \tau_{\text{perf}} = 0.05)$$
  The specific deteriorated metrics are appended to `degraded_metrics`.
- **`IMPROVING`:** If metrics demonstrate positive gains exceeding the threshold ($\Delta_m \ge +\tau_{\text{perf}}$).
- **`STABLE`:** If metric variations remain within $[-\tau_{\text{perf}}, +\tau_{\text{perf}}]$.
- **`INSUFFICIENT_DATA`:** If fewer than two observations are available, precluding trajectory calculation.

## 4.4 Model Health Assessment Methodology

Rather than evaluating classification health through a single unweighted metric such as accuracy, PhoenixML implements an explicit, configurable **Health Score Policy** (`backend/app/monitoring/health.py`).

### Metric Weightings and Operational Rationale
In spam email detection, precision and recall represent competing operational priorities: false positives alienate users by quarantining vital business emails, while false negatives breach security by admitting malware and scams into user inboxes. The composite health score balances these priorities as specified in Table 4.1.

Table 4.1 - Health Score Metric Weightings and Operational Rationale

| Metric | Configured Weight | Operational Rationale in Spam Filtering |
|:---|:---:|:---|
| **F1-Score** | 0.40 | Primary harmonic balance between precision and recall on class-imbalanced email streams. |
| **Precision** | 0.25 | Critical protection against False Positives (legitimate emails misclassified as spam). |
| **Recall** | 0.25 | Ensures detection efficacy against incoming spam messages (avoiding False Negatives). |
| **Accuracy** | 0.10 | General metric; weighted lowest due to vulnerability to class imbalance inflation. |

### Mathematical Normalization and Dynamic Redistribution
Each available metric $m_i \in [0.0, 1.0]$ is normalized to a 0-100 scale:
$$\bar{m}_i = m_i \times 100.0$$

In production environments, specific metrics may be temporarily unavailable (e.g., when precision is undefined due to zero positive predictions in a batch). PhoenixML enforces an explicit **Dynamic Redistribution Policy**: missing metrics are never treated as zero, which would artificially penalize model health. Instead, the weight of missing metrics is redistributed proportionally among the available metrics:
$$w_i^{\text{effective}} = \frac{w_i}{\sum_{j \in \mathcal{M}_{\text{avail}}} w_j}$$
$$\text{Health Score} = \sum_{i \in \mathcal{M}_{\text{avail}}} \bar{m}_i \times w_i^{\text{effective}}$$

The resulting score is clamped to $[0.0, 100.0]$ and categorized according to configurable status boundaries, detailed in Table 4.2.

Table 4.2 - Health Status Classification Boundaries

| Health Status | Score Range | Operational Meaning |
|:---|:---:|:---|
| `HEALTHY` | $\text{Score} \ge 80.0$ | Model operates within acceptable performance tolerances. |
| `WARNING` | $60.0 \le \text{Score} < 80.0$ | Moderate operational degradation detected; diagnostic review warranted. |
| `CRITICAL` | $\text{Score} < 60.0$ | Severe operational degradation; immediate maintenance intervention required. |
| `INSUFFICIENT_DATA` | $\text{Score} = \text{None}$ | Zero valid metrics available; health score cannot be evaluated. |

## 4.5 Statistical Data Drift Detection Design

Data drift detection evaluates changes in feature distributions without requiring ground-truth labels. PhoenixML implements the non-parametric **two-sample Kolmogorov-Smirnov (KS) test** from `scipy.stats.ks_2samp` (`backend/app/monitoring/data_drift.py`).

### Analytical Policy and Thresholds:
1. **Input Sanitization:** Reference and current continuous feature vectors are cleaned of `None`, `NaN`, and infinite values.
2. **Sample Size Safeguards:** Configurable via `minimum_samples` (default: 2). If either vector contains fewer than the required valid points, the test returns `status = INSUFFICIENT_DATA`.
3. **Statistical Significance Threshold:** Drift is flagged for a feature if its computed $p$-value falls below the significance level:
   $$p\text{-value} < \alpha \quad (\text{default } \alpha = 0.05)$$
4. **Multi-Feature Aggregation:** Feature results are aggregated into `DataDriftAnalysis`. If at least one feature exhibits statistically significant drift, `drift_detected = True` is reported.

## 4.6 Windowed Concept Drift Detection Design

Concept drift evaluates shifts in the conditional target relationship $P(Y \mid \mathbf{X})$. In PhoenixML, this is operationalized via a **windowed performance comparison** between a baseline reference labeled window and a current labeled window (`backend/app/monitoring/concept_drift.py`).

### Labeled Window Comparison:
For each window containing ground-truth pairs $(y_{\text{true}}, y_{\text{pred}})$, the detector resolves labels into canonical binary indicators ($0$ or $1$) and computes confusion matrix counts ($TP, TN, FP, FN$) and classification metrics under strict zero-division safeguards. Metric deltas are evaluated:
$$\Delta_{\text{metric}} = \text{Metric}_{\text{current}} - \text{Metric}_{\text{reference}}$$

If any monitored metric exhibits a decline exceeding the degradation threshold:
$$\Delta_{\text{metric}} \le -\text{threshold} \quad (\text{default threshold } = 0.05)$$
the system signals `status = DRIFTED`, sets `drift_detected = True`, and records the degraded metrics in `drifted_metrics`.

## 4.7 Operational Explainability Layer Design

The Explainability Layer (`backend/app/monitoring/explainability.py`) acts as an analytical bridge between raw monitoring telemetry and the AIMD engine. It synthesizes outputs from Health Assessment, Performance Trends, Data Drift, and Concept Drift into a structured `ExplanationResult`:
- **Deterministic Prioritization:** Signals are ranked by severity (`CRITICAL` > `WARNING` > `INFO`) and category (`HEALTH` > `PERFORMANCE` > `CONCEPT_DRIFT` > `DATA_DRIFT`).
- **Primary Factors:** The top drivers of warning or critical status are extracted to guide human inspection.
- **Scientific Limitation Invariant:** The module reports observable statistical signals using non-causal associative phrasing (e.g., *"accompanied by"*, *"observed signal consistent with degradation"*). It does not claim mathematical causal proof of model failure.

## 4.8 Domain Decoupling of the Analytical Components

The six core analytical engines detailed in this chapter and Chapter 5 are designed as pure domain components. By decoupling them completely from FastAPI web handlers and SQLAlchemy database models, PhoenixML achieves:
1. **Isolated Unit Testability:** All 14 tests in `test_health_assessment.py`, 19 tests in `test_performance_analysis.py`, 13 tests in `test_data_drift.py`, 31 tests in `test_concept_drift.py`, and 22 tests in `test_explainability.py` execute in memory in under 2 seconds without starting database transactions or mocking web requests.
2. **Fault Containment:** Numerical errors, unexpected `None` values, or infinite floats in telemetry payloads are safely caught and normalized within the domain components without causing API crashes.
3. **Architectural Separation of Concerns:** Database transactions, user authentication, and HTTP response formatting remain strictly confined to the API and service layers.

## 4.9 Chapter Summary

This chapter detailed the monitoring, drift detection, and explainability subsystems of PhoenixML. It formalized the multi-metric telemetry ingestion schema, performance trend analysis, composite health score policy with dynamic redistribution, two-sample KS data drift testing, windowed concept drift detection, and operational explainability synthesis. It concluded by emphasizing the architectural advantages of domain decoupling for testability and system maintainability.

---

\\newpage


# CHAPTER 5 - ADAPTIVE MAINTENANCE & DECISION-SUPPORT SYSTEM

## 5.1 Philosophy of Decision Support in MLOps

A central philosophical tenet of PhoenixML is that production machine learning maintenance requires **decision support rather than unconstrained autonomous execution**. In mission-critical environments like spam filtering, autonomous systems that automatically trigger retraining, rewrite classification weights, or reroute production traffic introduce unacceptable operational liabilities:
1. **Adversarial Exploitation:** Attackers can craft adversarial email bursts designed to trigger autonomous retraining pipelines, injecting malicious tokens into newly trained models.
2. **Catastrophic Forgetting & Regression:** Unsupervised retraining on recent noisy batches can cause catastrophic forgetting of rare, historical, or edge-case legitimate emails.
3. **Unverified Rollback Outages:** Automatically rolling back production traffic to an older model version without human verification can crash production services if the older model artifact is corrupted, missing, or incompatible with updated data schemas.

PhoenixML resolves this by functioning strictly as an intelligent decision-support platform. The Adaptive Intelligent Model Decision (AIMD) engine analyzes synthesized monitoring evidence to recommend structured, deterministic maintenance actions. However, **every recommendation unconditionally requires authorized human review and sign-off** before any production action can be taken.

## 5.2 Controlled Maintenance Actions

The AIMD engine evaluates evidence against a strictly controlled enumeration of six operational maintenance actions (`backend/app/decisions/aimd.py`):
1. **`CONTINUE_MONITORING`:** The model operates within acceptable performance tolerances, and no statistically significant feature or concept drift is detected. The system recommends maintaining the current standard monitoring cadence.
2. **`INCREASED_MONITORING`:** An isolated feature has exhibited data drift while overall classification health and performance remain stable. The engine recommends increasing sampling frequency to detect any latent degradation early.
3. **`DATA_COLLECTION`:** Multiple input features have drifted while classification performance currently remains stable. The engine recommends gathering and labeling representative production samples from the shifted feature subspace to prepare for future retraining.
4. **`RETRAIN`:** The engine detects concept drift, concurrent data drift with declining health, or critical health where rollback is precluded. Retraining on verified operational data is recommended.
5. **`ROLLBACK`:** Critical operational collapse is detected AND an alternate, verified stable model version is explicitly confirmed in registry metadata. The engine recommends rolling back production traffic to the verified stable predecessor.
6. **`HUMAN_REVIEW`:** The engine encounters insufficient telemetry, performance degradation without detected drift, or ambiguous, conflicting signals. The engine recommends comprehensive diagnostic review by a human engineer.

## 5.3 Deterministic Decision Rules & Evaluation Logic

The AIMD engine executes a deterministic rule tree that systematically evaluates synthesized operational evidence. Figure 5.1 depicts the evaluation flow, and Table 5.1 formalizes the decision matrix.

```
                  +-----------------------------------+
                  |   Receive Aggregated Context      |
                  | Health, Perf, Data Drift, Concept |
                  +-----------------------------------+
                                     │
                                     ▼
                      Has usable monitoring signals?
                                     │
                      ┌──────────────┴──────────────┐
                      ▼ NO                          ▼ YES
             [HUMAN_REVIEW]          Is Health CRITICAL (< 60)?
          (Priority: MEDIUM)                        │
                                      ┌─────────────┴─────────────┐
                                      ▼ YES                       ▼ NO
                          Verified rollback target?       Concept Drift detected?
                                      │                           │
                               ┌──────┴──────┐             ┌──────┴──────┐
                               ▼ YES         ▼ NO          ▼ YES         ▼ NO
                          [ROLLBACK]     [RETRAIN]     [RETRAIN]   Perf Degraded / Warning?
                         (CRITICAL)     (CRITICAL)    (CRITICAL/         │
                                                        HIGH)     ┌──────┴──────┐
                                                                  ▼ YES         ▼ NO
                                                             [HUMAN_REVIEW] Data Drift?
                                                              (HIGH/MED)         │
                                                                          ┌──────┴──────┐
                                                                          ▼ YES         ▼ NO
                                                                    >= 2 drifted? [CONTINUE_
                                                                          │        MONITORING]
                                                                   ┌──────┴──────┐   (LOW)
                                                                   ▼ YES         ▼ NO
                                                                [DATA_COL]  [INCREASED_
                                                                 (MEDIUM)    MONITORING]
                                                                              (MEDIUM)
```

Figure 5.1 - AIMD Decision Rule Evaluation Flow

Table 5.1 - AIMD Recommendation Decision Matrix

| Rule ID | Operational Condition / Evidence Pattern | Recommended Action | Priority | Confidence | Operational Policy & Rationale |
|:---|:---|:---|:---|:---|:---|
| **R-01** | **Critical Health** ($\text{Score} < 60$) + Verified Rollback Target Available | `ROLLBACK` | `CRITICAL` | `HIGH` / `MODERATE` | Severe degradation; verified stable predecessor model available for immediate reversion subject to human approval. |
| **R-02** | **Critical Health** ($\text{Score} < 60$) + No Rollback Target Available | `RETRAIN` | `CRITICAL` | `HIGH` / `MODERATE` | Rollback precluded by safety check (no target verified). Immediate retraining on recent verified data recommended. |
| **R-03** | **Concept Drift Detected** (Performance drop across labeled windows) | `RETRAIN` | `CRITICAL` / `HIGH` | `HIGH` / `MODERATE` | Shift in $P(Y \mid X)$ detected; retraining required to align model decision boundaries with current concept. |
| **R-04** | **Performance Degradation** Without Detected Drift (Data or Concept) | `HUMAN_REVIEW` | `HIGH` / `MEDIUM` | `MODERATE` | Performance dropped but feature distributions and concepts appear stable. Root cause uncharacterized; blind retraining avoided. |
| **R-05** | **Health Warning** ($60 \le \text{Score} < 80$) With Concurrent Data Drift | `RETRAIN` | `HIGH` | `HIGH` | Feature distribution shift accompanied by declining composite health. Retraining recommended on recent operational data. |
| **R-06a**| **Data Drift Detected** on Healthy Model ($\ge 2$ features drifted) | `DATA_COLLECTION` | `MEDIUM` | `HIGH` / `MODERATE` | Input features shifted but accuracy remains stable. Recommend gathering and labeling production samples from drifted subspace. |
| **R-06b**| **Data Drift Detected** on Healthy Model (1 feature drifted) | `INCREASED_MONITORING` | `MEDIUM` | `HIGH` / `MODERATE` | Distribution shift in isolated feature. Increase observation frequency to monitor for latent classification degradation. |
| **R-07** | **Healthy & Stable Model** ($\text{Score} \ge 80$, Stable, No Drift) | `CONTINUE_MONITORING` | `LOW` | `HIGH` | Model operating within acceptable operational tolerances. Standard monitoring cadence maintained. |
| **R-08** | **Insufficient Data / Missing Signals** | `HUMAN_REVIEW` | `MEDIUM` | `INSUFFICIENT` | Monitoring observations span zero time or metrics missing. Investigation of data collection pipelines required. |

## 5.4 Rollback Safety Invariant & Context Verification

A critical safety innovation of the AIMD engine is the **Rollback Safety Invariant**:
> *The AIMD engine shall NEVER recommend a `ROLLBACK` action solely because model health has collapsed.*

Under PhoenixML safety policies, a rollback recommendation is evaluated against `historical_maintenance_context`:
- If `historical_maintenance_context` is missing, `None`, or empty, `ROLLBACK` is strictly precluded.
- If `rollback_target_available` is not explicitly `True`, `ROLLBACK` is strictly precluded.
- When precluded, the engine falls back to `RETRAIN` (Priority: `CRITICAL`), explicitly documenting the preclusion in its rationale:
  *"Model operational health is CRITICAL (score: 52.4). Rollback is precluded (No verified rollback target available in registry). Urgent model retraining on recent verified production data is recommended, subject to human approval."*

This invariant prevents disastrous operational scenarios where automated systems attempt to revert traffic to nonexistent, unverified, or incompatible model artifacts.

## 5.5 Urgency Priority & Evidence Confidence Classifications

Every recommendation emitted by AIMD includes deterministic urgency priority and evidence confidence ratings, formalized in Tables 5.2 and 5.3.

Table 5.2 - AIMD Urgency Priority Levels and SLA

| Priority | Operational Context | Response SLA |
|:---|:---|:---|
| `CRITICAL` | Critical health score (< 60), severe classification collapse, or concept drift | Immediate human operator triage and approval |
| `HIGH` | Concept drift detected, performance drop without drift, or warning with data drift | Prioritized scheduling during current operational cycle |
| `MEDIUM` | Data drift on stable models or insufficient monitoring data | Routine review and diagnostic evaluation |
| `LOW` | Model healthy and performance stable or improving | Standard observational logging |

Table 5.3 - AIMD Evidence Confidence Classifications

| Confidence | Analytical Evidence Breadth | Numeric Mapping |
|:---|:---|:---:|
| `HIGH` | Corroborated by $\ge 2$ independent analytical sources (e.g., health + trend + drift) | 0.9 |
| `MODERATE` | Supported by a primary strong analytical signal with limited corroboration | 0.7 |
| `LOW` | Ambiguous or conflicting signals requiring expert triage | 0.4 |
| `INSUFFICIENT` | Missing observations or inputs marked `INSUFFICIENT_DATA` | 0.1 |

## 5.6 Human-in-the-Loop Approval Workflow

Every recommendation emitted by AIMD enforces two invariant attributes:
$$\text{requires\_human\_approval} = \text{True}$$
$$\text{approval\_status} = \text{PENDING}$$

Figure 5.2 illustrates the approval state machine governing recommendation resolution.

```
                  +-----------------------------------+
                  |              PENDING              |
                  | (Recommendation Awaiting Review)  |
                  +-----------------------------------+
                        │                         │
       Admin / Owner    │                         │    Admin / Owner
       Approves Action  │                         │    Rejects Action
                        ▼                         ▼
             +--------------------+    +--------------------+
             |      APPROVED      |    |      REJECTED      |
             | (Human Authorized) |    | (Action Dismissed) |
             +--------------------+    +--------------------+
```

Figure 5.2 - Decision Approval State Machine Transitions

### State Transition Rules:
1. `PENDING` -> `APPROVED`: Permitted for authorized users (`ADMIN` globally; `ML_ENGINEER` for owned models).
2. `PENDING` -> `REJECTED`: Permitted for authorized users (`ADMIN` globally; `ML_ENGINEER` for owned models).
3. `APPROVED` -> `APPROVED` / `REJECTED` -> `REJECTED`: Idempotent confirmations return HTTP 200 without modifying state.
4. `APPROVED` -> `REJECTED` or `REJECTED` -> `APPROVED`: **Strictly Forbidden** (HTTP 400 Bad Request). Finalized decisions cannot be overturned.
5. Finalized (`APPROVED`/`REJECTED`) -> `PENDING`: **Strictly Forbidden** (HTTP 400 Bad Request). Finalized decisions cannot be re-opened.

## 5.7 Decision Persistence and Audit Trail Design

When AIMD evaluates a model, the recommendation is permanently committed to PostgreSQL in the `decision_logs` table. The stored record captures:
- Unique identifier (`id` UUID)
- Model relationship (`model_id` referencing `registered_models.id`, ON DELETE CASCADE)
- Generation timestamp (`created_at` in UTC)
- Evaluated health metrics (`health_score` and `health_status`)
- Decision recommendation attributes (`recommended_action`, `priority`, `confidence`)
- Full justification texts (`rationale` and `explanation`)
- Corroborating telemetry evidence (`supporting_signals` JSON payload)
- Invariant safety flags (`requires_human_approval = True` and current `approval_status`)

### Current Schema Scope vs. Future Audit Extensions:
The API strictly enforces that only authorized users (`ADMIN` or the owning `ML_ENGINEER`) can execute the approval endpoint (`PATCH /api/spam-models/{id}/decisions/{id}/approval`). When authorized, the repository commits the new `approval_status` (`APPROVED` or `REJECTED`).

Under the current database schema, individual reviewer user IDs (`reviewed_by`) and secondary approval timestamps (`approved_at`) are not persisted as dedicated relational columns on the `decision_logs` record. Maintaining an immutable historical record of the original decision and enforcing state machine finality satisfies the core operational requirements, while granular actor-level audit tables represent a planned future enhancement (detailed in Section 8.4).

## 5.8 Chapter Summary

This chapter detailed the design of the Adaptive Intelligent Model Decision (AIMD) engine and the Human-in-the-Loop approval workflow. It articulated why production ML systems require decision support rather than unconstrained autonomous execution, defined the six controlled maintenance actions, formalized the deterministic decision matrix, and detailed the rollback safety invariant. It concluded by describing the approval state machine, priority/confidence ratings, and decision persistence architecture.

---

\\newpage


# CHAPTER 6 - IMPLEMENTATION DETAILS

## 6.1 Implementation Overview & Layered Organization

PhoenixML is implemented as an asynchronous, service-oriented Python web application adhering to clean architectural separation [11, 12]. The backend source code is organized under `backend/app/`:
```
backend/app/
├── core/         # Configuration (config.py), logging, exception handlers
├── db/           # SQLAlchemy Base class, engine session factory, dependencies
├── auth/         # Security functions, JWT decoding, authentication routes
├── users/        # User domain models, schemas, and profile management
├── models/       # RegisteredModel entity, Model Registry service, and router
├── monitoring/   # Health, performance, data drift, concept drift, explainability
├── decisions/    # AIMD engine, DecisionLog entity, repository, and service
├── dashboard/    # Fleet-wide aggregate telemetry service and router
└── main.py       # FastAPI application factory, middleware, and router mounts
```

The frontend is housed under `frontend/`, consisting of a pure React 18 Single Page Application served directly by FastAPI.

## 6.2 Core Software Technology Stack

Table 6.1 presents the production software stack and primary scientific libraries utilized.

Table 6.1 - Core Software Technology Stack

| Component Tier | Technology / Library | Version | Operational Role | Reference |
|:---|:---|:---|:---|:---:|
| **Programming Language** | Python | 3.12+ | Core backend runtime and scientific computation | - |
| **API Web Framework** | FastAPI | 0.115+ | High-throughput asynchronous REST API and OpenAPI documentation | Tiangolo [17] |
| **ASGI Server** | Uvicorn | 0.30+ | Production ASGI asynchronous server implementation | - |
| **ORM & Persistence** | SQLAlchemy | 2.0+ | Modern mapped-column relational Object-Relational Mapping | Bayer [19] |
| **Database Engine** | PostgreSQL | 15+ | ACID relational storage with native UUID and JSON support | PostgreSQL [18] |
| **Schema Migrations** | Alembic | 1.13+ | Version-controlled database schema migration tracking | - |
| **Data Validation** | Pydantic | 2.8+ | Strong typing, request parsing, and schema contracts | - |
| **Security & Auth** | PyJWT / Passlib | 2.9+ / 1.7+ | JWT token issuance/verification and bcrypt password hashing | Jones [15] |
| **Scientific Computing** | SciPy / NumPy | 1.14+ / 2.0+ | Kolmogorov-Smirnov test (`ks_2samp`) and numerical vectors | - |
| **Machine Learning** | Scikit-Learn | 1.5+ | Reference classification algorithms and metrics | Pedregosa [9] |
| **Frontend Framework** | React | 18.2 | Component-driven operator dashboard Single Page Application | Meta [20] |
| **Testing Framework** | Pytest / HTTPX | 8.3+ / 0.27+ | Automated unit, integration, and E2E system testing | - |

## 6.3 Decoupled Domain Analytical Engines Implementation

The core analytical engines in `app/monitoring/` and `app/decisions/` are implemented as pure Python domain components:
- **`HealthAssessor` (`app/monitoring/health.py`):** Accepts metric floating-point values, validates policy weights via Pydantic, applies missing metric dynamic redistribution, clamps the composite score to $[0.0, 100.0]$, and categorizes status (`HEALTHY`, `WARNING`, `CRITICAL`, `INSUFFICIENT_DATA`).
- **`PerformanceAnalyzer` (`app/monitoring/performance.py`):** Sorts chronological observations, sanitizes floats, computes deltas against baselines, and flags `DEGRADED`, `STABLE`, or `IMPROVING`.
- **`DataDriftDetector` (`app/monitoring/data_drift.py`):** Strips non-numeric values from reference and current feature distributions, enforces sample size minimums ($N \ge 2$), and invokes `scipy.stats.ks_2samp(ref_clean, cur_clean)` to evaluate the $p$-value against $\alpha = 0.05$.
- **`ConceptDriftDetector` (`app/monitoring/concept_drift.py`):** Resolves heterogeneous label representations into canonical $0$ and $1$ integers, computes confusion matrix counts, calculates classification metrics, and signals `DRIFTED` if any metric drops by $\ge 0.05$.
- **`ExplainabilityAnalyzer` (`app/monitoring/explainability.py`):** Ingests domain results from Health, Performance, and Drift modules, ranks signals deterministically, extracts top drivers, and generates associative non-causal summaries.
- **`AIMDDecisionEngine` (`app/decisions/aimd.py`):** Evaluates multi-factor context against deterministic rules, enforces rollback context verification, sets priority/confidence, and assigns `requires_human_approval = True`.

Because these components have zero dependencies on web handlers or database sessions, they execute with sub-millisecond efficiency and provide 100% isolated testability.

## 6.4 Authentication & RBAC Implementation

User authentication is centralized in `app/auth/`:
- `security.py`: Implements `get_password_hash()`, `verify_password()`, `create_access_token()`, and `decode_token()`.
- `dependencies.py`: Defines `get_current_user()` (which decodes the bearer JWT, validates expiration, and fetches the active user) and `require_roles(*allowed_roles)` (which enforces role authorization).

```python
def require_roles(*allowed_roles: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AuthorizationError(detail="Insufficient permissions")
        return current_user
    return role_checker
```

The router (`app/auth/router.py`) exposes `/api/auth/register`, `/api/auth/login`, `/api/auth/refresh`, and `/api/auth/logout`.

## 6.5 Model Registry Implementation

Implemented in `app/models/`:
- Entity: `RegisteredModel` (`app/models/models.py`) mapping to `registered_models`.
- Repository: `RegisteredModelRepository` (`app/models/repository.py`) providing CRUD queries using modern SQLAlchemy 2.0 `select()` statements.
- Service: `RegisteredModelService` (`app/models/service.py`) enforcing ownership constraints: `ADMIN` users can access and modify any model, while `ML_ENGINEER` users are strictly restricted to models where `model.owner_id == user.id`.
- Router: Exposes `/api/spam-models` (`GET`, `POST`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`).

## 6.6 Monitoring Telemetry Ingestion & Query Implementation

Implemented across `app/models/` and `app/monitoring/`:
- Entity: `MonitoringObservation` (`app/models/models.py`) mapping to `monitoring_observations`.
- Repository: `MonitoringObservationRepository` (`app/models/monitoring_repository.py`) handling chronological ingestion, timestamp validation, pagination, and date-range queries.
- Router: Exposes `/api/spam-models/{model_id}/monitoring` (`POST` for observation ingestion, `GET` for listing chronological records) and `/api/spam-models/{model_id}/monitoring/{observation_id}` (`GET` single record, `DELETE`).

## 6.7 Health, Drift & Explainability Subsystems Implementation

The monitoring service (`app/monitoring/service.py`) acts as the orchestrator:
1. Ingests raw telemetry or retrieves recent observation records for a model.
2. Passes metric values to `HealthAssessor` to obtain the normalized health score.
3. Passes chronological observations to `PerformanceAnalyzer` to assess trajectories.
4. When feature distributions or labeled test batches are supplied, routes them to `DataDriftDetector` and `ConceptDriftDetector`.
5. Passes all analytical results to `ExplainabilityAnalyzer` to produce a structured explanation result.

## 6.8 AIMD Engine & Decision Service Implementation

Implemented in `app/decisions/`:
- Pure Domain: `AIMDDecisionEngine` (`app/decisions/aimd.py`).
- Entity: `DecisionLog` (`app/decisions/models.py`) mapping to `decision_logs`.
- Repository: `DecisionLogRepository` (`app/decisions/repository.py`) managing ACID transactions, pessimistic locking for updates (`get_by_id_and_model_for_update`), and paginated history queries.
- Service: `DecisionService` (`app/decisions/service.py`):
  - Orchestrates the full analytical pipeline to build `AIMDContext`.
  - Invokes `AIMDDecisionEngine.evaluate(context)`.
  - Persists the recommendation into `decision_logs` with `approval_status = PENDING`.
  - Exposes `update_approval_status()` enforcing role authorization, ownership scoping, and state transition finality.
- Router: Exposes `/api/spam-models/{id}/decisions/evaluate` (`POST`), `/api/spam-models/{id}/decisions` (`GET`), and `/api/spam-models/{id}/decisions/{decision_id}/approval` (`PATCH`).

## 6.9 Single-Port Web Serving & Dashboard Implementation

In `app/main.py`, FastAPI is configured with CORS and static file mounting:
```python
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.is_dir():
    app.mount("/ui", StaticFiles(directory=str(frontend_dir), html=True), name="ui")

    @app.get("/", include_in_schema=False)
    def root_redirect():
        return RedirectResponse(url="/ui/")
```

The operator dashboard single-page application (`frontend/src/App.js`) is constructed from modular React components:
- `LoginScreen`: Renders email/password inputs, role hint badges, and handles JWT token storage.
- `Navbar`: Displays platform branding, current authenticated user, role badge, and sign-out trigger.
- `HITLBanner`: Displays the prominent human-in-the-loop governance advisory notice.
- `KPIGrid`: Executive summary metric cards displaying total models, active models, fleet average health, and pending approvals.
- `HealthMeter`: Visual progress bar and status badge depicting normalized 0-100 health.
- `DecisionReviewBox`: Primary interactive card displaying AIMD recommendations, rationale narratives, and interactive "Approve" and "Reject" buttons.
- `ModelCard`: Summary card showing model details, deployment status, and quick-action links.
- `RecentDecisionsTable`: Historical table displaying recent recommendations and finalized approval states.

## 6.10 Database Schema & Migration Implementation

Database migrations are managed using Alembic, with five sequential version scripts tracking schema evolution:
1. `0001_add_user_table.py` / `b9b363044e54_create_user_model.py`: Creates the `users` table, UUID primary keys, unique indexes, and `userrole` enum (`ADMIN`, `ML_ENGINEER`, `VIEWER`).
2. `e4cbbfe86b34_add_registered_models.py`: Creates `registered_models` table, foreign key referencing `users.id` with `ON DELETE CASCADE`, indexes on `name` and `owner_id`, and `modelstatus` enum.
3. `38dc8f99dc6c_add_monitoring_observations_table.py`: Creates `monitoring_observations` table with foreign key to `registered_models.id` (`CASCADE`), metric floats, and timestamps.
4. `c30a5d242a96_add_decision_logs_table.py`: Creates `decision_logs` table, native PostgreSQL enums (`aimdaction`, `aimdpriority`, `approvalstatus`), JSON supporting signals, float constraints, and foreign key to `registered_models.id` (`CASCADE`).

## 6.11 Automated Testing Implementation & Test Architecture

Testing is implemented using `pytest` and `httpx`. The test suite is organized into **32 dedicated test modules** covering five distinct validation levels:
1. **Unit Tests (Pure Analytical Logic):**
   - `test_health_assessment.py`: Validates metric weighting, missing metric redistribution, boundary clamping, and invalid float handling (14 tests).
   - `test_performance_analysis.py`: Validates chronological observation sorting, degradation thresholding, and status classifications (19 tests).
   - `test_data_drift.py`: Validates two-sample KS-test statistics, $p$-values, and sample size minimums (13 tests).
   - `test_concept_drift.py`: Validates label canonicalization, confusion matrix math, and window comparison (31 tests).
   - `test_explainability.py`: Validates signal ranking, severity hierarchies, and associative summaries (22 tests).
   - `test_aimd.py`: Validates all six decision rules, priority assignments, confidence ratings, and rollback safety invariants (32 tests).
2. **Persistence & Database Integration Tests:**
   - `test_decision_log_db.py`, `test_database_integration_persistence.py`, `test_model_registry_db.py`, `test_monitoring_db.py`: Validate schema constraints, foreign key cascades, UUID generation, enum persistence, and transaction rollback safety (83 tests total).
3. **Service Layer Integration Tests:**
   - `test_model_registry_service.py`, `test_monitoring_service.py`, `test_decision_service.py`, `test_decision_query_service.py`: Validate service orchestration, business rules, and repository transactions (44 tests total).
4. **API & Contract Tests:**
   - `test_auth.py`, `test_login.py`, `test_logout.py`, `test_refresh.py`, `test_profile.py`, `test_dependencies.py`, `test_security.py`: Validate authentication endpoints and JWT contracts (47 tests total).
   - `test_model_registry_api.py`, `test_model_registry_integration.py`: Validate model CRUD endpoints (18 tests total).
   - `test_monitoring_api.py`, `test_monitoring_api_integration.py`: Validate observation ingestion endpoints (26 tests total).
   - `test_decision_api.py`, `test_decision_evaluation_api.py`, `test_decision_approval_api.py`: Validate on-demand evaluation, decision history, and approval endpoints (49 tests total).
   - `test_dashboard_api.py`: Validates fleet-wide and model-specific aggregate telemetry endpoints (16 tests).
5. **Security & RBAC Enforcement Tests:**
   - `test_rbac.py`: Validates role restrictions across endpoints and verifies cross-engineer tenant isolation (8 tests).
6. **Frontend & End-to-End Workflow Tests:**
   - `test_dashboard_ui.py`: Validates frontend route redirects (`/` -> `/ui/`), static file mounts, HTML structure, and CSS presence (9 tests).
   - `test_system_integration_workflow.py`: Validates complete multi-step operational lifecycles from registration to approval (8 tests).

## 6.12 Chapter Summary

This chapter provided a detailed examination of PhoenixML's implementation. It detailed the core software stack, documented the decoupled domain analytical engines, reviewed authentication and RBAC, and detailed the model registry, monitoring, AIMD, and dashboard subsystems. It detailed the single-port web serving architecture, documented Alembic database migrations, and outlined the architecture of the 32 automated test modules.

---

\\newpage


# CHAPTER 7 - RESULTS, DEMONSTRATION & EVALUATION

## 7.1 Evaluation Strategy & Test Environment

The PhoenixML platform was evaluated through a rigorous verification strategy designed to validate functional correctness, statistical precision, security enforcement, and operational safety:
1. **Automated Unit & Integration Test Suites:** Continuous verification of all 32 test modules using `pytest` and `httpx`.
2. **Security & Access Control Auditing:** Verifying role boundaries, credential hashing, token lifecycle, and cross-engineer isolation.
3. **Database Schema & Relational Integrity Auditing:** Validating ACID transaction safety, foreign key cascading deletions, and migration stability against PostgreSQL.
4. **End-to-End Telemetry Demonstration (`SpamGuard-v1`):** Simulating production telemetry progression across healthy and degraded operational states to evaluate the complete monitoring, explainability, AIMD recommendation, and human approval lifecycle.

The evaluation was executed on a standardized development workstation operating Windows 11 64-bit, Python 3.12, PostgreSQL 16, and modern browser environments.

## 7.2 Functional Verification of Platform Subsystems

Functional verification confirmed that all 15 functional requirements (FR-01 through FR-15) operate as specified:
- **Authentication:** Registration, login, token refresh, and logout execute without session leaks.
- **Model Registry:** Full CRUD operations on model metadata operate cleanly with automatic timestamps and UUID assignment.
- **Telemetry Ingestion:** Runtime observation payloads are ingested and validated against strict schema boundaries.
- **Drift Detection:** Two-sample KS-tests accurately calculate $p$-values and identify distribution shifts; windowed comparisons flag concept drift when metrics deteriorate beyond 0.05.
- **Health Assessment:** Normalized 0-100 scores are computed accurately, with dynamic redistribution correctly adjusting weights when individual metrics are omitted.
- **AIMD Recommendation:** Multi-factor evidence is deterministically mapped to the appropriate maintenance action with priority and confidence ratings.
- **Human Approval Workflow:** Approvals and rejections transition cleanly from `PENDING`, enforcing state finality.

## 7.3 Authentication & RBAC Enforcement Verification

Security test suites verified the Role-Based Access Control matrix (Table 3.3):
- `ADMIN` accounts successfully perform all global administrative, operational, and approval tasks.
- `ML_ENGINEER` accounts successfully manage their own registered models, ingest telemetry, trigger AIMD evaluations, and submit approvals on their owned models.
- Cross-engineer access attempts (e.g., Engineer A attempting to view or approve Engineer B's model decisions) are systematically blocked with HTTP 403 Forbidden exceptions.
- `VIEWER` accounts are restricted to read-only endpoints; any attempt to trigger evaluations, register models, or update approvals returns HTTP 403 Forbidden.

## 7.4 Model Registry & Ownership Scoping Results

The Model Registry subsystem was verified for multi-model inventory tracking. Registered models maintain distinct operational statuses (`DEVELOPMENT`, `ACTIVE`, `ARCHIVED`). Model ownership scoping was confirmed: cascading delete constraints ensure that when a model is deleted by its owner, all associated monitoring observations and decision logs are purged cleanly by PostgreSQL, preventing orphaned database records.

## 7.5 Monitoring Ingestion & Health Evaluation Results

Telemetry ingestion was validated using synthetic and historical observation streams. The health scoring engine was verified across diverse boundary conditions:
- When all four metrics (accuracy, precision, recall, F1) are present, the composite score reflects the weighted sum ($0.10 \times \text{Acc} + 0.25 \times \text{Prec} + 0.25 \times \text{Rec} + 0.40 \times \text{F1}$).
- When precision or recall is missing (`None`), the dynamic redistribution policy successfully reallocates weights among available metrics without false zero-score penalties.
- When all metrics are missing, the engine returns `health_score = None` and `status = INSUFFICIENT_DATA`.

## 7.6 Drift Detection & Operational Explainability Results

Analytical testing confirmed that the data drift detector correctly identifies continuous feature distribution shifts when sample $p$-values fall below $\alpha = 0.05$, while returning `INSUFFICIENT_DATA` when sample counts are below the minimum threshold ($N < 2$). The concept drift detector successfully flags performance drops across labeled windows exceeding the 0.05 degradation threshold.

The operational explainability layer was verified to synthesize multi-source telemetry into prioritized explanation signals, extracting top contributing factors using strictly non-causal associative phrasing (e.g., *"performance degraded accompanied by concept drift"*).

## 7.7 Distinction: Monitored Model vs. PhoenixML MLOps Platform

To ensure academic and technical rigor, this evaluation emphasizes a fundamental architectural distinction:
- **The Monitored Model (`SpamGuard-v1`):** Represents an external, registered spam classification model (specifically a Multinomial Naïve Bayes classifier trained on email text representations).
- **PhoenixML:** Represents the intelligent MLOps monitoring and decision-support platform that supervises the registered model throughout its operational deployment.

> **CRITICAL CLARIFICATION:**
> The following operational demonstration illustrates PhoenixML's monitoring, health scoring, explainability, and AIMD decision-support pipeline using registered-model telemetry. It does **not** claim that PhoenixML trained `SpamGuard-v1` end-to-end within the platform runtime, nor does it claim that PhoenixML autonomously retrained, deployed, or modified the model.

## 7.8 Telemetry-Driven Demonstration: SpamGuard-v1

To evaluate the complete decision-support lifecycle, an operational demonstration was conducted using a registered model named **`SpamGuard-v1`** (Framework: `scikit-learn`, Algorithm: `MultinomialNB`, Status: `ACTIVE`).

The demonstration evaluated two successive operational observation windows:

### Stage 1: Initial Healthy Observation
- Classification Telemetry:
  - Accuracy = 0.95
  - Precision = 0.93
  - Recall = 0.91
  - F1-Score = 0.92
  - Prediction Count: 1,000 (Spam: 300, Ham: 700)
- Mathematical Health Score Calculation:
  $$\text{Health Score} = 0.10(95) + 0.25(93) + 0.25(91) + 0.40(92)$$
  $$\text{Health Score} = 9.50 + 23.25 + 22.75 + 36.80 = \mathbf{92.30 / 100}$$
- Status Classification: **`HEALTHY`** ($\ge 80.0$)

### Stage 2: Degraded Observation (Simulating Operational Distribution Shift)
- Classification Telemetry:
  - Accuracy = 0.70
  - Precision = 0.68
  - Recall = 0.65
  - F1-Score = 0.66
  - Prediction Count: 1,200 (Spam: 450, Ham: 750)
- Mathematical Health Score Calculation:
  $$\text{Health Score} = 0.10(70) + 0.25(68) + 0.25(65) + 0.40(66)$$
  $$\text{Health Score} = 7.00 + 17.00 + 16.25 + 26.40 = \mathbf{66.65} \approx \mathbf{66.7 / 100}$$
- Status Classification: **`WARNING`** ($60.0 \le \text{Score} < 80.0$)

Table 7.1 summarizes the operational telemetry and health evaluation results across both stages.

Table 7.1 - SpamGuard-v1 Operational Telemetry and Health Evaluation Results

| Observation Stage | Accuracy | Precision | Recall | F1-Score | Mathematical Calculation | Health Score (0-100) | Health Status |
|:---|:---:|:---:|:---:|:---:|:---|:---:|:---:|
| **Initial Observation** | 0.950 | 0.930 | 0.910 | 0.920 | $9.50 + 23.25 + 22.75 + 36.80$ | **92.3 / 100** | `HEALTHY` |
| **Degraded Observation**| 0.700 | 0.680 | 0.650 | 0.660 | $7.00 + 17.00 + 16.25 + 26.40$ | **66.7 / 100** | `WARNING` |

### AIMD Evaluation of Degraded Telemetry:
Upon triggering on-demand evaluation (`POST /api/spam-models/{id}/decisions/evaluate`), the AIMD engine evaluated the multi-factor context:
- Health Status: `WARNING` (Score: 66.7)
- Performance Trajectory: `DEGRADED` (F1 dropped from 0.92 to 0.66; Accuracy dropped from 0.95 to 0.70)
- Data Drift: No statistical feature drift detected in baseline vectors.
- Concept Drift: No labeled test batches submitted for sliding window comparison.
- Rule Triggered: **Rule 4** (Performance degradation observed without detected data or concept drift).

Because root causes are uncharacterized, blind retraining was avoided in accordance with PhoenixML safety policies. The engine generated a `HUMAN_REVIEW` recommendation, detailed in Table 7.2.

Table 7.2 - SpamGuard-v1 AIMD Recommendation Output

| Recommendation Attribute | Evaluated System Output | Description / Operational Meaning |
|:---|:---|:---|
| **Model Identifier** | `SpamGuard-v1` | Registered model under operational supervision |
| **Recommended Action** | `HUMAN_REVIEW` | Suggested maintenance action (AIMD Rule 4) |
| **Priority** | `HIGH` / `MEDIUM` | Urgency classification for human operator triage |
| **Evidence Confidence** | `MODERATE` (0.7) | Normalized evidence confidence rating |
| **Evaluated Health Score**| 66.7 / 100 | Composite health rating at decision time |
| **Evaluated Health Status**| `WARNING` | Composite health classification |
| **Rationale Narrative** | *"Performance degradation observed without accompanying feature data drift or concept drift. Because root causes are uncharacterized, automated retraining is not advisable. Human review and diagnostic inspection are recommended."* | Deterministic justification text |
| **Supporting Signals** | `["health_warning(score=66.7)", "performance_degraded(f1_score, accuracy)"]` | Corroborating telemetry indicators |
| **Requires Human Approval**| `True` | Invariant safety flag enforcing human-in-the-loop oversight |
| **Initial Approval Status**| `PENDING` | Recommendation persisted awaiting operator sign-off |

```
[FIGURE PLACEHOLDER: Telemetry Progression and Health Degradation for SpamGuard-v1]
Figure 7.1 - Telemetry Progression and Health Degradation for SpamGuard-v1
```

## 7.9 Human Approval Workflow Execution Results

Following the generation of the `HUMAN_REVIEW` recommendation for `SpamGuard-v1`:
1. The recommendation appeared on the operator dashboard in the pending review card.
2. The authorized ML Engineer inspected the diagnostic explanation and corroborating telemetry.
3. The engineer submitted an approval action via `PATCH /api/spam-models/{id}/decisions/{decision_id}/approval` with payload `{"approval_status": "APPROVED"}`.
4. The backend validated user authentication and model ownership, verified state machine finality, and committed `approval_status = APPROVED` in PostgreSQL.
5. A subsequent attempt to change the approved decision to `REJECTED` returned HTTP 400 Bad Request (*"Cannot change approval status of a finalized decision"*), confirming state machine immutability.

```
[FIGURE PLACEHOLDER: End-to-End Decision Support and Human Approval Execution Sequence]
Figure 7.2 - End-to-End Decision Support and Human Approval Execution Sequence
```

## 7.10 Operator Dashboard & Web UI Operational Results

The React 18 single-page dashboard was verified in modern browser sessions:
- Seamless session management: Login screen authenticates credentials, stores JWT tokens in local storage, and loads fleet KPIs.
- Real-time KPI summary: Displays total models (1), active models (1), average health score (66.7%), and pending approvals (0 after approval).
- Visual Health Progress Bar: Renders color-coded progress bars (green for $\ge 80$, amber for $60-79$, red for $< 60$).
- Interactive Approval Controls: "Approve" and "Reject" buttons trigger immediate API calls with optimistic UI updates.

## 7.11 Automated Test Suite Execution Results

The entire PhoenixML platform was subjected to automated verification using `pytest`. The test execution yielded **439 passing tests out of 439 total tests** across **32 dedicated test modules** (100% pass rate, 0 failures, 4 warnings, total execution time: 178.61 seconds).

Table 7.3 details the test distribution across system components.

Table 7.3 - Comprehensive Automated Test Suite Distribution and Coverage

| Functional Test Category | Dedicated Test Modules | Number of Tests | Pass Rate |
|:---|:---|:---:|:---:|
| **Authentication, JWT & Security** | `test_auth.py` (5), `test_login.py` (7), `test_logout.py` (6), `test_refresh.py` (8), `test_profile.py` (10), `test_security.py` (7), `test_dependencies.py` (4) | 47 | 100% |
| **Role-Based Access Control (RBAC)**| `test_rbac.py` (8) | 8 | 100% |
| **Model Registry Subsystem** | `test_model_registry_api.py` (17), `test_model_registry_service.py` (7), `test_model_registry_db.py` (8), `test_model_registry_integration.py` (1) | 33 | 100% |
| **Monitoring Telemetry Subsystem** | `test_monitoring_api.py` (14), `test_monitoring_service.py` (9), `test_monitoring_db.py` (13), `test_monitoring_api_integration.py` (12) | 48 | 100% |
| **Health Assessment Engine** | `test_health_assessment.py` (14) | 14 | 100% |
| **Performance Trend Analysis** | `test_performance_analysis.py` (19) | 19 | 100% |
| **Statistical Data Drift Detection**| `test_data_drift.py` (13) | 13 | 100% |
| **Windowed Concept Drift Detection**| `test_concept_drift.py` (31) | 31 | 100% |
| **Explainability Analyzer** | `test_explainability.py` (22) | 22 | 100% |
| **AIMD Decision Engine** | `test_aimd.py` (32) | 32 | 100% |
| **Decision Persistence & DB Layer** | `test_decision_log_db.py` (55), `test_decision_service.py` (14), `test_decision_query_service.py` (14), `test_database_integration_persistence.py` (7) | 90 | 100% |
| **Decision Approval & Evaluation APIs**| `test_decision_api.py` (13), `test_decision_evaluation_api.py` (17), `test_decision_approval_api.py` (19) | 49 | 100% |
| **Dashboard API & Frontend UI** | `test_dashboard_api.py` (16), `test_dashboard_ui.py` (9) | 25 | 100% |
| **End-to-End System Integration** | `test_system_integration_workflow.py` (8) | 8 | 100% |
| **TOTAL AUTOMATED TEST SUITE** | **32 Dedicated Test Modules** | **439** | **100%** |

## 7.12 Database & Migration Consistency Validation

Database integrity and schema migration consistency were verified against PostgreSQL:
- Clean forward and backward Alembic migration executions confirmed schema stability up to head revision `c30a5d242a96`.
- Foreign key cascading delete constraints were verified: deleting registered models cleans up all observation and decision records.
- Native enum constraints (`aimdaction`, `aimdpriority`, `approvalstatus`) prevent invalid string insertions.

## 7.13 Discussion of Findings

The experimental evaluation and testing results demonstrate that PhoenixML successfully achieves its primary design goals:
1. **From Passive Alerting to Structured Guidance:** The platform successfully converts isolated, confusing metric drops into structured, explainable maintenance recommendations.
2. **Guaranteed Operational Safety:** The strict human-in-the-loop requirement (`requires_human_approval = True`) and the rollback safety invariant eliminate the severe risks of unconstrained autonomous execution.
3. **High Architectural Reliability:** The complete test suite pass rate (439/439 tests) across all 32 modules validates the architectural resilience of the decoupled domain design.

## 7.14 Chapter Summary

This chapter presented the comprehensive evaluation results of PhoenixML. It detailed functional and security verification, highlighted the distinction between the monitored classifier and the MLOps platform, documented the complete `SpamGuard-v1` telemetry demonstration (evaluating initial 92.3 health vs. degraded 66.7 health and `HUMAN_REVIEW` approval), and presented the verified automated test suite results (439 tests across 32 modules).

---

\\newpage


# CHAPTER 8 - CONCLUSION & FUTURE SCOPE

## 8.1 Conclusion

Modern enterprise software systems increasingly depend on machine learning models whose operational effectiveness degrades silently in production due to evolving data distributions and concept drift. In security-sensitive domains like spam email detection, failure to adapt allows emerging phishing campaigns to breach corporate boundaries or causes vital communications to be incorrectly quarantined. While standard MLOps platforms offer telemetry dashboards and threshold alerts, they suffer from passive alerting without structured, policy-governed maintenance guidance.

This project successfully designed, implemented, and evaluated **PhoenixML**, an intelligent MLOps decision-support platform for model monitoring, explainability, and adaptive maintenance. The platform integrates multi-source telemetry ingestion, two-sample Kolmogorov-Smirnov data drift testing, windowed concept drift proxy detection, weighted composite health scoring with dynamic redistribution, and operational explainability synthesis into a unified, service-oriented architecture. Through the Adaptive Intelligent Model Decision (AIMD) engine, PhoenixML provides deterministic, policy-governed maintenance recommendations across six controlled actions (`CONTINUE_MONITORING`, `INCREASED_MONITORING`, `DATA_COLLECTION`, `RETRAIN`, `ROLLBACK`, and `HUMAN_REVIEW`).

Crucially, the system strictly enforces **human-in-the-loop (HITL)** governance and rollback safety invariants, eliminating the severe operational hazards of unconstrained autonomous execution. Validated with **439 passing automated tests out of 439 total tests** across **32 dedicated test modules** (100% pass rate) and demonstrated via the operational evaluation of `SpamGuard-v1`, PhoenixML establishes a robust foundation for modern, safe, and explainable MLOps governance.

## 8.2 Summary of Contributions

The primary engineering and academic contributions of PhoenixML include:
1. **Intelligent Decision-Support Paradigm:** Formulated an evidence-based MLOps supervision framework that bridges raw telemetry and operational maintenance triage.
2. **Decoupled Pure Domain Analytical Engines:** Architected six standalone analytical modules (`HealthAssessor`, `PerformanceAnalyzer`, `DataDriftDetector`, `ConceptDriftDetector`, `ExplainabilityAnalyzer`, `AIMDDecisionEngine`) completely decoupled from web and persistence layers, ensuring high testability, maintainability, and reuse.
3. **Dynamic Redistribution Health Policy:** Developed a mathematically rigorous composite health score that normalizes multi-metric performance into a 0-100 scale and dynamically reallocates weights for missing metrics, preventing false zero-score penalties.
4. **Dual-Layer Drift Detection:** Integrated non-parametric continuous feature drift testing (KS-test) and sliding labeled-window performance tracking (concept drift).
5. **Deterministic AIMD Decision Engine:** Codified an operational decision matrix that maps multi-factor evidence to structured maintenance recommendations with urgency priority and confidence ratings.
6. **Rollback Safety Invariant:** Guaranteed operational safety by enforcing historical registry verification before permitting rollback recommendations, precluding catastrophic outages.
7. **Auditable Human-in-the-Loop State Machine:** Enforced mandatory human approval (`requires_human_approval = True`) and immutable state transitions (`PENDING` -> `APPROVED`/`REJECTED`) with strict Role-Based Access Control (`ADMIN`, `ML_ENGINEER`, `VIEWER`).
8. **Single-Port Embedded Web Serving:** Implemented embedded static-file serving for the React 18 SPA operator dashboard, simplifying demonstration and local execution.
9. **Exhaustive Automated Verification:** Built and validated 32 automated test modules comprising 439 tests with a 100% pass rate.

## 8.3 Current Limitations

While PhoenixML achieves its core design objectives, several operational boundaries reflect the current scope:
1. **Batch Telemetry Ingestion:** Observations are ingested via batch REST API endpoints rather than real-time distributed event streaming pipelines (such as Apache Kafka or AWS Kinesis).
2. **Operational Proxy for Concept Drift:** Concept drift is inferred from windowed performance drops rather than mathematical information-theoretic divergence measures.
3. **Absence of Local Attribution:** Explainability focuses on systemic operational telemetry; individual instance-level feature attributions (via SHAP or LIME) are not currently integrated into the operational explanations.
4. **Approval Audit Granularity:** The current database schema persists decision recommendations and final approval states, but does not capture reviewer user IDs or secondary approval timestamps in dedicated relational columns.

## 8.4 Future Enhancements

The architectural roadmap for PhoenixML outlines several major enhancements:
1. **Granular Reviewer Audit Logging:** Extending the PostgreSQL schema with dedicated reviewer foreign keys (`reviewed_by` referencing `users.id`), approval timestamps (`approved_at`, `rejected_at`), and an immutable `decision_approval_audit` table to record every authorization event for formal regulatory compliance.
2. **Semi-Automated Maintenance Execution Pipelines:** While maintaining human approval sign-off, introducing worker integrations (e.g., Celery or Temporal) that automatically execute the approved action upon operator authorization (e.g., dispatching retraining jobs or updating proxy routing rules).
3. **Champion-Challenger Shadow Evaluation:** Deploying retrained models into shadow observation pipelines to evaluate comparative performance against active models before operators authorize production traffic switching.
4. **Real-Time Streaming Telemetry:** Ingesting high-throughput prediction streams via Apache Kafka or Redis Streams with windowed streaming aggregators.
5. **Instance-Level Explainability Integration:** Incorporating SHAP TreeExplainer and LIME routines to complement systemic operational explainability with localized feature importance graphs.
6. **Cross-Domain Extension:** Generalizing the platform to supervise models deployed in fraud detection, loan default prediction, and automated medical diagnosis.

## 8.5 Concluding Remarks

PhoenixML demonstrates that post-deployment machine learning governance does not require choosing between passive, confusing alerts and risky autonomous self-healing. By synthesizing multi-source telemetry into explainable recommendations and enforcing human oversight, PhoenixML provides a reliable, secure, and disciplined blueprint for production MLOps engineering.

---

\\newpage


# REFERENCES

1. Sculley, D., Holt, G., Golovin, D., Davydov, E., Phillips, T., Ebner, D., Chaudhary, V., Young, M., Crespo, J.-F., & Dennison, D. (2015). *Hidden Technical Debt in Machine Learning Systems.* Advances in Neural Information Processing Systems (NeurIPS 2015), 28, 2503-2511.
2. Breck, E., Cai, S., Nielsen, E., Salib, M., & Sculley, D. (2017). *The ML Test Score: A Rubric for ML Production Readiness and Technical Debt Reduction.* Proceedings of IEEE Big Data 2017, 1123-1132.
3. Zinkevich, M. (2017). *Rules of Machine Learning: Best Practices for ML Engineering.* Google Research. [Online]. Available: https://developers.google.com/machine-learning/guides/rules-of-ml.
4. IEEE Computer Society. (2009). *IEEE Std 1016-2009: IEEE Standard for Software Design Descriptions.* IEEE Computer Society, Piscataway, NJ.
5. ISO/IEC/IEEE. (2017). *ISO/IEC/IEEE 12207:2017 Systems and Software Engineering - Software Life Cycle Processes.* International Organization for Standardization, Geneva, Switzerland.
6. Géron, A. (2022). *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow: Concepts, Tools, and Techniques to Build Intelligent Systems* (3rd ed.). O'Reilly Media, Sebastopol, CA.
7. Bishop, C. M. (2006). *Pattern Recognition and Machine Learning.* Springer-Verlag, New York, NY.
8. Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep Learning.* MIT Press, Cambridge, MA.
9. Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, E. (2011). *Scikit-learn: Machine Learning in Python.* Journal of Machine Learning Research (JMLR), 12, 2825-2830.
10. Zaharia, M., Chen, A., Davidson, A., Ghodsi, A., Hong, S. A., Konwinski, A., Murching, S., Nykodym, T., Ogilvie, P., Parkhe, M., Xie, F., & Zumar, C. (2018). *Accelerating the Machine Learning Lifecycle with MLflow.* IEEE Data Engineering Bulletin, 41(4), 39-45.
11. Bass, L., Clements, P., & Kazman, R. (2021). *Software Architecture in Practice* (4th ed.). Addison-Wesley Professional, Boston, MA.
12. Richards, M., & Ford, N. (2020). *Fundamentals of Software Architecture: An Engineering Approach.* O'Reilly Media, Sebastopol, CA.
13. Elmasri, R., & Navathe, S. B. (2015). *Fundamentals of Database Systems* (7th ed.). Pearson, Boston, MA.
14. Fielding, R. T. (2000). *Architectural Styles and the Design of Network-based Software Architectures.* Ph.D. dissertation, Department of Information and Computer Science, University of California, Irvine.
15. Jones, M. B., Bradley, J., & Sakimura, N. (2015). *JSON Web Token (JWT).* RFC 7519, Internet Engineering Task Force (IETF). [Online]. Available: https://tools.ietf.org/rfc/rfc7519.txt.
16. Fielding, R. T., Nottingham, M., & Reschke, J. (2022). *HTTP Semantics.* RFC 9110, Internet Engineering Task Force (IETF). [Online]. Available: https://tools.ietf.org/rfc/rfc9110.txt.
17. Tiangolo, S. (2024). *FastAPI Framework Documentation.* [Online]. Available: https://fastapi.tiangolo.com/.
18. PostgreSQL Global Development Group. (2024). *PostgreSQL 16 Documentation.* [Online]. Available: https://www.postgresql.org/docs/.
19. Bayer, M. (2024). *SQLAlchemy: The Database Toolkit for Python.* [Online]. Available: https://www.sqlalchemy.org/.
20. Meta Platforms, Inc. (2024). *React Documentation.* [Online]. Available: https://react.dev/.

---

\\newpage


# APPENDIX

## A. API Reference Summary

Table A.1 provides a complete directory of the RESTful API endpoints implemented in PhoenixML.

Table A.1 - Comprehensive PhoenixML REST API Endpoint Directory

| Functional Group | HTTP Method | Endpoint Path | RBAC Authorization | Description / Function |
|:---|:---:|:---|:---|:---|
| **Health Check** | `GET` | `/health` | Public | Root service liveness check |
| **Health Check** | `GET` | `/api/health` | Public | API operational status and project name |
| **Authentication**| `POST`| `/api/auth/login` | Public | Authenticate credentials and issue JWT tokens |
| **Authentication**| `POST`| `/api/auth/refresh` | Public | Issue new access token using valid refresh token |
| **Authentication**| `POST`| `/api/auth/logout` | Authenticated | Invalidate active user session |
| **Authentication**| `POST`| `/api/auth/register` | Public / Admin | Register a new user account |
| **User Profile** | `GET` | `/api/users/me` | Authenticated | Retrieve authenticated user profile |
| **User Profile** | `PATCH`| `/api/users/me` | Authenticated | Update user profile attributes |
| **User Profile** | `POST`| `/api/users/me/change-password` | Authenticated | Change account password with verification |
| **Model Registry** | `GET` | `/api/spam-models` | `ADMIN`, `ML_ENGINEER`, `VIEWER` | List registered models (scoped by user ownership) |
| **Model Registry** | `POST`| `/api/spam-models` | `ADMIN`, `ML_ENGINEER` | Register a new spam classification model |
| **Model Registry** | `GET` | `/api/spam-models/{model_id}` | `ADMIN`, `ML_ENGINEER`, `VIEWER` | Retrieve specific model metadata |
| **Model Registry** | `PUT` | `/api/spam-models/{model_id}` | `ADMIN`, `ML_ENGINEER` | Update registered model metadata |
| **Model Registry** | `DELETE`| `/api/spam-models/{model_id}` | `ADMIN`, `ML_ENGINEER` | Delete registered model (cascades to telemetry) |
| **Monitoring** | `POST`| `/api/spam-models/{model_id}/monitoring` | `ADMIN`, `ML_ENGINEER` | Ingest a runtime monitoring observation |
| **Monitoring** | `GET` | `/api/spam-models/{model_id}/monitoring` | `ADMIN`, `ML_ENGINEER`, `VIEWER` | List monitoring observations (paginated) |
| **Monitoring** | `GET` | `/api/spam-models/{model_id}/monitoring/{obs_id}`| `ADMIN`, `ML_ENGINEER`, `VIEWER` | Retrieve single observation record |
| **Monitoring** | `DELETE`| `/api/spam-models/{model_id}/monitoring/{obs_id}`| `ADMIN`, `ML_ENGINEER` | Delete specific observation record |
| **Decision Support**| `POST`| `/api/spam-models/{model_id}/decisions/evaluate` | `ADMIN`, `ML_ENGINEER` | Trigger AIMD evaluation across observations |
| **Decision Support**| `GET` | `/api/spam-models/{model_id}/decisions` | `ADMIN`, `ML_ENGINEER`, `VIEWER` | List paginated decision history (newest first) |
| **Decision Support**| `GET` | `/api/spam-models/{model_id}/decisions/{decision_id}`| `ADMIN`, `ML_ENGINEER`, `VIEWER` | Retrieve single decision record |
| **Decision Support**| `PATCH`| `/api/spam-models/{model_id}/decisions/{decision_id}/approval`| `ADMIN`, `ML_ENGINEER` | Update human approval (`APPROVED`/`REJECTED`)|
| **Dashboard** | `GET` | `/api/dashboard` | `ADMIN`, `ML_ENGINEER`, `VIEWER` | Retrieve consolidated fleet dashboard overview |
| **Dashboard** | `GET` | `/api/dashboard/{model_id}` | `ADMIN`, `ML_ENGINEER`, `VIEWER` | Retrieve single-model dashboard overview |
| **Operator UI** | `GET` | `/ui/` | Public / Web Browser | Interactive operator dashboard Single Page App |
| **Operator UI** | `GET` | `/` | Public / Web Browser | Root redirect to `/ui/` dashboard entrypoint |

## B. Database Schema Reference

PhoenixML utilizes four relational tables in PostgreSQL:
1. `users`: Stores user identity, salted bcrypt password hash, account status, and role enum (`ADMIN`, `ML_ENGINEER`, `VIEWER`).
2. `registered_models`: Stores model identity name (e.g. `SpamGuard-v1`), framework, algorithm, deployment status enum (`DEVELOPMENT`, `ACTIVE`, `ARCHIVED`), and foreign key `owner_id` referencing `users.id` with `ON DELETE CASCADE`.
3. `monitoring_observations`: Stores runtime observation timestamps, prediction volumes (total, spam, ham), and performance metrics (accuracy, precision, recall, F1) with foreign key `model_id` referencing `registered_models.id` (`ON DELETE CASCADE`).
4. `decision_logs`: Stores evaluated health score, health status, recommended action (`aimdaction`), urgency priority (`aimdpriority`), evidence confidence, justification rationale, diagnostic explanation, JSON supporting signals, `requires_human_approval` (default `True`), and approval status (`approvalstatus`: `PENDING`, `APPROVED`, `REJECTED`) with foreign key `model_id` referencing `registered_models.id` (`ON DELETE CASCADE`).

## C. Configuration & Deployment Instructions

PhoenixML configuration is centralized in `backend/app/core/config.py` using Pydantic `BaseSettings`. Table C.1 documents primary parameters.

Table C.1 - Core System Configuration Parameters

| Configuration Variable | Default Value | Environment Override | Operational Description |
|:---|:---|:---|:---|
| `PROJECT_NAME` | `"PhoenixML"` | `PROJECT_NAME` | Application identifier display name |
| `API_V1_STR` | `"/api"` | `API_V1_STR` | Global REST API prefix route |
| `DEBUG` | `False` | `DEBUG` | FastAPI debug mode flag |
| `DATABASE_URL` | `"postgresql://postgres:...@localhost:5432/phoenixml"` | `DATABASE_URL` | PostgreSQL connection URI |
| `JWT_SECRET_KEY` | `""` (Secret) | `JWT_SECRET_KEY` | Cryptographic secret for signing HMAC-SHA256 JWTs |
| `JWT_ALGORITHM` | `"HS256"` | `JWT_ALGORITHM` | Asymmetric or symmetric signature algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | `ACCESS_TOKEN_EXPIRE_MINUTES` | Lifespan duration for JWT access tokens |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | `REFRESH_TOKEN_EXPIRE_DAYS` | Lifespan duration for JWT refresh tokens |
| `HEALTHY_THRESHOLD` | `80.0` | `HEALTHY_THRESHOLD` | Composite health boundary for `HEALTHY` state |
| `WARNING_THRESHOLD` | `60.0` | `WARNING_THRESHOLD` | Composite health boundary for `WARNING` state |
| `DATA_DRIFT_ALPHA` | `0.05` | `DATA_DRIFT_ALPHA` | Significance level for two-sample KS-tests |
| `CONCEPT_DRIFT_THRESHOLD`| `0.05` | `CONCEPT_DRIFT_THRESHOLD`| Performance degradation delta threshold |

### Local Deployment Instructions:
1. Initialize virtual environment:
   ```bash
   python -m venv .venv
   .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```
2. Configure environment variables in `.env`:
   ```bash
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/phoenixml
   JWT_SECRET_KEY=your-secure-random-secret-key-at-least-32-chars
   ```
3. Execute database migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```
4. Launch the application:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
5. Access the operator dashboard at `http://localhost:8000/ui/` or interactive OpenAPI docs at `http://localhost:8000/docs`.

## D. Test Suite Summary

The automated test suite comprises **439 passing tests** across **32 dedicated test modules**:
1. `tests/test_auth.py` (5 tests)
2. `tests/test_login.py` (7 tests)
3. `tests/test_logout.py` (6 tests)
4. `tests/test_refresh.py` (8 tests)
5. `tests/test_profile.py` (10 tests)
6. `tests/test_security.py` (7 tests)
7. `tests/test_dependencies.py` (4 tests)
8. `tests/test_rbac.py` (8 tests)
9. `tests/test_model_registry_api.py` (17 tests)
10. `tests/test_model_registry_service.py` (7 tests)
11. `tests/test_model_registry_db.py` (8 tests)
12. `tests/test_model_registry_integration.py` (1 test)
13. `tests/test_monitoring_api.py` (14 tests)
14. `tests/test_monitoring_service.py` (9 tests)
15. `tests/test_monitoring_db.py` (13 tests)
16. `tests/test_monitoring_api_integration.py` (12 tests)
17. `tests/test_health_assessment.py` (14 tests)
18. `tests/test_performance_analysis.py` (19 tests)
19. `tests/test_data_drift.py` (13 tests)
20. `tests/test_concept_drift.py` (31 tests)
21. `tests/test_explainability.py` (22 tests)
22. `tests/test_aimd.py` (32 tests)
23. `tests/test_decision_log_db.py` (55 tests)
24. `tests/test_decision_service.py` (14 tests)
25. `tests/test_decision_query_service.py` (14 tests)
26. `tests/test_database_integration_persistence.py` (7 tests)
27. `tests/test_decision_api.py` (13 tests)
28. `tests/test_decision_evaluation_api.py` (17 tests)
29. `tests/test_decision_approval_api.py` (19 tests)
30. `tests/test_dashboard_api.py` (16 tests)
31. `tests/test_dashboard_ui.py` (9 tests)
32. `tests/test_system_integration_workflow.py` (8 tests)

- **Total Test Modules:** 32
- **Total Tests Passed:** 439 (0 failures, 4 warnings)
- **Execution Duration:** ~178.6 seconds (~2 minutes 58 seconds)

## E. Demonstration Walkthrough & Interface Specifications

The operational demonstration of `SpamGuard-v1` is captured across twelve primary interface views:
1. **Figure E.1 - Operator Login View:** Web browser rendering `http://localhost:8000/ui/` displaying brand headers, OAuth2 email/password input fields, role hint banner, and sign-in button.
2. **Figure E.2 - Operator Dashboard Overview:** The primary executive view showing fleet-wide model inventory counters, active observation totals, average system health score progress meters, and pending approval alerts.
3. **Figure E.3 - Model Registry View:** Model inventory table displaying registered models (`SpamGuard-v1`), active frameworks (`scikit-learn`), classification algorithms (`MultinomialNB`), deployment status tags, and model ownership.
4. **Figure E.4 - Monitoring Observations & Telemetry Visualizations:** Chronological observation table showing ingested telemetry records (accuracy, precision, recall, F1-score, prediction counts) and trend indicators.
5. **Figure E.5 - Health Score Meter and Status Classification:** Detailed model health card displaying the normalized 0-100 composite health score (e.g., 66.7/100 for degraded state), health status badge (`WARNING`), and individual normalized metric bars.
6. **Figure E.6 - Feature Data Drift Statistical Summary:** Drift report panel showing evaluated continuous feature distributions, two-sample KS test statistics, computed $p$-values, significance threshold ($\alpha = 0.05$), and drift status flags.
7. **Figure E.7 - AIMD Recommendation Review Card:** Operator recommendation card rendering the suggested action (`HUMAN_REVIEW`), priority badge (`HIGH`/`MEDIUM`), confidence score (`0.70`), human-readable rationale narrative, and mandatory HITL advisory banner.
8. **Figure E.8 - Diagnostic Explainability & Corroborating Signals:** Expanded modal detailing prioritized operational signals, primary degradation factors, and associative evidence summaries synthesized from the explainability layer.
9. **Figure E.9 - Human Approval Workflow Modal:** Operator dialog rendering the interactive "Approve" and "Reject" action triggers, displaying `requires_human_approval = True` and state transition confirmation.
10. **Figure E.10 - Decision History & Audit Trail Table:** Historical audit log table displaying persisted `decision_logs` records, evaluation timestamps (UTC), recommended actions, rationales, and finalized approval states (`APPROVED`).
11. **Figure E.11 - Interactive OpenAPI (Swagger UI) Interface:** Interactive FastAPI documentation rendered at `http://localhost:8000/docs`, showing all functional endpoint groups, request schemas, and authorization locks.
12. **Figure E.12 - PostgreSQL Schema Migration Verification:** Terminal execution output demonstrating clean Alembic migration status (`alembic current` showing `c30a5d242a96`) and verified PostgreSQL database tables.

---
DOCUMENT STATUS: First complete draft
SOURCE OF TRUTH: Current PhoenixML implementation + current project documentation
---
