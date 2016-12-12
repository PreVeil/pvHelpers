from distutils.core import setup
setup(name='pvHelpers',
      version='1.15',
      packages=['pvHelpers'],
      install_requires=[
        "PyYAML==3.11",
        "requests==2.7.0",
        "simplejson==3.8.2",
      ],
)
