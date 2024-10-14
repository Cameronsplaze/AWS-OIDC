
# Github AWS OIDC

To let GitHub Actions deploy to AWS. Only one stack can exist per account, so had to move this logic to it's own repo.

Look at [./AccessConfigOIDC.yaml](./AccessConfigOIDC.yaml) for adding more repos/branches to your whitelist.

## Deploying / Developing

This project uses the [./makefile](./makefile) to help streamline deploying/developing.

```bash
# Make sure your cdk creds are configured correctly for the right account:
make aws-whoami
# Synth the Stack:
make cdk-synth
# Deploy the Stack:
make cdk-deploy
```
