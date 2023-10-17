# Messaging System API

Welcome to Messaging System API, a RESTful API backend built with Django Rest Framework for handling messages between users. This platform provides a simple and efficient way for users to send, receive, and manage messages.

## Table of Contents
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Usage](#usage)

## Features
- User registration and login
- Sending and receiving messages
- Message filtering, sorting, and searching
- Marking messages as read
- Deleting messages

## Getting Started

### Prerequisites
Before you begin, ensure you have met the following requirements:
- Python 3.6+
- Django 3.0+
- Django Rest Framework 3.0+
- [Django Filters](https://django-filter.readthedocs.io/en/stable/)
- [DRF YASG (Yet Another Swagger Generator)](https://drf-yasg.readthedocs.io/en/stable/)
- [Django Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/)

### Installation
1. Clone the repository:

   ```bash
   git clone https://github.com/daniel3levi/messaging-system.git
   cd messaging-system


## API Endpoints

### User Registration
Register a new user.

- **Endpoint:** `/auth/register/`
- **Method:** POST

### User Login
Log in to the system to obtain an access token (JWT).

- **Endpoint:** `/auth/login/`
- **Method:** POST

### JWT Token Generation
Generate a new JWT token by providing valid user credentials.

- **Endpoint:** `/jwt/create/`
- **Method:** POST

### JWT Token Refresh
Refresh an existing JWT token.

- **Endpoint:** `/jwt/refresh/`
- **Method:** POST

### JWT Token Verification
Verify the validity of a JWT token.

- **Endpoint:** `/jwt/verify/`
- **Method:** POST

### Message Create
Retrieve a list of messages and create new messages.

- **Endpoint:** `/messages/`
- **Methods:** POST (Create)

### Delete Message 
Delete relationship to a user if exists, or message (if the message has no user relationships).

- **Endpoint:** `/messages/<message_id>/delete-relationship/`
- **Methods:** DELETE (Delete message or relationship to a user)

### Update Message
Mark as read if the user is one of the recipients.

- **Endpoint:** `/messages/<message_id>/update-is-read/`
- **Methods:**  PUT (Update Read Status)

### Message by ID
Get user messages by ID.

- **Endpoint:** `/messages/<message_id>`
- **Method:** GET

### Message List, Filter, Sort, and Search Messages
Get all user messages, filter, sort, and search messages using query parameters.

- **Endpoint:** `/messages/`
- **Options:**
     - filter:
       1. `/messages/?filter=sent/`
       2. `/messages/?filter=received/`
       3. `/messages/?filter=received/is_read=true/`
       4. `/messages/?filter=received/is_read=false/`
    - ordering:
        1. `/messages/?ordering=creation_date` (Newest to Oldest)
        2. `/messages/?ordering=-creation_date` (Oldest to Newest)
    - search:
        1. `/messages/?search=<text>`
- **Method:** GET

## Authentication

This API uses JWT (JSON Web Tokens) for authentication. To access protected endpoints, you need to include a JWT token in the Authorization header of your HTTP requests. Here's how you can obtain a JWT token:

- **User Registration:** Use the `/auth/register/` endpoint to create a new user. Upon successful registration, you will receive a confirmation message.

- **User Login:** Log in to the system by providing your username and password via the `/auth/login/` endpoint. Upon successful login, you will receive a JWT token in the response, which you can use to access protected endpoints.

## Usage

You can interact with the API using the provided endpoints. Detailed API documentation is available via Swagger and ReDoc, making it easy to understand request formats and response structures. To access the documentation:

- **Swagger UI:** Visit http://127.0.0.1:8000/swagger/ in your web browser.

- **ReDoc:** Visit http://127.0.0.1:8000/redoc/ in your web browser.


