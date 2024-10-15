SHELL:=/bin/bash
.SILENT:
MAKEFLAGS += --no-print-directory
# Default action:
.DEFAULT_GOAL := cdk-synth



#########################
## Generic CDK Helpers ##
#########################

.PHONY := cdk-synth
cdk-synth:
	echo "Synthesizing Stack..."
	echo ""
	cdk synth

.PHONY := cdk-deploy
cdk-deploy:
	echo "Deploying the Stack..."
	echo "Starting at: `date +'%-I:%M%P (%Ss)'`"
	echo ""
	cdk deploy GithubOidcStack --require-approval never
	echo "Finished at: `date +'%-I:%M%P (%Ss)'`"

.PHONY := cdk-destroy
cdk-destroy:
	echo "Destroying the Stack..."
	echo "Starting at: `date +'%-I:%M%P (%Ss)'`"
	echo ""
	cdk destroy GithubOidcStack --force
	echo "Finished at: `date +'%-I:%M%P (%Ss)'`"

###################
## Misc Commands ##
###################

.PHONY := aws-whoami
aws-whoami:
	# Make sure you're in the right account
	aws sts get-caller-identity \
		--query "$${query:-Arn}" \
		--output text
