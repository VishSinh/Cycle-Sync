# Period Tracking Backend

Period Tracking Backend is a Django project designed to provide backend functionality for period tracking applications. It includes features such as user authentication, user details management, period tracking, and data retrieval.

## Key Features

- User authentication: Allows users to register, login, and manage their accounts securely.
- User details management: Enables users to update their personal information such as name, date of birth, and physical attributes.
- Period tracking: Facilitates the tracking of menstrual cycles, including start and end dates, cycle lengths, and symptoms.
- Data retrieval: Provides endpoints to fetch user-specific period data for analysis or visualization.
- Period Prediction: Utilizes historical period data and an ML model to forecast future menstrual cycles, aiding users in planning and preparation.

## Requirements

- Python 3.x
- Django
- Django REST Framework
- MongoDB
- RabbitMQ

## API Reference

Documentation for APIs in Postman

### [Postman Link](https://www.postman.com/joint-operations-engineer-19861059/workspace/period-tracker/collection/29105784-5e45c883-b972-4da9-9c02-42dbe2fe774f?action=share&creator=29105784)

## Installation

To install and run the project locally, follow these steps:

- Clone the repository:

```bash
git clone https://github.com/VishSinh/Period-Tracker.git
```

- Navigate to the project directory:

```bash
cd Cycle-Sync
```

- Build and run the project locally:

```bash
make build-and-run-local
```

- For additional commands, use:

```bash
make help
```

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`SECRET_KEY`

`SESSION_SECRET_KEY`

`SESSION_EXPIRY`

`USER_ID_HASH_SALT`

`CELERY_BROKER_URL`

`RATE_LIMIT`

`RATE_LIMIT_WINDOW`
