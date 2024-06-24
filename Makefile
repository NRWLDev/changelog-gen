release:
	changelog-gen

coverage:
	pytest --cov=changelog_gen --cov-config pyproject.toml
