# Development

This document describes how to set up a development environment for the `readlif` package, how to run tests, and how to manage dependencies.

## Environment setup

We use poetry for dependency management and build tooling. You can either install poetry globally or within a virtual environment in order to isolate poetry itself. We recommend the latter. First, create a new conda environment from the `dev.yml` environment file:

```bash
conda env create -n readlif-dev -f envs/dev.yml
conda activate readlif-dev
```

Next, install dependencies, including the development, documentation, and build dependencies:

```bash
poetry install --no-root --with dev
```

If you have installed poetry globally, activate the poetry virtual environment:

```bash
poetry shell
```

Poetry detects and respects existing virtual environments, so if you are using poetry within a conda environment, this step is not needed.

Finally, install the package itself in editable mode:

```bash
pip install -e .
```

## Formatting and linting

If you have installed poetry globally, make sure to run `poetry shell` before running the commands below.

To format the code, use the following command:

```bash
make format
```

To run the lint checks and type checking, use the following command:

```bash
make lint
```

## Pre-commit hooks

We use pre-commit to run formatting and lint checks before each commit. To install the pre-commit hooks, use the following command:

```bash
pre-commit install
```

To run the pre-commit checks manually, use the following command:

```bash
make pre-commit
```

## Testing

We use `pytest` for testing. The tests are found in the `/tests` directory. To run the tests, use the following command:

```bash
make test
```

## Managing dependencies

We use poetry to manage dependencies. To add a new dependency, use the following command:

```bash
poetry add some-package
```

To add a new development dependency, use the following command:

```bash
poetry add --group dev some-dev-package
```

To update a dependency, use the following command:

```bash
poetry update some-package
```

Whenever you add or update a dependency, poetry will automatically update both `pyproject.toml` and the `poetry.lock` file. Make sure to commit the changes to these files to the repo.

## Publishing the package on PyPI

First, create a `.env` file by coping `.env.copy` and then add your API tokens for the test and prod PyPI servers.

Next, create a new git tag with a name that matches the new version number, prepended with a "v". We use semantic versioning of the form `MAJOR.MINOR.PATCH`. See [semver.org](https://semver.org/) for more information.

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

__Before creating the tag, make sure that your local git repository is on `main`, is up-to-date, and does not contain uncommitted changes!__

If you make a mistake and need to delete a tag, use the following command:

```bash
git tag -d <tagname>
```

If you already pushed the deleted tag to GitHub, you will also need to delete the tag from the remote repository:

```bash
git push origin :refs/tags/<tagname>
```

Once you've created the new tag, check that poetry correctly infers the new version number:

```bash
poetry version -s
```

__The output of this command should exactly match the new version number in the tag you just created (e.g. `0.1.0`).__

Next, check that you can publish the package to the PyPI test server:

```bash
make build-and-test-publish
```

The `build-and-test-publish` command calls `poetry build` to build the package and then `poetry publish` to upload the build artifacts to the test server.

Check that you can install the new version of the package from the test server:

```bash
pip install --index-url https://test.pypi.org/simple/ readlif==0.1.0
```

If everything looks good, build and publish the package to the prod PyPI server:

```bash
make build-and-publish
```

Finally, check that you can install the new version of the package from the prod PyPI server:

```bash
pip install readlif==0.1.0
```
