from setuptools import setup, find_packages

version = '0.0.1'

setup(name="helga-github",
      version=version,
      description=('github plugin for helga'),
      classifiers=['Development Status :: 4 - Beta',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   ],
      keywords='irc bot github',
      author='Douglas Fuller',
      author_email='douglas.fuller [at] gmail [dot] com',
      url='https://github.com/fullerdj/helga-github',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          'helga>=1.7.5',
          'treq>=15.1.0',
          'twisted',
      ],
      tests_require=[
          'pytest-twisted',
      ],
      entry_points = dict(
          helga_plugins = [
              'github = github:github',
          ],
      ),
)
