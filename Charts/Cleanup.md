
# Client Offboarding Process

This document outlines the high-level process for decommissioning Cyngular monitoring infrastructure.

## Offboarding Overview

The offboarding process reverses the deployment flow in the following order:

### 1. Service Cleanup

**Note:** To install cleanup Lambda functions, use the `CFN/Cleanup.yaml` CloudFormation template. [Create per account / region with stacksets]

- Clean up DNS logging configurations (remove-dns)
- Clean up VPC Flow Logs configurations (remove-vpcflowlogs)

**Note:** or delete the query logging configurations named 'cyngular-dns' per region per account manually.

### 2. S3 Bucket Cleanup

- Delete all objects in Cyngular logging S3 bucket
- Remove cyngular S3 bucket created for log collection

### 3. StackSet Decommissioning (When using org, or multi region)

In the management account, remove StackSets in reverse deployment order:

**a) Services StackSet (`${CLIENT_NAME}-services`)**

- Delete stack instances from all organizational units and regions
- Delete the Services StackSet itself

**b) ReadonlyRole StackSet (`${CLIENT_NAME}-role`)**

- Delete stack instances from all organizational units
- Delete the ReadonlyRole StackSet itself

### 4. Core Stack Cleanup

In the management account, remove the foundational CloudFormation stacks:

- Delete Services stack (`${CLIENT_NAME}-services`)
- Delete Core stack (`${CLIENT_NAME}-core`)
- Delete ReadonlyRole stack (`${CLIENT_NAME}-ro-role`)

<!-- All resources follow the naming convention `${CLIENT_NAME}-*` for easy identification during cleanup. -->
