.PHONY: virtual install build-requirements black isort flake8 unit-test feature-test terraform-apply terraform-destroy wait-circle sync-barn

install: virtual
	.venv/bin/pip install -Ur requirements.txt

.venv/bin/pip:
	virtualenv .venv

virtual: .venv/bin/pip # Creates an isolated python 3 environment

update-requirements: install
	.venv/bin/pip freeze > requirements.txt

.venv/bin/black:
	.venv/bin/pip install -U black

.venv/bin/isort:
	.venv/bin/pip install -U isort

.venv/bin/flake8:
	.venv/bin/pip install -U flake8

.venv/bin/pytest:
	.venv/bin/pip install -U pytest

.venv/bin/pytest-bdd:
	.venv/bin/pip install -U pytest-bdd

.venv/bin/aws:
	.venv/bin/pip install -U awscli

.venv/bin/coverage:
	.venv/bin/pip install -U coverage

black: .venv/bin/black # Formats code with black
	.venv/bin/black handlers/*.py tests --check

isort: .venv/bin/isort # Sorts imports using isort
	.venv/bin/isort handlers/*.py tests --check-only

flake8: .venv/bin/flake8 # Lints code using flake8
	.venv/bin/flake8 handlers/*.py tests --exclude .git,__pycache__,.venv

conformity-tests: black isort flake8

unit-tests: .venv/bin/pytest # Runs unit tests
	cd handlers;AWS_DEFAULT_REGION="us-east-1" ../.venv/bin/pytest ../tests/unit

coverage-test: .venv/bin/pytest .venv/bin/coverage
	cd handlers;AWS_DEFAULT_REGION="us-east-1" ../.venv/bin/coverage run -m pytest ../tests/unit;../.venv/bin/coverage report -m

feature-tests: .venv/bin/pytest-bdd # Runs feature tests locally
	echo $$GMAIL_ACCESS_TOKEN > gmail_token.json
	echo $$GMAIL_CLIENT_SECRET > client_secret.json
	.venv/bin/py.test tests/features --gherkin-terminal-reporter-expanded


ci-tests: # Runs feature tests in CircleCI
	echo $$GMAIL_ACCESS_TOKEN > gmail_token.json
	echo $$GMAIL_CLIENT_SECRET > client_secret.json
	mkdir test-results
	BARN_BUCKET=$(shell cat barn_bucket) .venv/bin/pytest tests/features --junitxml=test-results/features.xml
#	cd handlers;../.venv/bin/pytest ../tests/unit --junitxml=../test-results/unit.xml
## Unit tests disabled pending moto bugfix https://github.com/spulec/moto/pull/3763

.bin/terraform: # Installs Terraform
	mkdir -p tests/.bin
	curl -L -o tests/.bin/terraform.zip https://releases.hashicorp.com/terraform/0.14.10/terraform_0.14.10_linux_amd64.zip
	unzip tests/.bin/terraform.zip
	mv terraform tests/.bin/
	chmod +x tests/.bin/terraform

terraform-apply: .bin/terraform
	cd tests;.bin/terraform init;.bin/terraform apply -auto-approve;.bin/terraform output -raw barn_bucket | tee ../barn_bucket;cd ..

terraform-destroy: .bin/terraform
	cd tests;.bin/terraform destroy -auto-approve;cd ..

wait-circle:
	-curl https://meadow-testing.grassfed.tools/signup;while [ "$$?" != "0" ];do sleep 1; curl https://meadow-testing.grassfed.tools/signup;done;sleep 60

sync-barn: .venv/bin/aws
	wget https://github.com/GrassfedTools/barn-email-templates/releases/download/v1.1.0/transactional.tar.gz;tar -zxvf transactional.tar.gz;.venv/bin/aws s3 cp transactional s3://$(shell cat barn_bucket)/transactional --recursive
