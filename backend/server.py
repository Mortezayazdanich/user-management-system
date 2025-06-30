import grpc
from concurrent import futures
import time
import uuid
import bcrypt
import sqlite3

# Import the generated classes
from generated import user_pb2
from generated import user_pb2_grpc

# Import our database initialization function
from .database import init_db

# Import Authentication libraries
import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta


# Create a class to define the server functions, derived from
# user_pb2_grpc.UserServiceServicer
class UserServiceServicer(user_pb2_grpc.UserServiceServicer):

    # This is the implementation of the RegisterUser RPC
    def RegisterUser(self, request, context):
        print("RegisterUser request received")
        # Get data from the request object
        username = request.username
        email = request.email
        password = request.password

        # --- Input Validation (Basic) ---
        if not all([username, email, password]):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("All fields (username, email, password) are required.")
            return user_pb2.UserResponse()

        # --- Password Hashing ---
        # NEVER store plain text passwords!
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # --- Database Interaction ---
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        try:
            # Generate a unique ID for the user
            user_id = str(uuid.uuid4())
            
            # Insert the new user into the database
            cursor.execute(
                "INSERT INTO users (id, username, email, hashed_password) VALUES (?, ?, ?, ?)",
                (user_id, username, email, hashed_password)
            )
            conn.commit()
            print(f"User {username} created with ID {user_id}")

            # --- Prepare and Return the Response ---
            # Create a User message
            user_message = user_pb2.User(id=user_id, username=username, email=email)
            # Wrap it in a UserResponse
            return user_pb2.UserResponse(user=user_message)

        except sqlite3.IntegrityError as e:
            # This error occurs if the username or email already exists (due to UNIQUE constraint)
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(f"User with this username or email already exists.")
            return user_pb2.UserResponse()
        finally:
            conn.close()

    # We will implement the other methods later
    def LoginUser(self, request, context):
        print("LoginUser request received")
        email = request.email
        password = request.password.encode('utf-8')

        conn = sqlite3.connect('users.db')
        # Use Row factory to access columns by name
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()

        # Find the user by email
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user_record = cursor.fetchone()
        conn.close()

        if user_record:
            # Check if the provided password matches the hashed password in the DB
            if bcrypt.checkpw(password, user_record['hashed_password']):
                print(f"User {user_record['username']} logged in successfully.")
                
                payload = {
                'user_id': user_record['id'],
                'username': user_record['username'],
                'exp': datetime.utcnow() + timedelta(hours=24),  # Expiration time
                'iat': datetime.utcnow()  # Issued at time
                }
            
                secret_key = os.getenv('JWT_SECRET_KEY')
                token = jwt.encode(payload, secret_key, algorithm='HS256')

                return user_pb2.LoginUserResponse(token=token)

        # If user not found or password incorrect
        print("Invalid login attempt")
        context.set_code(grpc.StatusCode.UNAUTHENTICATED)
        context.set_details("Invalid email or password")
        return user_pb2.LoginUserResponse()
    
    def GetUser(self, request, context):
        print(f"GetUser request received for user_id: {request.user_id}")
        # Get metadata from the call
        metadata = dict(context.invocation_metadata())
        token = metadata.get('authorization', None)

        if not token:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Missing authentication token")
            return user_pb2.UserResponse()

        # The token comes in as "Bearer <token>"
        token = token.replace('Bearer ', '')
        
        try:
            # Decode and verify the JWT
            secret_key = os.getenv('JWT_SECRET_KEY')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = payload['user_id']

        except jwt.ExpiredSignatureError:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Token has expired")
            return user_pb2.UserResponse()
        except jwt.InvalidTokenError:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Invalid token")
            return user_pb2.UserResponse()

        # If token is valid, fetch user from DB
        print(f"GetUser request received for user_id from token: {user_id}")
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
        user_record = cursor.fetchone()
        conn.close()

        if user_record:
            user = user_pb2.User(
                id=user_record["id"],
                username=user_record["username"],
                email=user_record["email"]
            )
            return user_pb2.UserResponse(user=user)
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('User not found')
            return user_pb2.UserResponse()
        

    def UpdateUserProfile(self, request, context):
        user_id = request.user_id
        new_username = request.username
        new_email = request.email
        print(f"UpdateUserProfile request received for user_id: {user_id}")

        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Check if the new username and email is being used by another user
            cursor.execute("SELECT id FROM users WHERE id != ? AND (username = ? OR email = ?)", (user_id, new_username, new_email))
            if cursor.fetchone():
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details('Username or email already in use by another user')
                return user_pb2.UserResponse()
            
            # If clear, proceed with the update
            # Update the user's profile
            cursor.execute("Update users SET username = ?, email = ? WHERE id = ?", (new_username, new_email, user_id))
            conn.commit()
        
            print(f"User {user_id} updated successfully.")
            # If the update was successful, we can return the updated user information
            # Since we have the updated data, there's no need to fetch it again from the database.
            # Return the updated user information
            updated_user = user_pb2.User(
                id=user_id,
                username=new_username,
                email=new_email
            )
            return user_pb2.UserResponse(user=updated_user)
        finally:
            conn.close()
        # If we reach here, it means the user was not found or some other error occurred
    
    def ListAllUsers(self, request, context):
        print("ListAllUsers request received")
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT id, username, email FROM users ORDER BY username")
            user_records = cursor.fetchall()

            # Create a list of User messages
            users = []
            for record in user_records:
                users.append(user_pb2.User(
                    id=record["id"],
                    username=record["username"],
                    email=record["email"]
                ))

            # Return the list of users wrapped in a ListUsersResponse
            return user_pb2.ListUsersResponse(users=users)
        finally:
            conn.close()

    




# Function to create and start the server
def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Add the defined servicer to the server
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)

    # Listen on port 50051
    port = "50051"
    server.add_insecure_port(f"[::]:{port}")

    # Start the server
    server.start()
    print(f"gRPC server started, listening on port {port}.")
    
    # Keep the server running
    try:
        while True:
            time.sleep(86400) # One day in seconds
    except KeyboardInterrupt:
        server.stop(0)

# Main execution block
if __name__ == '__main__':
    # Initialize the database when the server starts
    init_db()
    serve()