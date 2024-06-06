WEBAPP = webapp

setup_system_pkgs:
	@echo "Setup system packages..."
	@sudo apt-get -y update
	@sudo apt-get -y install gnupg \
		openssl \
		build-essential \
		zlib1g-dev \
		libncurses5-dev \
		libgdbm-dev \
		libnss3-dev \
		libssl-dev \
		libsqlite3-dev \
		libreadline-dev \
		libffi-dev \
		curl \
		libbz2-dev

setup_poetry:
	@echo "Setup poetry..."
	@curl -sSL https://install.python-poetry.org | python3 - --version 1.8.2

setup: setup_system_pkgs setup_poetry
	@echo "Installing ruby gems and python packages..."
	@gem install bundler:1.16.1
	@gem install set -v 1.0.3
	@gem install sorted_set
	@bundle _1.16.1_ install --gemfile=./requirements/Gemfile
	@poetry env use 3.7.5
	@poetry install

test: setup
	@echo "Running tests..."
	python -m unittest tests

clean:
	poetry env remove 3.7.5 || true

.PHONY: $(WEBAPP) all setup clean info coverage
