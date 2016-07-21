#!/usr/bin/env python
# encoding: utf-8

import os

from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))


setup(
		name = "htdsa",
		version = "1.0.0",

		description = "Client and server implementations of the HTDSA 2015-18-B draft for Requests and WebCore.",
		long_description = "",
		url = "https://github.com/marrow/htdsa-python",
		author = "Alice Bevan-McGregor",
		author_email = "alice@gothcandy.com",
		license = "mit",
		keywords = [],

		packages = find_packages(exclude=['test', 'example', 'conf', 'benchmark', 'tool', 'doc']),
		include_package_data = True,
		package_data = {'': [
				'README.md',
				'LICENSE.txt'
			]},

		namespace_packages = [
			],

		setup_requires = [
				'pytest-runner',
			],

		tests_require = [
				'pytest-runner',
				'coverage',
				'pytest',
				'pytest-cov',
				'pytest-spec',
				'pytest-flakes',
			],

		install_requires = [
			],

		extras_require = dict(
				development = [
						'pytest-runner',
						'coverage',
						'pytest',
						'pytest-cov',
						'pytest-spec',
						'pytest-flakes',
					],
			),

		zip_safe = True,

		entry_points = {
				}
	)
