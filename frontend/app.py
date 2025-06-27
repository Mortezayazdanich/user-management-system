import grpc
from flask import Flask, render_template, request, redirect, url_for, flash, session

# Import our generated gRPC classes
from generated import user_pb2
from generated import user_pb2_grpc

# --- Flask App Setup ---
app = Flask(__name__)
# A secret key is needed for flashing messages
app.secret_key = 'your_super_secret_key' 

# --- gRPC Client Setup ---
# Create a connection (channel) to the gRPC server
channel = grpc.insecure_channel('localhost:50051')
# Create a client object (stub)
stub = user_pb2_grpc.UserServiceStub(channel)

# --- Basic Routes ---
@app.route('/')
def index():
    # For now, the home page just redirects to the registration page
    return redirect(url_for('register'))

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        # 1. Get data from the form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        try:
            # 2. Create the gRPC request message
            grpc_request = user_pb2.RegisterUserRequest(
                username=username, 
                email=email, 
                password=password
            )
            
            # 3. Call the gRPC server's RegisterUser method
            response = stub.RegisterUser(grpc_request)
            
            print(f"gRPC server responded: {response.user.username} created.")
            flash(f"User '{response.user.username}' created successfully! Please log in.", 'success')
            return redirect(url_for('login')) # Redirect to login after successful registration

        except grpc.RpcError as e:
            # Handle errors from the gRPC server
            error_details = e.details()
            print(f"An gRPC error occurred: {error_details}")
            flash(f"Error: {error_details}", 'error')

    # If it's a GET request, just show the registration page
    return render_template('register.html')


@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            grpc_request = user_pb2.LoginUserRequest(email=email, password=password)
            response = stub.LoginUser(grpc_request)
            
            # Store user's token (their ID) in the session
            session['user_id'] = response.token
            session['username'] = 'temp_user' # We'll fix this in the next step
            
            flash('You were successfully logged in!', 'success')
            return redirect(url_for('profile'))

        except grpc.RpcError as e:
            flash(e.details(), 'error')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/profile')
def profile():
    # Check if a user_id is stored in the session
    if 'user_id' not in session:
        flash('Please log in to view this page.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    try:
        # 1. Create a gRPC request with the user's ID
        grpc_request = user_pb2.GetUserRequest(user_id=user_id)
        
        # 2. Call the GetUser RPC on the backend
        response = stub.GetUser(grpc_request)
        
        # 3. The user data is in response.user. Pass it to the template.
        return render_template('profile.html', user=response.user)

    except grpc.RpcError as e:
        # Handle potential errors, like if the user was deleted from the DB
        flash(f"Could not fetch profile: {e.details()}", 'error')
        
        # If the user is not found, their session is invalid. Log them out.
        if e.code() == grpc.StatusCode.NOT_FOUND:
            session.clear()
            
        return redirect(url_for('login'))



@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# --- Main Execution Block ---
if __name__ == '__main__':
    # Run the Flask app on a different port than the gRPC server
    app.run(debug=True, port=5000)