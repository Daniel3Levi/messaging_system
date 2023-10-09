# Messaging System - Django Rest Framework

Messaging System is a RESTful API backend built with Django Rest Framework for handling messages between users. 
It provides a simple and efficient platform for users to send, receive, and manage messages.

## Features

- User registration and login with token-based authentication.
- Create, Read, Update operations for messages.
- View all messages for a specific user.
- Retrieve unread messages.
- Mark messages as read.
- Filter messages based on sender, receiver, and read status.

## Installation

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/daniel3levi/messaging-system.git

### Overview of the available API endpoints
**API Entry Point:** `/api/v1`

### User Authentication

**User Registration**
- **URL:** `/auth/register/`
- **HTTP Method:** POST
- **Description:** Register a new user.
- **View:** `UserRegistrationView`

**User Login**
- **URL:** `/auth/login/`
- **HTTP Method:** POST
- **Description:** Log in an existing user and obtain an authentication token.
- **View:** `UserLoginView`

### Messaging System

**Create New Message**
- **URL:** `/new-message/`
- **HTTP Method:** POST
- **Description:** Create and send a new message.
- **View:** `MessageCreateView`

**Read Message**
- **URL:** `/read-message/<int:pk>/`
- **HTTP Method:** PATCH
- **Description:** Retrieve and view a specific message by its ID.
- **View:** `MessageDetailView`

**Unread Messages**
- **URL:** `/unread-messages/`
- **HTTP Method:** GET
- **Description:** Retrieve a list of unread messages.
- **View:** `UnreadMessageListView`

**Sent Messages**
- **URL:** `/sent-messages/`
- **HTTP Method:** GET
- **Description:** Retrieve a list of messages sent by the logged-in user.
- **View:** `SentMessagesListView`

**Received Messages**
- **URL:** `/received-messages/`
- **HTTP Method:** GET
- **Description:** Retrieve a list of messages received by the logged-in user.
- **View:** `ReceivedMessagesListView`

