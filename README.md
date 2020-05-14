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

Everytime, we want to make changes to pvHelpers and use it in core, we need to do the following:
1.
