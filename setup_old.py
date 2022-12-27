from setuptools import setup

setup(name='vedirect',
      version='0.3',
      description='Victron VE.Direct decoder for Python, forked from karioja',
      url='https://github.com/jmfife/vedirect',
      author='Mike Fife',
      author_email='jmfife@gmail.com',
      license='MIT',
      packages=['vedirect'],
      install_requires=[
          'pyserial',
      ],
      zip_safe=False,
      entry_points={
          'console_scripts': ['vedirect=vedirect.vedirect:main',
                              'vedirect_device_emulator=vedirect.vedirect_device_emulator:main'],
      },
      extras_require={
          "examples": ["paho-mqtt"],     # to run example MQTT publisher
      }
      )
