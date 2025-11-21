# Manual Deployment Guide (AWS Console)

This guide walks you through deploying the CloudFormation stacks and StackSets via the AWS Console.

## Part 1: Deploy Management Acount CloudFormation Stacks

You will create three stacks, in the following order in your chosen region (RUNTIME_REGION):

1) ReadonlyRole
2) Core
3) Services

All templates are in this repository under `CFN/`. If you are in the AWS Console, choose “Upload a template file” and select the file from your local clone.

### 1. ReadonlyRole stack

- GoTo: CloudFormation > Stacks > Create stack > With new resources (standard)
- Template: Upload `CFN/ReadonlyRole.yaml`
- Stack name: `${CLIENT_NAME}-ro-role`
- Parameters:
  - ClientName = <`client company name`>
  - CyngularAccountId = 851565895544

<!-- Note: Parameter names must match exactly as shown below. StackSets do not support unknown parameters; only supply those listed. -->

- Acknowledge required Capabilities
- Create stack and wait for completion

### 2. Core stack

- GoTo: CloudFormation > Stacks > Create stack
- Template: Upload `CFN/Core.yaml`
- Stack name: `${CLIENT_NAME}-core`
- Parameters (use what applies to your setup):
  - ClientName = <`client company name`>
  - OrganizationId = <`organization id`>

  - EnableCloudTrail = true/false
  - EnableBucketPolicyManager = true/false

  - CyngularAccountId = 851565895544

- Acknowledge required Capabilities
- Create stack and wait for completion

### 3. Services stack

- GoTo: CloudFormation > Stacks > Create stack
- Template: Upload `CFN/Services.yaml`
- Stack name: `${CLIENT_NAME}-services`
- Parameters (align with your Core parameters):
  - ClientName = <`client company name`>
  - ClientMgmtAccountId = ClientMgmtAccountId (required when deploying in organizations)

  - EnableDNS = true/false
  - EnableVPCFlowLogs = true/false
  - EnableEKS = true/false

  - ServiceManagerOverride = integer (default: 1)
  - ExcludedRegions = ExcludedRegions (optional)

- Acknowledge required Capabilities
- Create stack and wait for completion

## Part 2: Deploy Organization-Scoped StackSets

You will create two StackSets, then add instances targeting your OUs in your chosen region(s).

- GoTo: CloudFormation > StackSets > Create StackSet
- Permission model: SERVICE MANAGED
- Auto-deployment: Enabled (retain stacks on account removal: typically false, set to true only if deletion is required and the stack instances are stuck)
- Managed execution: Active
- Acknowledge required Capabilities

### A. ReadonlyRole StackSet

- Name: `${CLIENT_NAME}-role`
- Template: Upload `CFN/ReadonlyRole.yaml`
- Parameters:
  - ClientName = <`client company name`>
  - CyngularAccountId = 851565895544
- Create StackSet

Add Stack Instances:

- Deployment targets: Organizational Units
- OrganizationalUnitIds: one or more values from ORGANIZATIONAL_UNIT_IDS
- Regions: RUNTIME_REGION (to deploy the stacks in - cyngular will still manage all but excleded)
- Deployment options:
  - Maximum concurrent accounts: Precentage - 90
  - Failure tolerance: Precentage - 70
  - Region concurrency = Sequential (only single region)
  - Optionally tune: FailureTolerancePercentage, MaxConcurrentPercentage
- Acknowledge required Capabilities
- Submit and wait for operation to succeed

### B. Services StackSet

- Name: `${CLIENT_NAME}-services`
- Template: Upload `CFN/Services.yaml`
- Parameters:
  - ClientName = <`client company name`>
  - EnableDNS = true/false
  - EnableVPCFlowLogs = true/false
  - EnableEKS = true/false
  - ServiceManagerOverride = increase numeric to force trigger of the lambda from cloudformation stack. integer (default: 1)
  - ExcludedRegions = list of regions to exclude from cyngular scan (optional)
  - ClientMgmtAccountId = ClientMgmtAccountId (required when deploying in organizations)
<!-- - Create StackSet

Add Stack Instances: -->

- Deployment targets: Organizational Units
- OrganizationalUnitIds: one or more values from ORGANIZATIONAL_UNIT_IDS
- Regions: RUNTIME_REGION (and any additional regions required)
- Operation preferences (optional):
  - RegionConcurrencyType = PARALLEL
  - FailureTolerancePercentage (e.g., 25)
  - MaxConcurrentPercentage (e.g., 50)
- Acknowledge required Capabilities
- Submit and wait for operation to succeed

## Validation

- Stacks: Verify all three stacks show CREATE_COMPLETE in the target region.
- StackSets: Verify latest operations are SUCCEEDED and that instances are created in target accounts/OUs and regions.
- Services functionality: if DNS, VPC Flow Logs, or EKS were enabled, verify the corresponding resources/policies exist.

## Notes & Troubleshooting

- Parameter names are case-sensitive and must match the template defined types.
- If you use your own S3 buckets (e.g., CloudTrail, VPC Flow Logs), ensure required tags and bucket policies are applied, See `docs/INSTRUCTIONS.md`.
- If StackSet creation fails due to permissions, re-check that CloudFormation StackSets trusted access is enabled in AWS Organizations, and that your admin account has required permissions.
- To change rollout speed/reliability, adjust FailureTolerancePercentage and MaxConcurrentPercentage during stack instance creation.
