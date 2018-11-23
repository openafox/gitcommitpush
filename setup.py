import setuptools

setuptools.setup(
    name="gitcommitpush",
    version='0.1.0',
    url="https://github.com/openafox/githubcommit",
    author="Shaleen Anand Taneja - major updates by Austin Fox",
    description="Jupyter extension to enable user push notebooks to a git repo",
    packages=setuptools.find_packages(),
    install_requires=[
        'psutil',
        'notebook',
        'gitpython'
    ],
    package_data={'gitcommitpush': ['static/*']},
)
