
# Off Boarding

1. Manualy Invoke "remove" lambdas - in every client account

  * remove-dns
  * remove-vpcflowlogs

2. Delete all objects in cyngular logs s3 bucket

3. Manualy delete Stacksets - in mgmgt account (delete stacks from stacksets, then stacksets)
    * mgmt-regional - mgmt account scope
    * StackSet-1 & stackset-2 - OU scope
    * exec role stackset - OU scope

4. Delete main stack of stacksets
