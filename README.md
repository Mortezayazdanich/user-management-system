# User Management System

A modern user management system built with Python, featuring a gRPC backend service and a Flask web frontend. This system provides secure user registration, authentication, and profile management capabilities.

## 🏗️ Architecture

- **Backend**: gRPC server with SQLite database
- **Frontend**: Flask web application with HTML templates
- **Authentication**: JWT-based authentication with bcrypt password hashing
- **Database**: SQLite for data persistence
- **Protocol**: Protocol Buffers (protobuf) for service definitions

## 🚀 Features

- **User Registration**: Create new user accounts with username, email, and password
- **User Authentication**: Secure login with JWT token generation
- **Profile Management**: View user profiles with authentication
- **Session Management**: Secure session handling with token validation
- **Admin Panel**: Administrative interface for user management (planned)
- **Password Security**: bcrypt hashing for secure password storage

## 📁 Project Structure

```
user-management-system/
├── backend/
│   ├── server.py          # gRPC server implementation
│   └── database.py        # Database initialization and utilities
├── frontend/
│   ├── app.py            # Flask web application
│   └── templates/        # HTML templates
│       ├── base.html
│       ├── login.html
│       ├── register.html
│       ├── profile.html
│       ├── edit_profile.html
│       └── admin.html
├── protos/
│   └── user.proto        # Protocol buffer definitions
├── generated/
│   ├── user_pb2.py       # Generated protobuf classes
│   └── user_pb2_grpc.py  # Generated gRPC classes
└── README.md
```

## 🛠️ Installation

### Prerequisites

- Python 3.7+
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd user-management-system
   ```

2. **Install dependencies**
   ```bash
   pip install grpcio grpcio-tools flask bcrypt pyjwt python-dotenv
   ```

3. **Environment Setup**
   Create a `.env` file in the root directory:
   ```
   JWT_SECRET_KEY=your_super_secret_jwt_key_here
   ```

4. **Generate gRPC code** (if needed)
   ```bash
   python -m grpc_tools.protoc -I./protos --python_out=./generated --grpc_python_out=./generated ./protos/user.proto
   ```

## 🚀 Usage

### Running the Backend Server

1. **Start the gRPC server**
   ```bash
   python backend/server.py
   ```
   The server will start on port `50051` and automatically initialize the SQLite database.

### Running the Frontend Application

1. **Start the Flask web server**
   ```bash
   python frontend/app.py
   ```
   The web application will be available at `http://localhost:5000`

### Using the Application

1. **Register a new user**: Navigate to `/register` and create an account
2. **Login**: Use your credentials to log in at `/login`
3. **View Profile**: Access your profile information at `/profile`
4. **Logout**: End your session using the logout functionality

## 🔧 API Endpoints

### gRPC Service Methods

- `RegisterUser`: Create a new user account
- `LoginUser`: Authenticate and receive JWT token
- `GetUser`: Retrieve user profile (requires authentication)
- `UpdateUserProfile`: Update user information (planned)
- `ListAllUsers`: Admin function to list all users (planned)

### Web Routes

- `/`: Home page (redirects to register)
- `/register`: User registration form
- `/login`: User login form
- `/profile`: User profile page (protected)
- `/profile/edit`: Edit profile page (planned)
- `/admin`: Admin panel (planned)
- `/logout`: Logout and clear session

## 🔐 Security Features

- **Password Hashing**: bcrypt for secure password storage
- **JWT Authentication**: Stateless authentication with token expiration
- **Session Management**: Secure session handling in Flask
- **Input Validation**: Server-side validation for all user inputs
- **Error Handling**: Proper error responses and user feedback

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL
);
```

## 🧪 Development

### Protocol Buffer Schema

The service is defined in `protos/user.proto` with the following key messages:
- `User`: Core user data structure
- `RegisterUserRequest`: User registration payload
- `LoginUserRequest`: Login credentials
- `LoginUserResponse`: JWT token response
- `UserResponse`: Standard user data response

### Code Generation

To regenerate the gRPC code after modifying the `.proto` file:
```bash
python -m grpc_tools.protoc -I./protos --python_out=./generated --grpc_python_out=./generated ./protos/user.proto
```

## 🚧 Roadmap

- [ ] Complete profile editing functionality
- [ ] Admin panel implementation
- [ ] Password reset functionality
- [ ] Email verification
- [ ] Rate limiting
- [ ] Docker containerization
- [ ] Unit and integration tests
- [ ] API documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions or support, please open an issue in the GitHub repository.
