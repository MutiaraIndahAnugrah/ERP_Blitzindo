from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in kulkul_erp/__init__.py
from kulkul_erp import __version__ as version

setup(
	name="kulkul_erp",
	version=version,
	description="Kulkul ERP Custom",
	author="Kulkul",
	author_email="Kulkul",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
