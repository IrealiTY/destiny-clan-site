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
pip install -r requirements.txt
```

Run the API:

```python
# Run from project root
python clan.py --debug
```

### Frontend

Install JS dependencies:

```
yarn install
```

Run the frontend:

```
yarn serve
```
