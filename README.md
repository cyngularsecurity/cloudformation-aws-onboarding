# Cyngular AWS Client Onboarding

Automated deployment of security monitoring infrastructure for AWS accounts using CloudFormation StackSets.

## Quick Start

1. Configure client parameters in `.env` file
2. Run deployment: `./Scripts/RainDeployOB.sh`
3. Monitor deployment: `rain log <stack-name> --chart`

## Documentation

- [Deployment Instructions](./docs/INSTRUCTIONS.md) - Prerequisites and deployment steps
- [Service Configuration](./docs/CYNGULAR_SERVICES.md) - Service enablement options
- [Architecture Diagrams](./Charts/) - Visual workflow and architecture diagrams

## Architecture

**Gen3 (Current)**: Managed StackSets with automated region discovery
- `CFN/Gen3/` - CloudFormation templates
- `Lambdas/Services/` - Service orchestration lambdas
- Auto-discovers all enabled regions

**Gen2 (Legacy)**: Custom Lambda-managed StackSets
- `CFN/CyngularOnBoarding.yaml` - Monolithic template
- Manual region specification required

## Key Features

- Cross-account security monitoring
- Multi-region automated deployment
- Service-based architecture (DNS, VFL, EKS, OS)
- Organization-wide StackSet support
- Production-grade error handling and metrics

## Requirements

- AWS CLI configured
- Rain CLI (`brew install rain`)
- AWS Organizations (if using org deployment)
- Appropriate IAM permissions

See [CLAUDE.md](./CLAUDE.md) for detailed development guidance.