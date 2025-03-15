# Django Parking Management System

Welcome to the **Django Parking Management System**! This project is a RESTful API-based application that manages parking-related operations, including user registration, authentication, parking image processing, and real-time availability monitoring. The system is designed to be scalable and flexible, catering to both web and mobile users.

---

## Table of Contents

- [Django Parking Management System](#django-parking-management-system)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
  - [Features](#features)
  - [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [Steps](#steps)
  - [API Endpoints](#api-endpoints)
    - [Authentication](#authentication)
    - [Parking Management](#parking-management)
    - [Mobile-Specific Endpoints](#mobile-specific-endpoints)
  - [Dependencies](#dependencies)
  - [Contributing](#contributing)
  - [License](#license)
  - [Contact](#contact)

---

## Project Overview

This project provides a robust solution for managing parking spaces. It includes features such as user authentication, parking image annotation, real-time parking space monitoring, and integration with machine learning models for advanced processing (e.g., YOLOv8). The system is built using Django and Django REST Framework (DRF), ensuring a clean and maintainable codebase.

---

## Features

- **User Authentication**: Secure user registration and login via JWT tokens.
- **Parking Management**:
  - Associate parking spaces with users.
  - Upload and process parking images.
  - Create and manage annotations for parking spaces.
- **Real-Time Monitoring**:
  - Process uploaded images to detect available parking spots.
  - Update parking availability dynamically.
- **Mobile Support**:
  - Dedicated endpoints for mobile applications.
  - Retrieve parking images and spot information in Base64 format.
- **Scalability**:
  - Designed to handle multiple parking spaces and users efficiently.

---

## Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL or SQLite (for development)
- Git

### Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/django-parking-management.git
   cd django-parking-management
   ```

2. **Set Up Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Update the `.env` file with your database credentials and other configurations.

5. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start the Development Server**
   ```bash
   python manage.py runserver
   ```

7. **Access the API**
   - Open your browser or use tools like Postman to interact with the API at `http://localhost:8000`.

---

## API Endpoints

The following endpoints are available:

### Authentication

- **Register User**
  - URL: `/register/`
  - Method: `POST`
  - Description: Register a new user.

- **Login User**
  - URL: `/login/`
  - Method: `POST`
  - Description: Authenticate a user and retrieve JWT tokens.

- **Mobile Registration**
  - URL: `/register-mobile/`
  - Method: `POST`
  - Description: Register a new mobile user.

- **Mobile Login**
  - URL: `/login-mobile/`
  - Method: `POST`
  - Description: Authenticate a mobile user.

---

### Parking Management

- **Check Annotations**
  - URL: `/check-annotations/`
  - Method: `GET`
  - Description: Check if annotations exist for the user's parking.

- **Create Annotations**
  - URL: `/create-annotations/`
  - Method: `POST`
  - Description: Create annotations for the user's parking.

- **View User Parking**
  - URL: `/my-parking/`
  - Method: `GET`
  - Description: Retrieve details of the user's parking.

- **View User Parking Image**
  - URL: `/my-parking/image/`
  - Method: `GET`
  - Description: Retrieve the image associated with the user's parking.

- **Process Image**
  - URL: `/process-image/`
  - Method: `POST`
  - Description: Upload an image and process it to detect parking spots.

---

### Mobile-Specific Endpoints

- **List Parkings**
  - URL: `/parking/`
  - Method: `GET`
  - Description: Retrieve a list of all parkings.

- **View Parking Image**
  - URL: `/parking/image/`
  - Method: `GET`
  - Description: Retrieve the image and spot information for a specific parking.

---

## Dependencies

- **Django**: Web framework.
- **Django REST Framework (DRF)**: For building APIs.
- **Simple JWT**: For JWT-based authentication.
- **OpenCV**: For image processing.
- **NumPy**: For numerical computations.
- **YOLOv8**: For object detection (parking spot monitoring).

Install dependencies using:
```bash
pip install -r requirements.txt
```

---

## Contributing

We welcome contributions from the community! To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeatureName`).
3. Commit your changes (`git commit -m "Add some feature"`).
4. Push to the branch (`git push origin feature/YourFeatureName`).
5. Open a pull request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

For questions or feedback, feel free to reach out:

- Email: 321abdulfatah@gmail.com
- GitHub: [GitHub Profile](https://github.com/321abdulfatah)

---

Thank you for using the **Django Parking Management System**! We hope this project meets your needs and inspires further innovation.