import grpc
from concurrent import futures
import time
import uuid
import bcrypt
import sqlite3
import jwt
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Import the generated classes
from generated import user_pb2
from generated import user_pb2_grpc

# Import our database initialization function
from .database import init_db

# THIS MUST BE AT THE TOP LEVEL OF THE SCRIPT
load_dotenv()


# Create a class to define the server functions, derived from
# user_pb2_grpc.UserServiceServicer
class UserServiceServicer(user_pb2_grpc.UserServiceServicer):

    def RegisterUser(self, request, context):
        print("RegisterUser request received")
        username = request.username
        email = request.email
        password = request.password

        if not all([username, email, password]):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("All fields (username, email, password) are required.")
            return user_pb2.UserResponse()

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        try:
            user_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO users (id, username, email, hashed_password) VALUES (?, ?, ?, ?)",
                (user_id, username, email, hashed_password)
            )
            conn.commit()
            print(f"User {username} created with ID {user_id}")

            user_message = user_pb2.User(id=user_id, username=username, email=email)
            return user_pb2.UserResponse(user=user_message)
        except sqlite3.IntegrityError:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details("User with this username or email already exists.")
            return user_pb2.UserResponse()
        finally:
            conn.close()

    def LoginUser(self, request, context):
        print("LoginUser request received")
        email = request.email
        password = request.password.encode('utf-8')

        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user_record = cursor.fetchone()
        conn.close()

        if user_record and bcrypt.checkpw(password, user_record['hashed_password']):
            print(f"User {user_record['username']} logged in successfully.")
            
            payload = {
                'user_id': user_record['id'],
                'username': user_record['username'],
                'exp': datetime.utcnow() + timedelta(hours=24),
                'iat': datetime.utcnow()
            }
            
            secret_key = os.getenv('JWT_SECRET_KEY')
            encoded_token = jwt.encode(payload, secret_key, algorithm='HS256')
            
            return user_pb2.LoginUserResponse(token=encoded_token)

        print("Invalid login attempt")
        context.set_code(grpc.StatusCode.UNAUTHENTICATED)
        context.set_details("Invalid email or password")
        return user_pb2.LoginUserResponse()

    def GetUser(self, request, context):
        metadata = dict(context.invocation_metadata())
        auth_header = metadata.get('authorization', None)

        if not auth_header:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Missing authentication token")
            return user_pb2.UserResponse()

        token = auth_header.replace('Bearer ', '')
        
        try:
            secret_key = os.getenv('JWT_SECRET_KEY')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Token has expired. Please log in again.")
            return user_pb2.UserResponse()
        except jwt.InvalidTokenError:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            context.set_details("Invalid token. Please log in again.")
            return user_pb2.UserResponse()

        print(f"GetUser request received for user_id from token: {user_id}")
        conn = sqlite3.connect('users.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
        user_record = cursor.fetchone()
        conn.close()

        if user_record:
            user_message = user_pb2.User(
                id=user_record['id'],
                username=user_record['username'],
                email=user_record['email']
            )
            return user_pb2.UserResponse(user=user_message)
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("User not found")
            return user_pb2.UserResponse()

    def UpdateUserProfile(self, request, context):
        # Placeholder for future implementation
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ListAllUsers(self, request, context):
        # Placeholder for future implementation
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
    port = "50051"
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"gRPC server started, listening on port {port}.")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    init_db()
    serve()