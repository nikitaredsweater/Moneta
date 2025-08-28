#!/bin/bash

# Moneta Microservice Generator
# Creates a complete FastAPI-based microservice with all necessary files

set -e

# Check if service name is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide a service name"
    echo "Usage: $0 <service_name>"
    echo "Example: $0 user_service"
    exit 1
fi

SERVICE_NAME=$1

echo "🚀 Creating FastAPI microservice: $SERVICE_NAME"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Create service directory at the project root level (same level as monolith and document_service)
cd "$PROJECT_ROOT"
mkdir -p "$SERVICE_NAME"
cd "$SERVICE_NAME"

echo "📁 Creating directory structure..."

# Create all necessary directories
mkdir -p app/api/v1/routes
mkdir -p app/schemas
mkdir -p app/services
mkdir -p app/utils
mkdir -p app/tests
mkdir -p app/enums
mkdir -p app/handlers
mkdir -p scripts

# Create __init__.py files
touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/routes/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py

echo "📝 Creating configuration files..."

# Create requirements.in
cat > requirements.in << 'EOF'
fastapi
uvicorn

# --- Testing ---
pytest
pytest-asyncio

# --- Formatters & Linters ---
isort
black  # Using black instead of yapf for Python 3.13 compatibility
# unify - removed due to Python 3.13 incompatibility (depends on lib2to3)
flake8
flake8-bugbear
flake8-comprehensions
flake8-isort
flake8-quotes
dlint
darglint

# --- Static Analysis & Security ---
bandit
pylint
mypy

# --- Pre-commit and its dependencies ---
pre-commit

# --- Additional tools for local pre-commit hooks ---
# Note: Most of the pre-commit hook tools are provided by the pre-commit-hooks package
# and don't need to be installed separately as they're built into the pre-commit ecosystem
# --- Environment ---
python-dotenv
EOF

# Create empty requirements.txt
touch requirements.txt

# Create environment.config.example
cat > environment.config.example << 'EOF'
# Application Configuration
APP_NAME=New Microservice
APP_VERSION=1.0.0
DEBUG=false

# Server Configuration
HOST=0.0.0.0
PORT=8000


# Logging
LOG_LEVEL=INFO

# Database (if needed)
DATABASE_URL=postgresql://user:password@db:5432/dbname

# Message Queue (if needed)
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
EOF

# Create pytest.ini
cat > pytest.ini << 'EOF'
[pytest]
pythonpath = app
EOF

# Create setup.cfg
cat > setup.cfg << 'EOF'
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist,venv

[isort]
profile = black
multi_line_output = 3
line_length = 88
known_first_party = app

[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[tool:black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool:bandit]
exclude_dirs = ["venv", "tests"]
skips = ["B101", "B601"]
EOF


echo "🔧 Creating application files..."

# Create app/config.py and app/dependencies.py
touch app/config.py
touch app/dependencies.py

# Create app/main.py
cat > app/main.py << 'EOF'
"""
Main FastAPI application module
"""

import logging

from app.api import app_router
from fastapi import FastAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)
logger.info('Starting application')

app = FastAPI()
app.include_router(app_router)
EOF

# Create app/api/__init__.py
cat > app/api/__init__.py << 'EOF'
"""
Routers module
"""

from app.api.v1 import v1_router
from fastapi import APIRouter

app_router = APIRouter()
app_router.include_router(v1_router, prefix='/v1')
EOF

# Create app/api/v1/__init__.py
cat > app/api/v1/__init__.py << 'EOF'
"""
v1 API routes
"""

from app.api.v1.routes.health import health_check_router
from fastapi import APIRouter

v1_router = APIRouter()

v1_router.include_router(health_check_router, prefix='/health')
EOF

# Create app/api/v1/routes/__init__.py
cat > app/api/v1/routes/__init__.py << 'EOF'
from app.api.v1.routes.health import health_check_router

__all__ = ["health_check_router"]
EOF

# Create app/api/v1/routes/health.py
cat > app/api/v1/routes/health.py << 'EOF'
from fastapi import APIRouter, HTTPException
from typing import Any, Dict

import time
import app.schemas as schemas

health_check_router = APIRouter()


@health_check_router.get("/health", response_model=schemas.HealthResponse)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "$SERVICE_NAME",
        "version": "1.0.0"
    }
EOF

# Copy base.py from document_service
cat > app/schemas/base.py << 'EOF'
"""
Base data transfer object
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# Use Pydantic's UUID4 with a custom factory
MonetaID = Annotated[UUID, Field(default_factory=uuid4)]


def _to_camel(string: str) -> str:
    """
    Convert snake_case to camelCase

    Args:
        string (str): The string to convert

    Returns:
        str: The converted string
    """
    str_split = string.split("_")
    return str_split[0] + "".join(word.capitalize() for word in str_split[1:])


class CamelModel(BaseModel):
    """
    Base model that converts snake_case to camelCase
    """

    model_config = {
        'alias_generator': _to_camel,
        'populate_by_name': True,
    }


class BaseDTO(CamelModel):
    """
    Base Moneta Financial DTO

    This is a base class for all DTOs.
    It contains the id and created_at fields.
    It also converts snake_case to camelCase.

    Make sure that the DTO fields match the ORM model fields.

    Except for:
      deleted_at field.
    """

    id: MonetaID
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = {
        'from_attributes': True,  # Updated from orm_mode
        'alias_generator': _to_camel,
        'populate_by_name': True,
    }
EOF

# Create app/schemas/__init__.py
cat > app/schemas/__init__.py << 'EOF'
from app.schemas.base import BaseDTO, CamelModel
from app.schemas.health import HealthResponse

__all__ = ["BaseDTO", "CamelModel", "HealthResponse"]
EOF

# Create app/schemas/health.py
cat > app/schemas/health.py << 'EOF'
"""
Health-related schemas
"""

from app.schemas.base import CamelModel


class HealthResponse(CamelModel):
    """Health check response model"""

    status: str
    timestamp: float
    service: str
    version: str
EOF

echo "🐳 Creating Docker files..."

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

echo "📋 Creating documentation..."

# Create blank README.MD
cat > README.MD << 'EOF'
# New Microservice

This is a new FastAPI-based microservice for the Moneta backend ecosystem.

## Table of Contents

- [API Endpoints](#api-endpoints)
- [Setup Instructions](#setup-instructions)
- [Development](#development)

## API Endpoints

### Base URL
All endpoints are prefixed with `/v1`

### Health Check

#### `GET /v1/health/`
Simple health check endpoint to verify service status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123,
  "service": "new_microservice",
  "version": "1.0.0"
}
```

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run development server:
```bash
./scripts/run_dev.sh
```

## Development

- API documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc
EOF

# Create blank ONBOARDING.MD
cat > ONBOARDING.MD << 'EOF'
# Onboarding

This file will help you to quickly understand some core ideas that are a part of this service.

## Table of Contents

- [Project Structure Overview](#project-structure-overview)
- [Development Workflow](#development-workflow)

## Project Structure Overview

Understanding the folder hierarchy is crucial for navigating the codebase efficiently.

### Root Level Structure

```
new_microservice/
├── app/                     # Main application code
├── proto/                   # Protocol buffer definitions
├── scripts/                 # Utility scripts
├── Dockerfile              # Docker container definition
├── environment.config.example # Environment variables template
├── requirements.txt        # Python dependencies
└── README.MD               # Service documentation
```

### App Directory Structure

```
app/
├── main.py                # Application entry point
├── config.py              # Configuration settings
├── api/                   # REST API routes
│   ├── v1/                # Version 1 API routes
│   │   └── routes/        # Individual endpoint handlers
│   │       └── health.py  # Health check endpoint
├── schemas/               # Pydantic data models
│   ├── base.py            # Base schema classes
│   └── health.py          # Health-specific schemas
└── services/              # Business logic layer
```

## Development Workflow

1. **Make changes** to the code
2. **Test locally** using `./scripts/run_dev.sh`
3. **Follow coding standards** (black, isort, flake8, mypy)
4. **Add tests** for new functionality
5. **Update documentation** as needed

## Key Takeaways for Developers

1. **Follow the existing patterns** established in the codebase
2. **Use the provided schemas** for request/response validation
3. **Keep business logic** in the services layer
4. **Document your changes** in the README.MD
EOF

echo "🔧 Creating pre-commit configuration..."

# Create the pre-commit config file
cat > .pre-commit-config.yaml << 'EOF'
exclude: ^alembic/
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-shebang-scripts-are-executable
      - id: name-tests-test
        args: [--pytest-test-first]
      - id: detect-private-key
        exclude: cred.json
      - id: check-toml
      - id: check-merge-conflict
      - id: pretty-format-json
        args: [--autofix, --indent=2]
        exclude: cred.json
      - id: check-yaml
        exclude: chart/|charts/|werf-*
      - id: debug-statements
      - id: requirements-txt-fixer
      - id: trailing-whitespace
        args: [--markdown-linebreak-ext=md]
      - id: end-of-file-fixer
        exclude: cred.json

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  # unify removed due to Python 3.13 incompatibility (depends on lib2to3)

  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
        args: [--line-length=80, --skip-string-normalization]

  - repo: local
    hooks:
      - id: pylint
        name: pylint
        entry: pylint
        language: system
        types: [python]
        require_serial: true

  - repo: https://github.com/pycqa/flake8
    rev: 7.3.0
    hooks:
      - id: flake8
        additional_dependencies:
          - darglint
          - dlint
          - flake8-bugbear
          - flake8-comprehensions
          - flake8-isort
          - flake8-quotes

  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.6
    hooks:
      - id: bandit
        args: ["-q", "--ini", "setup.cfg"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.16.1
    hooks:
      - id: mypy
        args:
          [
            --ignore-missing-imports,
            --scripts-are-modules,
            --follow-imports=skip,
            --disallow-untyped-defs,
            --disallow-incomplete-defs,
            --warn-redundant-casts,
            --implicit-optional,
            --exclude,
            site-packages,
          ]
EOF

# Creating a .gitignore file
cat > .gitignore << 'EOF'
# Created by https://www.toptal.com/developers/gitignore/api/macos,visualstudio,visualstudiocode,python,venv,dotenv,windows,linux
# Edit at https://www.toptal.com/developers/gitignore?templates=macos,visualstudio,visualstudiocode,python,venv,dotenv,windows,linux

### dotenv ###
.env

### Linux ###
*~

# temporary files which can be created if a process still has a handle open of a deleted file
.fuse_hidden*

# KDE directory preferences
.directory

# Linux trash folder which might appear on any partition or disk
.Trash-*

# .nfs files are created when an open file is removed but is still being accessed
.nfs*

### macOS ###
# General
.DS_Store
.AppleDouble
.LSOverride

# Icon must end with two \r
Icon


# Thumbnails
._*

# Files that might appear in the root of a volume
.DocumentRevisions-V100
.fseventsd
.Spotlight-V100
.TemporaryItems
.Trashes
.VolumeIcon.icns
.com.apple.timemachine.donotpresent

# Directories potentially created on remote AFP share
.AppleDB
.AppleDesktop
Network Trash Folder
Temporary Items
.apdisk

### macOS Patch ###
# iCloud generated files
*.icloud

### Python ###
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
#   For a library or package, you might want to ignore these files since the code is
#   intended to run in multiple environments; otherwise, check them in:
# .python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or not
#   install all needed dependencies.
#Pipfile.lock

# poetry
#   Similar to Pipfile.lock, it is generally recommended to include poetry.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
#   https://python-poetry.org/docs/basic-usage/#commit-your-poetrylock-file-to-version-control
#poetry.lock

# pdm
#   Similar to Pipfile.lock, it is generally recommended to include pdm.lock in version control.
#pdm.lock
#   pdm stores project-wide configurations in .pdm.toml, but it is recommended to not include it
#   in version control.
#   https://pdm.fming.dev/#use-with-ide
.pdm.toml

# PEP 582; used by e.g. github.com/David-OConnor/pyflow and github.com/pdm-project/pdm
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# PyCharm
#  JetBrains specific template is maintained in a separate JetBrains.gitignore that can
#  be found at https://github.com/github/gitignore/blob/main/Global/JetBrains.gitignore
#  and can be added to the global gitignore or merged into this file.  For a more nuclear
#  option (not recommended) you can uncomment the following to ignore the entire idea folder.
#.idea/

### Python Patch ###
# Poetry local configuration file - https://python-poetry.org/docs/configuration/#local-configuration
poetry.toml

# ruff
.ruff_cache/

# LSP config files
pyrightconfig.json

### venv ###
# Virtualenv
# http://iamzed.com/2009/05/07/a-primer-on-virtualenv/
[Bb]in
[Ii]nclude
[Ll]ib
[Ll]ib64
[Ll]ocal
[Ss]cripts
pyvenv.cfg
pip-selfcheck.json

### VisualStudioCode ###
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json
!.vscode/*.code-snippets

# Local History for Visual Studio Code
.history/

# Built Visual Studio Code Extensions
*.vsix

### VisualStudioCode Patch ###
# Ignore all local history of files
.history
.ionide

### Windows ###
# Windows thumbnail cache files
Thumbs.db
Thumbs.db:encryptable
ehthumbs.db
ehthumbs_vista.db

# Dump file
*.stackdump

# Folder config file
[Dd]esktop.ini

# Recycle Bin used on file shares
$RECYCLE.BIN/

# Windows Installer files
*.cab
*.msi
*.msix
*.msm
*.msp

# Windows shortcuts
*.lnk

### VisualStudio ###
## Ignore Visual Studio temporary files, build results, and
## files generated by popular Visual Studio add-ons.
##
## Get latest from https://github.com/github/gitignore/blob/main/VisualStudio.gitignore

# User-specific files
*.rsuser
*.suo
*.user
*.userosscache
*.sln.docstates

# User-specific files (MonoDevelop/Xamarin Studio)
*.userprefs

# Mono auto generated files
mono_crash.*

# Build results
[Dd]ebug/
[Dd]ebugPublic/
[Rr]elease/
[Rr]eleases/
x64/
x86/
[Ww][Ii][Nn]32/
[Aa][Rr][Mm]/
[Aa][Rr][Mm]64/
bld/
[Bb]in/
[Oo]bj/
[Ll]og/
[Ll]ogs/

# Visual Studio 2015/2017 cache/options directory
.vs/
# Uncomment if you have tasks that create the project's static files in wwwroot
#wwwroot/

# Visual Studio 2017 auto generated files
Generated\ Files/

# MSTest test Results
[Tt]est[Rr]esult*/
[Bb]uild[Ll]og.*

# NUnit
*.VisualState.xml
TestResult.xml
nunit-*.xml

# Build Results of an ATL Project
[Dd]ebugPS/
[Rr]eleasePS/
dlldata.c

# Benchmark Results
BenchmarkDotNet.Artifacts/

# .NET Core
project.lock.json
project.fragment.lock.json
artifacts/

# ASP.NET Scaffolding
ScaffoldingReadMe.txt

# StyleCop
StyleCopReport.xml

# Files built by Visual Studio
*_i.c
*_p.c
*_h.h
*.ilk
*.meta
*.obj
*.iobj
*.pch
*.pdb
*.ipdb
*.pgc
*.pgd
*.rsp
*.sbr
*.tlb
*.tli
*.tlh
*.tmp
*.tmp_proj
*_wpftmp.csproj
*.tlog
*.vspscc
*.vssscc
.builds
*.pidb
*.svclog
*.scc

# Chutzpah Test files
_Chutzpah*

# Visual C++ cache files
ipch/
*.aps
*.ncb
*.opendb
*.opensdf
*.sdf
*.cachefile
*.VC.db
*.VC.VC.opendb

# Visual Studio profiler
*.psess
*.vsp
*.vspx
*.sap

# Visual Studio Trace Files
*.e2e

# TFS 2012 Local Workspace
$tf/

# Guidance Automation Toolkit
*.gpState

# ReSharper is a .NET coding add-in
_ReSharper*/
*.[Rr]e[Ss]harper
*.DotSettings.user

# TeamCity is a build add-in
_TeamCity*

# DotCover is a Code Coverage Tool
*.dotCover

# AxoCover is a Code Coverage Tool
.axoCover/*
!.axoCover/settings.json

# Coverlet is a free, cross platform Code Coverage Tool
coverage*.json
coverage*.xml
coverage*.info

# Visual Studio code coverage results
*.coverage
*.coveragexml

# NCrunch
_NCrunch_*
.*crunch*.local.xml
nCrunchTemp_*

# MightyMoose
*.mm.*
AutoTest.Net/

# Web workbench (sass)
.sass-cache/

# Installshield output folder
[Ee]xpress/

# DocProject is a documentation generator add-in
DocProject/buildhelp/
DocProject/Help/*.HxT
DocProject/Help/*.HxC
DocProject/Help/*.hhc
DocProject/Help/*.hhk
DocProject/Help/*.hhp
DocProject/Help/Html2
DocProject/Help/html

# Click-Once directory
publish/

# Publish Web Output
*.[Pp]ublish.xml
*.azurePubxml
# Note: Comment the next line if you want to checkin your web deploy settings,
# but database connection strings (with potential passwords) will be unencrypted
*.pubxml
*.publishproj

# Microsoft Azure Web App publish settings. Comment the next line if you want to
# checkin your Azure Web App publish settings, but sensitive information contained
# in these scripts will be unencrypted
PublishScripts/

# NuGet Packages
*.nupkg
# NuGet Symbol Packages
*.snupkg
# The packages folder can be ignored because of Package Restore
**/[Pp]ackages/*
# except build/, which is used as an MSBuild target.
!**/[Pp]ackages/build/
# Uncomment if necessary however generally it will be regenerated when needed
#!**/[Pp]ackages/repositories.config
# NuGet v3's project.json files produces more ignorable files
*.nuget.props
*.nuget.targets

# Microsoft Azure Build Output
csx/
*.build.csdef

# Microsoft Azure Emulator
ecf/
rcf/

# Windows Store app package directories and files
AppPackages/
BundleArtifacts/
Package.StoreAssociation.xml
_pkginfo.txt
*.appx
*.appxbundle
*.appxupload

# Visual Studio cache files
# files ending in .cache can be ignored
*.[Cc]ache
# but keep track of directories ending in .cache
!?*.[Cc]ache/

# Others
ClientBin/
~$*
*.dbmdl
*.dbproj.schemaview
*.jfm
*.pfx
*.publishsettings
orleans.codegen.cs

# Including strong name files can present a security risk
# (https://github.com/github/gitignore/pull/2483#issue-259490424)
#*.snk

# Since there are multiple workflows, uncomment next line to ignore bower_components
# (https://github.com/github/gitignore/pull/1529#issuecomment-104372622)
#bower_components/

# RIA/Silverlight projects
Generated_Code/

# Backup & report files from converting an old project file
# to a newer Visual Studio version. Backup files are not needed,
# because we have git ;-)
_UpgradeReport_Files/
Backup*/
UpgradeLog*.XML
UpgradeLog*.htm
ServiceFabricBackup/
*.rptproj.bak

# SQL Server files
*.mdf
*.ldf
*.ndf

# Business Intelligence projects
*.rdl.data
*.bim.layout
*.bim_*.settings
*.rptproj.rsuser
*- [Bb]ackup.rdl
*- [Bb]ackup ([0-9]).rdl
*- [Bb]ackup ([0-9][0-9]).rdl

# Microsoft Fakes
FakesAssemblies/

# GhostDoc plugin setting file
*.GhostDoc.xml

# Node.js Tools for Visual Studio
.ntvs_analysis.dat
node_modules/

# Visual Studio 6 build log
*.plg

# Visual Studio 6 workspace options file
*.opt

# Visual Studio 6 auto-generated workspace file (contains which files were open etc.)
*.vbw

# Visual Studio 6 auto-generated project file (contains which files were open etc.)
*.vbp

# Visual Studio 6 workspace and project file (working project files containing files to include in project)
*.dsw
*.dsp

# Visual Studio 6 technical files

# Visual Studio LightSwitch build output
**/*.HTMLClient/GeneratedArtifacts
**/*.DesktopClient/GeneratedArtifacts
**/*.DesktopClient/ModelManifest.xml
**/*.Server/GeneratedArtifacts
**/*.Server/ModelManifest.xml
_Pvt_Extensions

# Paket dependency manager
.paket/paket.exe
paket-files/

# FAKE - F# Make
.fake/

# CodeRush personal settings
.cr/personal

# Python Tools for Visual Studio (PTVS)
*.pyc

# Cake - Uncomment if you are using it
# tools/**
# !tools/packages.config

# Tabs Studio
*.tss

# Telerik's JustMock configuration file
*.jmconfig

# BizTalk build output
*.btp.cs
*.btm.cs
*.odx.cs
*.xsd.cs

# OpenCover UI analysis results
OpenCover/

# Azure Stream Analytics local run output
ASALocalRun/

# MSBuild Binary and Structured Log
*.binlog

# NVidia Nsight GPU debugger configuration file
*.nvuser

# MFractors (Xamarin productivity tool) working folder
.mfractor/

# Local History for Visual Studio
.localhistory/

# Visual Studio History (VSHistory) files
.vshistory/

# BeatPulse healthcheck temp database
healthchecksdb

# Backup folder for Package Reference Convert tool in Visual Studio 2017
MigrationBackup/

# Ionide (cross platform F# VS Code tools) working folder
.ionide/

# Fody - auto-generated XML schema
FodyWeavers.xsd

# VS Code files for those working on multiple tools
*.code-workspace

# Local History for Visual Studio Code

# Windows Installer files from build outputs

# JetBrains Rider
*.sln.iml

### VisualStudio Patch ###
# Additional files built by Visual Studio

# To store encryption keys
app/keys
*.pem

# End of https://www.toptal.com/developers/gitignore/api/macos,visualstudio,visualstudiocode,python,venv,dotenv,windows,linux

# Proto files
app/gen

# Include scripts folders (but exclude venv Scripts folders)
!scripts/
!*/scripts/
!monolith/scripts/
!document_service/scripts/
EOF

echo "✅ Microservice '$SERVICE_NAME' created successfully!"

echo ""
echo "🚀 Next steps:"
echo "1. cd $SERVICE_NAME"
echo "2. cp environment.config.example .env"
echo "3. Edit .env with your configuration"
echo "4. pip install -r requirements.in"
echo ""
echo "📖 Documentation:"
echo "- README.MD: API documentation"
echo "- ONBOARDING.MD: Developer guide"
echo "- ../MICROSERVICE_TEMPLATE.MD: Complete template reference"
echo ""
echo "🔍 Service will be available at:"
echo "- API: http://localhost:8000"
echo "- Docs: http://localhost:8000/docs"
echo "- Health: http://localhost:8000/v1/health"
