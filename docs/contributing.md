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
