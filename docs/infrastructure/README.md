# Infrastructure and Environments

Cloud landing zone, IaC, CI/CD, and observability blueprint.

## Environments
- `dev` (sandbox), `staging` (pre-prod), `prod` (segregated)
- Per-env accounts/projects, strict IAM boundaries

## IaC Patterns
- Terraform/Pulumi with modules and policy-as-code
- GitOps for infra changes and drift detection

## Observability
- Centralized logs, metrics, traces; SLOs and error budgets
- Runbooks and on-call rotations
