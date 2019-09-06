# Contributing to the project

Disclaimer: Development has only been tested on Windows!

## Requirements

Backend (API) / worker processes:
* Python3
  * pip
  * virtualenv

Frontend:
* Yarn: https://yarnpkg.com/en/docs/install
* vue-cli: https://cli.vuejs.org/guide/installation.html

## Running the project locally

First, clone the repo using Git.

### Database

<database setup walkthrough>
 
The project started out using sqlite3, but eventually moved for PostgreSQL. I believe this could still work with sqlite3 if you did not want to go through the trouble of setting up PostgreSQL.

Initialize alembic - this is used for database schema generation and migrations:

```
alembic init swampfoxdev
```

### Backend (API)

Install Python dependencies:

```python
# Create a virtualenv, run this in the cloned git project folder
python -m venv destiny-clan-site

# Active the virtualenv
. .\destiny-clan-site\Scripts\activate.ps1

# Install python dependencies
pip install -r requirements.txt
```

Run the API:

```python
# Run from project root
python clan.py --debug
```

### Frontend

Yarn is used to manage JS dependencies, and it also requires NodeJS. I would recommend installing Chocolatey to install both of these: https://chocolatey.org/

```
choco install nodejs
choco install yarn
```

Install JS dependencies:

```
yarn install
```

Run the frontend:

```
yarn serve
```
