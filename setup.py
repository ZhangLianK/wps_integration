from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in wps_integration/__init__.py
from wps_integration import __version__ as version

setup(
	name="wps_integration",
	version=version,
	description="WPS Integration",
	author="Alvin",
	author_email="zhangliankun0907@foxmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
