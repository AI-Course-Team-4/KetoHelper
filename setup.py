"""
📦 Restaurant Crawler MVP 패키지 설정
"""

from setuptools import setup, find_packages
from pathlib import Path

# README 파일 읽기
this_directory = Path(__file__).parent
long_description = (this_directory / "ARCHITECTURE_OPTIMIZED.md").read_text(encoding='utf-8')

setup(
    name="restaurant-crawler-mvp",
    version="1.0.0",
    author="Restaurant Crawler Team",
    description="MVP 식당 크롤링 시스템",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    packages=find_packages(),
    include_package_data=True,
    
    python_requires=">=3.8",
    
    install_requires=[
        "playwright>=1.40.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "psycopg2-binary>=2.9.9",
        "asyncpg>=0.29.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "pandas>=2.1.4",
        "click>=8.1.7",
        "pydantic>=2.5.2",
        "loguru>=0.7.2",
    ],
    
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-mock>=3.12.0",
            "black>=23.12.1",
            "flake8>=6.1.0",
            "mypy>=1.8.0",
        ]
    },
    
    entry_points={
        "console_scripts": [
            "crawler=crawler:cli",
        ],
    },
    
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    
    project_urls={
        "Documentation": "https://github.com/your-org/restaurant-crawler",
        "Source": "https://github.com/your-org/restaurant-crawler",
        "Tracker": "https://github.com/your-org/restaurant-crawler/issues",
    },
)