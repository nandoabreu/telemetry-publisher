SHELL := $(shell type bash | cut -d\  -f3)
POETRY_PATH := $(shell type poetry | cut -d\  -f3)
PROJECT_DIR := $(shell realpath .)
HOST_IP := $(shell ip -o -4 address | grep -v 127.0.0 | head -1 | awk '{print $$4}' | cut -d/ -f1)

VIRTUAL_ENV ?= $(shell poetry env info -p)
PYTHON_VERSION := $(shell cat .python-version 2>/dev/null || python3 -V | sed "s,.* \(3\.[0-9]\+\)\..*,\1,")

BUILD_DIR ?= build

$(shell eval run=dev python setup/dotenv-from-toml.py > .env)
include .env


self-test:
	@echo -e """\
	Application: ${APP_NAME} v${APP_VERSION}\n\
	Project: ${PROJECT_NAME} (${PROJECT_DESCRIPTION})\n\
	Source files: ${PROJECT_DIR}/${SRC_DIR}\n\
	Virtual env: $(shell poetry env info -p)\n\
	Current Python: ${PYTHON_VERSION}\n\
	""" | sed "s,: ,:|,;s,^\t,," | column -t -s\|

env-setup:
	@git init
	@[ -f .python-version ] && poetry env use $(shell cat .python-version) >/dev/null || true
	@poetry install -v
	@poetry run pre-commit install
	@sed -i "/^INSTALL_PYTHON=.*/a PATH=${POETRY_PATH}:\$$INSTALL_PYTHON/bin:\$$PATH" .git/hooks/pre-commit

test-unit:
	PYTHONPATH=${SRC_DIR} poetry run python -m pytest tests/unit --exitfirst --verbose  # --capture=no

test-unit-coverage:
	@PYTHONPATH=${SRC_DIR} poetry run python -m pytest tests/ --cov --cov-branch --cov-report term-missing

collect-and-publish:
	LOG_LEVEL="${LOG_LEVEL}" \
	PYTHONPATH="${VIRTUAL_ENV}/lib/python${PYTHON_VERSION}/site-packages:${SRC_DIR}" \
	python -m "${APP_DIR}"


build:
	@python setup/dotenv-from-toml.py > setup/.env
	@echo "${PROJECT_NAME} Build :: Call builder"
	@set -o allexport; source setup/.env; set +o allexport;
	@echo "${PROJECT_NAME} Build :: Compile App files"
	@poetry run python setup/compile.py build_ext -j 9 --build-lib build
	@cp setup/.env build/
	@find ${SRC_DIR} -type f -name *\.c -delete
	@rm -rf "build/temp.linux"*


run-kafka-ui:
	@podman run --rm -d --network=host --hostname=kafka-ui --name=kafka-ui \
		-e DYNAMIC_CONFIG_ENABLED=true \
		-e KAFKA_CLUSTERS_0_NAME=kafka-cluster \
		-e KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS=${KAFKA_BROKERS} \
		docker.io/provectuslabs/kafka-ui
	@echo "Kafka UI should be accessed via http://${HOST_IP}:8080/"

test-repl:
	PYTHONPATH=${SRC_DIR} poetry run python

tidy-up:
	@podman container stop kafka-ui
