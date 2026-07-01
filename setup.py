from setuptools import setup, find_packages

setup(
    name="CLASPLint",
    version="0.3.0",
    
    description="CLASP 3.1.1 / PEP 2606 Static Analysis Tool",
    
    author_email="thedayofthedo@gmail.com",
    
    keywords = ["CLASP", "pep2606", "Linter", "static-analysis", "naming-convention", "code-quality", "python"],
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "CLASPLint=CLASPLint.__main__:main",
        ],
    },
    include_package_data=True,
    zip_safe=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    platforms="any",
)
