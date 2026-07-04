# ApexScheduler: Enterprise Multi-Tenant Job Engine

A high-concurrency, horizontally scalable distributed job scheduler engineered from scratch for multi-tenant background processing. Built with FastAPI and PostgreSQL, this system implements advanced row-level locking patterns to guarantee strict task isolation and zero-race-condition queue pulling under heavy concurrent loads.

---

## 🏗️ System Architecture

The core architecture decouples ingestion from execution to ensure high throughput and horizontal scalability:

- **API Ingestion Nodes:** Stateless FastAPI instances handle tenant authentication, job submission validation, and real-time analytical reporting.
- **Database Layer:** A centralized PostgreSQL database utilizing optimized `JSONB` indices for flexible task payloads and status indexing.
- **Worker Node Cluster:** Independent background worker processes running concurrent execution loops, capable of scaling dynamically to meet queue demands.

<p align="center">
  <img src="System_architecture.png" width="900">
</p>

---

## 🗄️ Database Entity Relationship (ER)

The relational schema is built on strict multi-tenant normalization rules:

- Ensures data isolation between distinct tenant organizations via foreign key cascading constraints.
- Utilizes a highly optimized compound index on `(status, run_at, priority DESC)` within the core jobs table to minimize polling overhead.

<p align="center">
  <img src="DB_ER.png" width="900">
</p>
