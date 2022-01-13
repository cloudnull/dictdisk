#   Copyright Peznauts <kevin@peznauts.com>. All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
import setuptools

from iodict import meta


with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()


REQUIREMENTS = {"macos": ["xattr"]}


setuptools.setup(
    name="iodict",
    author=meta.__author__,
    author_email=meta.__email__,
    description="A disk backed dictionary implementation.",
    version=meta.__version__,
    packages=["iodict"],
    include_package_data=True,
    zip_safe=False,
    test_suite="tests",
    install_requires=[],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/directord/iodict",
    project_urls={
        "Bug Tracker": "https://github.com/directord/iodict/issues",
    },
    python_requires=">=3.6",
    extras_require=REQUIREMENTS,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Topic :: Utilities",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={},
    data_files=[],
)
