.PHONY: infra
infra:
	cd infra/ && ./infra.sh

.PHONY: clean
clean:
	- rm -rf env
	- find . -name "*.pyc" | xargs rm

env: requirements.txt requirements-dev.txt
	 virtualenv -p python3 env
	. env/bin/activate && pip install -r requirements.txt -r requirements-dev.txt

.PHONY: lint
lint: env
	flake8 src/

.PHONY: build
build: lint
ifndef TAG
	$(error TAG environment variable hasn't been defined!)
endif
	docker build \
		-t event-predictions:${TAG} \
		-t event-predictions:latest \
		.

.PHONY: push_build
push_build: build

.PHONY: run_locally
run_locally:
	docker run \
		-p 8000:8000 \
		-e PORT=8000 \
		event-predictions:latest \

.PHONY: deploy_aws
deploy_aws:
	echo 'Not implemented yet!'

.PHONY: deploy_agcp
deploy_aws:
	echo 'Not implemented yet!'

.PHONY: deploy_azire
deploy_aws:
	echo 'Not implemented yet!'
