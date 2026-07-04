CREATE TABLE organizations (
	id CHAR(36) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	slug VARCHAR(255) NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (slug)
);

CREATE TABLE retry_policies (
	id CHAR(36) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	strategy ENUM('fixed','linear','exponential') NOT NULL, 
	max_retries INTEGER NOT NULL, 
	base_delay_seconds INTEGER NOT NULL, 
	max_delay_seconds INTEGER NOT NULL, 
	jitter BOOL NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id)
);

CREATE TABLE users (
	id CHAR(36) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	full_name VARCHAR(255) NOT NULL, 
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (email)
);

CREATE TABLE org_members (
	id CHAR(36) NOT NULL, 
	user_id CHAR(36) NOT NULL, 
	org_id CHAR(36) NOT NULL, 
	`role` ENUM('owner','admin','member') NOT NULL, 
	joined_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_org_members_user_org UNIQUE (user_id, org_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

CREATE TABLE projects (
	id CHAR(36) NOT NULL, 
	org_id CHAR(36) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	slug VARCHAR(255) NOT NULL, 
	description TEXT, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_projects_org_slug UNIQUE (org_id, slug), 
	FOREIGN KEY(org_id) REFERENCES organizations (id) ON DELETE CASCADE
);

CREATE TABLE queues (
	id CHAR(36) NOT NULL, 
	project_id CHAR(36) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	slug VARCHAR(255) NOT NULL, 
	priority INTEGER NOT NULL, 
	concurrency_limit INTEGER NOT NULL, 
	retry_policy_id CHAR(36), 
	is_paused BOOL NOT NULL, 
	max_job_duration_seconds INTEGER NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	updated_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_queues_project_slug UNIQUE (project_id, slug), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE, 
	FOREIGN KEY(retry_policy_id) REFERENCES retry_policies (id)
);

CREATE TABLE scheduled_jobs (
	id CHAR(36) NOT NULL, 
	queue_id CHAR(36) NOT NULL, 
	cron_expression VARCHAR(100) NOT NULL, 
	payload JSON NOT NULL, 
	is_active BOOL NOT NULL, 
	next_run_at DATETIME NOT NULL, 
	last_run_at DATETIME, 
	created_by CHAR(36) NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(queue_id) REFERENCES queues (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE TABLE workers (
	id CHAR(36) NOT NULL, 
	hostname VARCHAR(255) NOT NULL, 
	pid INTEGER NOT NULL, 
	queue_id CHAR(36), 
	status ENUM('online','busy','draining','offline') NOT NULL, 
	concurrency INTEGER NOT NULL, 
	active_jobs INTEGER NOT NULL, 
	registered_at DATETIME NOT NULL DEFAULT now(), 
	last_heartbeat_at DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(queue_id) REFERENCES queues (id)
);

CREATE TABLE jobs (
	id CHAR(36) NOT NULL, 
	queue_id CHAR(36) NOT NULL, 
	type ENUM('immediate','delayed','scheduled','recurring','batch') NOT NULL, 
	status ENUM('queued','scheduled','claimed','running','completed','failed','dead_lettered','cancelled') NOT NULL, 
	priority INTEGER NOT NULL, 
	payload JSON NOT NULL, 
	result JSON, 
	attempt_count INTEGER NOT NULL, 
	max_retries INTEGER NOT NULL, 
	created_by CHAR(36) NOT NULL, 
	worker_id CHAR(36), 
	batch_id CHAR(36), 
	created_at DATETIME NOT NULL DEFAULT now(), 
	scheduled_at DATETIME, 
	claimed_at DATETIME, 
	started_at DATETIME, 
	completed_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(queue_id) REFERENCES queues (id) ON DELETE CASCADE, 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(worker_id) REFERENCES workers (id)
);

CREATE TABLE worker_heartbeats (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	worker_id CHAR(36) NOT NULL, 
	active_jobs INTEGER NOT NULL, 
	cpu_usage FLOAT, 
	memory_usage FLOAT, 
	timestamp DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(worker_id) REFERENCES workers (id) ON DELETE CASCADE
);

CREATE TABLE dead_letter_queue (
	id CHAR(36) NOT NULL, 
	job_id CHAR(36) NOT NULL, 
	queue_id CHAR(36) NOT NULL, 
	failure_reason TEXT NOT NULL, 
	last_error TEXT, 
	total_attempts INTEGER NOT NULL, 
	dead_lettered_at DATETIME NOT NULL DEFAULT now(), 
	requeued_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (job_id), 
	FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE, 
	FOREIGN KEY(queue_id) REFERENCES queues (id)
);

CREATE TABLE job_executions (
	id CHAR(36) NOT NULL, 
	job_id CHAR(36) NOT NULL, 
	worker_id CHAR(36) NOT NULL, 
	attempt_number INTEGER NOT NULL, 
	status ENUM('running','completed','failed','timed_out') NOT NULL, 
	started_at DATETIME NOT NULL DEFAULT now(), 
	completed_at DATETIME, 
	duration_ms INTEGER, 
	error_message TEXT, 
	error_traceback TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE, 
	FOREIGN KEY(worker_id) REFERENCES workers (id)
);

CREATE TABLE job_logs (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	job_id CHAR(36) NOT NULL, 
	execution_id CHAR(36), 
	level ENUM('debug','info','warn','error') NOT NULL, 
	message TEXT NOT NULL, 
	timestamp DATETIME NOT NULL DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(job_id) REFERENCES jobs (id) ON DELETE CASCADE, 
	FOREIGN KEY(execution_id) REFERENCES job_executions (id)
);
