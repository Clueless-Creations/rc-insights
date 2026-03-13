from setuptools import setup, find_packages

setup(
    name="rc-insights",
    version="0.1.0",
    description="Agent-ready CLI and Python library for RevenueCat Charts API analysis",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Katire (AI Agent)",
    author_email="katire@clueless.clothing",
    url="https://github.com/katire-agent/rc-insights",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.25.0",
        "rich>=13.0.0",
        "click>=8.0.0",
        "jinja2>=3.0.0",
    ],
    extras_require={
        "dev": ["pytest", "pytest-asyncio", "respx"],
    },
    entry_points={
        "console_scripts": [
            "rc-insights=rc_insights.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries",
    ],
)
