# PVHelpers

## Installing package

Recommended to install your dev environment within a fresh virtual environment.
```
${envpip} install --no-cache-dir --no-index  --force-reinstall -r requirements.txt -r requirements_${osx/linux/win}.txt
${envpip} install --no-index .
```

## Running Tests
 ```
 ${envpip} install tox
 ${envpython} -m tox -r -- {pytest-args}
 ```

 Note: This package depends on libsodium and the dependency won't get resolved automatically and you should install libsodium manually on your system. For instance, on linux, this can be done by `apt-get update && apt-get install -y libsodium-dev`

## Running Linters
```tox -e flake8 -- {flake8-args}```



## How to create a new version of pvHelpers for daemon

1. Make the code changes to pvHelpers.
2. Bump the semantic version of pvHelpers in both pvHelpers' setup.py and daemon's setup.py appropriately, according to the scope of the change from step 1.
3. Compile the new pvHelpers using ```python setup.py sdist --format=gztar```
4. Copy <path_to_pvHelpers_repo>/dist/pvHelpers-<major.minor.patch>.tar.gz to the python's folder of the vendor repo.
5. Make use of the vendor's branch in daemon.
6. Repeat step 1-5 if there are more changes.

Note: for a quick dev work, we can also use ```pip install -e <path_to_pvHelpers_repo>``` to use a local version of pvHelpers.
