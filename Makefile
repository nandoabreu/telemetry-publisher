.PHONY: build

SHELL := $(shell type bash | cut -d\  -f3)
POETRY_PATH := $(shell type poetry | cut -d\  -f3)
PROJECT_DIR := $(shell realpath .)
HOST_IP := $(shell ip -o -4 address | grep -v 127.0.0 | head -1 | awk '{print $$4}' | cut -d/ -f1)

VIRTUAL_ENV ?= $(shell poetry env info -p)
PYTHON_VERSION := $(shell cat .python-version 2>/dev/null || python3 -V | sed "s,.* \(3\.[0-9]\+\)\..*,\1,")

BUILD_DIR ?= build

$(shell eval run=dev python setup/dotenv-from-toml.py > .env)
include .env


env-info:
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
	@poetry install --no-root -v
	@poetry run pre-commit install
	@sed -i "/^INSTALL_PYTHON=.*/a PATH=${POETRY_PATH}:\$$INSTALL_PYTHON/bin:\$$PATH" .git/hooks/pre-commit

test-unit:
	PYTHONPATH=${SRC_DIR} poetry run python -m pytest tests/unit --exitfirst --verbose  # --capture=no

test-unit-coverage:
	@PYTHONPATH=${SRC_DIR} poetry run python -m pytest tests/ --cov --cov-branch --cov-report term-missing

collect-and-publish:
	@bash setup/collect-and-publish.bash


build: build-recreate-dir build-compile toss-build-temp

build-recreate-dir: toss-builds
	@mkdir "${BUILD_DIR}"

build-compile: toss-src-cache
	@set -o allexport; source .env; set +o allexport; \
		poetry run python setup/compile.py build_ext -j 9 --build-lib "${BUILD_DIR}"
	@cp -f src/app/__main__.py "${BUILD_DIR}/app/"
	@python setup/dotenv-from-toml.py > "${BUILD_DIR}/.env"

distro-pack:
	@poetry export --without-hashes --only main | \
		pip install -q --target="${BUILD_DIR}/dependencies" -r /dev/stdin
	@mkdir -p "${DISTRO_DIR}" && rm -f "${DISTRO_DIR}/${PROJECT_NAME}" && \
		mv "${BUILD_DIR}" "${DISTRO_DIR}/${PROJECT_NAME}"
	@cd "${DISTRO_DIR}" && tar -cpf "${PROJECT_NAME}.tar" "${PROJECT_NAME}"


run-kafka-ui:
	@podman run --rm -d --network=host --hostname=kafka-ui --name=kafka-ui \
		-e DYNAMIC_CONFIG_ENABLED=true \
		-e KAFKA_CLUSTERS_0_NAME=kafka-cluster \
		-e KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS=${KAFKA_BROKERS} \
		docker.io/provectuslabs/kafka-ui
	@echo "Kafka UI should be accessed via http://${HOST_IP}:8080/"

test-repl:
	PYTHONPATH=${SRC_DIR} poetry run python


toss-build-temp:
	@find src -type f -name "*\.c" -exec rm {} +
	@rm -rf ${BUILD_DIR}/temp.linux*

toss-src-cache:
	@find . -type d -name .pytest_cache | xargs rm -rf
	@find . -type d -name __pycache__ | xargs rm -rf

toss-builds:
	@rm -rf ${BUILD_DIR}

toss-dist-packages:
	@rm -fr ${DIST_DIR}

toss-containers:
	@podman container stop kafka-ui

toss-all: toss-src-cache toss-build-temp toss-builds
