## General Notes & Cavieates

* Organization Id is required only if deploying to an organization, from the management account,
deployment to an org from a member account will fail on cloudtrail permissions.

* ClientRegions contains all the regions the client is operation in,
the client main region, included in the list but determind by the region the main stack is deployed to.
