from distutils.core import setup
setup(name='pvHelpers',
      version='1.0',
      packages=['pvHelpers'],
      install_requires=[
        "PyYAML==3.11"
      ],
      dependency_links=[
        "https://github.com/PreVeil/vendor/raw/master/python/PyYAML-3.11.tar.gz"
      ]
)
