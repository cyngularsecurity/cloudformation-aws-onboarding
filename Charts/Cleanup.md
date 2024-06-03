
# Off Boarding
0. Manualy Invoke deletion lambdas - in every account
  * VFL & Resources
  * add delete lambdas to all accounts

0. Delete all objects in cyngular logs s3 bucket

0. Manualy delete Stacksets - in mgmgt account
    * Stack-2
    * StackSet-1 & StackSet-2
       * Delete Instances from stacksets
       * delete the stacksets
    * Delete exec role stackset

0. Delete main stack of stacksets

https://console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/create/review?templateURL=https://cyngular-onboarding-templates.s3.amazonaws.com/stacks/stack1.yaml&stackName=cyngular-onboarding