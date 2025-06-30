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
            session['jwt_token'] = response.token
            session['username'] = 'temp_user' # We'll fix this in the next step
            
            flash('You were successfully logged in!', 'success')
            return redirect(url_for('profile'))

        except grpc.RpcError as e:
            flash(f"Login Error: {e.details()}", 'error')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/profile')
def profile():
    # Check if a user_id is stored in the session
    if 'jwt_token' not in session: # Check for the JWT
        flash('Please log in to view this page.', 'error')
        return redirect(url_for('login'))

    jwt_token = session['jwt_token']
    try:
        # 1. Create a gRPC request with the user's ID
        grpc_request = user_pb2.EmptyRequest()

        metadata = [('authorization', f'Bearer {jwt_token}')]
        
        # 2. Call the GetUser RPC on the backend
        response = stub.GetUser(grpc_request, metadata=metadata)
        
        # 3. The user data is in response.user. Pass it to the template.
        return render_template('profile.html', user=response.user)

    except grpc.RpcError as e:
        # Handle potential errors, like if the user was deleted from the DB
        flash(f"Could not fetch profile: {e.details()}", 'error')
        
        # If the user is not found, their session is invalid. Log them out.
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            flash(f"Your session is invalid or has expired. Please log in again.", 'error')
            session.clear()
            
        return redirect(url_for('login'))

@app.route('/profile/edit', methods=('GET', 'POST'))
def edit_profile():
    if 'user_id' not in session:
        flash('Please log in to edit your profile.', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    if request.method == 'POST':
        # now we'll update the user's profile using the form data
        # Get the updated data from the form
        username = request.form['username']
        email = request.form['email']

        try:
            # Create a gRPC request to update the user
            grpc_request = user_pb2.UpdateUserProfileRequest(
                user_id=user_id,
                username=username,
                email=email
            )
            response = stub.UpdateUserProfile(grpc_request)
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))

        except grpc.RpcError as e:
            # Handle errors from the gRPC server
            flash(f"Error updating profile: {e.details()}", 'error')
            return redirect(url_for('edit_profile'))
        
        # Handling initial page load for GET request
    try:
        grpc_request = user_pb2.GetUserRequest(user_id=user_id)
        response = stub.GetUser(grpc_request)
        return render_template('edit_profile.html', user=response.user)
    except grpc.RpcError as e:
        flash(f"Error fetching profile for edit: {e.details()}", 'error')
        return redirect(url_for('profile'))
        
@app.route('/admin')
def admin():
    # This is a placeholder for the admin page
    # In a real app, you might check if the user is an admin before showing this page
    if 'user_id' not in session:
        flash('Please log in to view this page.', 'error')
        return redirect(url_for('login'))
    try:
        # The request message for this RPC is empty beacause it doesn't need any parameters
        grpc_request = user_pb2.EmptyRequest()
        # Call the ListAllUsers RPC
        response = stub.ListAllUsers(grpc_request)
        # Pass the list of users to the template
        return render_template('admin.html', user_list=response.users)
    
    except grpc.RpcError as e:
        flash(f"An admin error occurred: {e.details()}", 'error')
        return redirect(url_for('profile'))
    

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