.PHONY: build

SHELL := $(shell type bash | cut -d\  -f3)
POETRY_PATH := $(shell type poetry 2>/dev/null | cut -d\  -f3)
PROJECT_DIR := $(shell realpath .)
HOST_IP := $(shell ip -o -4 address 2>/dev/null | grep -v 127.0.0 | head -1 | awk '{print $$4}' | cut -d/ -f1)

VIRTUAL_ENV ?= $(shell poetry env info -p 2>/dev/null || find . -type d -name '*venv' -exec realpath {} \;)
PYTHON_VERSION := $(shell cat .python-version 2>/dev/null || python3 -V | sed "s,.* \(3\.[0-9]\+\)\..*,\1,")

BUILD_DIR ?= build

ifneq ($(shell echo "${MAKECMDGOALS}" | grep -q -E '^(env-setup|install-source)$$' && echo noenv || echo isdev), noenv)
$(shell eval run=dev python setup/dotenv-from-toml.py > .env)
include .env
endif

env-info:
	@echo -e """\
	Application: ${APP_NAME} v${APP_VERSION}\n\
	Project: ${PROJECT_NAME} (${PROJECT_DESCRIPTION})\n\
	Source files: ${PROJECT_DIR}/${SRC_DIR}\n\
	Virtual env: ${VIRTUAL_ENV}\n\
	Current Python: ${PYTHON_VERSION}\n\
	""" | sed "s,: ,:|,;s,^\t,," | column -t -s\|

env-setup:
# todo: build and pack for different versions - v3.9 compilation does not run on 3.11, etc
	@[ -f .python-version ] && poetry env use $(shell cat .python-version) >/dev/null || true
	@poetry install --no-root -v
	@poetry run pre-commit install
	@sed -i "/^INSTALL_PYTHON=.*/a PATH=${POETRY_PATH}:\$$INSTALL_PYTHON/bin:\$$PATH" .git/hooks/pre-commit

test-unit:
	PYTHONPATH=${SRC_DIR} poetry run python -m pytest tests/unit --exitfirst --verbose  # --capture=no

test-unit-coverage:
	@PYTHONPATH=${SRC_DIR} poetry run python -m pytest tests/ --cov --cov-branch --cov-report term-missing

run:
	@PYTHONPATH=${SRC_DIR} poetry run python -m app


build: build-recreate-dir build-compile toss-build-temp

build-recreate-dir: toss-builds
	@mkdir "${BUILD_DIR}"

build-compile: toss-src-cache
# todo: build and pack for different versions - v3.9 compilation does not run on 3.11, etc
	@set -o allexport; source .env; set +o allexport; \
		poetry run python setup/compile.py build_ext -j 9 --build-lib "${BUILD_DIR}"

distro-pack:
# todo: build and pack for different versions - v3.9 compilation does not run on 3.11, etc
	@rm -rf "${DISTRO_DIR}/${PROJECT_NAME}" && mkdir -p "${DISTRO_DIR}" && \
		cp -pr "${BUILD_DIR}" "${DISTRO_DIR}/${PROJECT_NAME}"
	@poetry export --without-hashes --only main | \
		pip install -q --upgrade -r /dev/stdin --target="${DISTRO_DIR}/${PROJECT_NAME}/dependencies"
	@cp -f src/app/__main__.py "${DISTRO_DIR}/${PROJECT_NAME}/app/"
	@cp -f setup/run.bash "${DISTRO_DIR}/${PROJECT_NAME}/run"
	@python setup/dotenv-from-toml.py > "${DISTRO_DIR}/${PROJECT_NAME}/.env"
	@cd "${DISTRO_DIR}" && tar -cpf "${PROJECT_NAME}.tar" "${PROJECT_NAME}"

install-source:
	@cat pyproject.toml | \
		awk '/^\[tool.poetry.dependencies\]/ {flag=1; next} /^\[/{flag=0} flag' | \
		grep -v '^python ' | sed 's, = ".\([0-9.].*[0-9]\)"$$,==\1,' | \
		sed 's| =.*version = ".\?\([0-9.].*[0-9]\)", python = "\(.\)\([0-9.]\+\)" }$$|==\1 ; python_version \2 "\3"|' \
		> requirements.parsed.txt
	@python3 -m venv .venv && .venv/bin/python -m pip install -q -r requirements.parsed.txt && \
		rm -f requirements.parsed.txt
	@.venv/bin/python setup/dotenv-from-toml.py > .env


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
	@rm -fr ${DISTRO_DIR}

toss-containers:
	@podman container stop kafka-ui

toss-all: toss-src-cache toss-build-temp toss-builds
