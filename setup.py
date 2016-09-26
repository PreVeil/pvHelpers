from distutils.core import setup
setup(name='pvHelpers',
      version='1.5',
      packages=['pvHelpers'],
      install_requires=[
        "PyYAML==3.11",
        "requests==2.7.0",
        "flanker==0.4.40",
        "simplejson==3.8.2",
        "Twisted==160.1.3",
      ],
)
