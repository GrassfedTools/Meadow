.PHONY: virtual install build-requirements black isort flake8 unit-test feature-test terraform-apply terraform-destroy wait-circle

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

black: .venv/bin/black # Formats code with black
	.venv/bin/black handlers/*.py tests --check

isort: .venv/bin/isort # Sorts imports using isort
	.venv/bin/isort handlers/*.py tests --check-only

flake8: .venv/bin/flake8 # Lints code using flake8
	.venv/bin/flake8 handlers/*.py tests --exclude .git,__pycache__,.venv

conformity-tests: black isort flake8

unit-tests: .venv/bin/pytest # Runs unit tests
	cd handlers;../.venv/bin/pytest ../tests/unit

feature-tests: .venv/bin/pytest-bdd # Runs feature tests locally
	echo $$GMAIL_ACCESS_TOKEN > gmail_token.json
	echo $$GMAIL_CLIENT_SECRET > client_secret.json
	.venv/bin/py.test tests/features --gherkin-terminal-reporter-expanded

ci-tests: # Runs feature tests in CircleCI
	echo $$GMAIL_ACCESS_TOKEN > gmail_token.json
	echo $$GMAIL_CLIENT_SECRET > client_secret.json
	mkdir test-results
	.venv/bin/pytest tests/features --junitxml=test-results/features.xml
	cd handlers;../.venv/bin/pytest ../tests/unit --junitxml=../test-results/unit.xml


.bin/terraform: # Installs Terraform
	mkdir -p tests/.bin
	curl -L -o tests/.bin/terraform.zip https://releases.hashicorp.com/terraform/0.14.10/terraform_0.14.10_linux_amd64.zip
	unzip tests/.bin/terraform.zip
	mv terraform tests/.bin/
	chmod +x tests/.bin/terraform

terraform-apply: .bin/terraform
	cd tests;.bin/terraform init;.bin/terraform apply -auto-approve;cd ..

terraform-destroy: .bin/terraform
	cd tests;.bin/terraform destroy -auto-approve;cd ..

wait-circle:
	-curl https://meadow-testing.grassfed.tools/signup;while [ "$$?" != "0" ];do sleep 1; curl https://meadow-testing.grassfed.tools/signup;done;sleep 60