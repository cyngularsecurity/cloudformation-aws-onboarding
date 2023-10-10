
## Product Side - Env Per Deployment region

- Secret Manager

- Vpc
- Internet Gateway
- S3 Vpc Endpoint

- for AZ 1 & 2 
    * Private Subnet
        - Route table for each private Subnets
        - Nat route at each + Elastic Ip's

    * Public Subnet
        - Same route table for two public Subnets:
        - With Outbound through Internet Gateway route

- DBSubnetGroup
- Security Group (DB)
- DBInstance [RDS, Postgress] (? Athena)

- Bastion:
    * Bastion Key Pair
    * Bastion Security Group

    * Bastion EC2 Instance
    * Bastion EIP

- Api:
    * Api Key Pair
    * Api Security Group

    * Api EC2 Instance
    * Api EIP

    * EC2 Role
    * EC2 Instance Profile

- Frontend:
    * Frontend Key Pair
    * Frontend Security Group

    * Frontend EC2 Instance
    * Frontend EIP

    * EC2 Role
    * EC2 Instance Profile

- Backend:
    * Backend Key Pair
    * Backend Security Group

    * Backend EC2 Instance

    * EC2 Role
    * EC2 Instance Profile 


 <!-- ------------------------------------------------------------------------ -->
## Steps

1. onboarding.py updates the ec2's userdata

## Per Region
2. Create bucket, upload lambda code in zip files

3. Create stack with "RegionDeployment-updated.yaml" Cloudformation template & insert the parameters

4. Insert the proper values into the Region secret manager

5. Run the cyngular-lambda-configure-resources lambda after the regionaldeployment was created (and api ec2 is running)

6. Create ssl certificate and configure it on api server (? service_config/nginx_config.sh)

7. Copy backend project into backend ec2 and run backend_init.sh with the proper secret values

8. Copy the frontend project into frontend ec2 and run npm i


 <!-- ------------------------------------------------------------------------ -->
## Client Side - Per Client

* Secret Manager

* IAM Role - Product Role

* Linuc Instance Profile

### SQS Queues
* CloudService
* EKSLogs
* Linux
* RDS

### DynamoDB Tables
* Cloud
* EKSLogs
* Linux

* Product Lambda IAM Role

### Lambda Functions
* Cloud Service
    - Lambda A, B, C
    - Event Rule & Premission

* Cloud Service EKS Logs
    - Lambda A, B, C

* Linux Service
    - Lambda A, B

* Visibility Service
    - Lmabda A, B

* EC2   
    - DB Instance

* EventBridge Schedual
    - Invoke Function Daily
        * Cloud
        * Visibility
        * EKS
        * Linux


 <!-- ------------------------------------------------------------------------ -->
## Per Client:
9. Create the second stack for every new client in the correct region with the "ClientDeployment.yaml" template at AWS Cloudformation and insert the parametes (some of them are outputs from region deployment). 

10. Insert the proper values into the Client secret manager

11. Run the Database_Init lambda for the new client

* After the stack has been created, the Key pairs of the services will be created at the Parameter Store in AWS. 
    Insert the values to key files, delete them in the Parameter Store.
    
<!-- ** Each region that you run stacks takes 5 Elastic Ips -->