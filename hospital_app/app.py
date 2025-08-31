# app.py - UPDATED
# This file contains all the Flask application routes and logic.

import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, Response, jsonify
from models import db, Patient, Doctor, Appointment, MedicalRecord, User, AccessRequest
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import re
from werkzeug.security import generate_password_hash, check_password_hash

# Flask App Configuration
app = Flask(__name__)
# A secret key is required for sessions
app.config['SECRET_KEY'] = 'your_very_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure the directory for file uploads
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize the SQLAlchemy object with the Flask app
db.init_app(app)

# Create the database tables when the app starts
with app.app_context():
    db.create_all()
    if not Doctor.query.first():
        sample_doctors = [
            Doctor(first_name='John', last_name='Doe', specialization='Cardiology'),
            Doctor(first_name='Jane', last_name='Smith', specialization='Neurology'),
            Doctor(first_name='Michael', last_name='Brown', specialization='Pediatrics')
        ]
        db.session.bulk_save_objects(sample_doctors)
        db.session.commit()
    
    # Check if Administrator account exists, if not, create it
    if not User.query.filter_by(username='Administrator').first():
        admin = User(username='Administrator')
        admin.set_password('password') # The default admin password
        db.session.add(admin)
        db.session.commit()

# --- Authentication Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['logged_in'] = True
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            return render_template('login.html', error='Invalid credentials. Please try again.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logs the user out by clearing the session."""
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# --- New Route for Handling Access Requests ---
@app.route('/request_access', methods=['POST'])
def request_access():
    """Handles new access requests from users."""
    try:
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        reason = request.form.get('reason')
        temporary = 'temporary' in request.form
        
        # Simple validation
        if not first_name or not last_name or not reason:
            flash('Please fill out all required fields.', 'danger')
            return redirect(url_for('login'))

        new_request = AccessRequest(
            first_name=first_name,
            last_name=last_name,
            reason=reason,
            temporary=temporary
        )
        db.session.add(new_request)
        db.session.commit()
        flash('Your access request has been submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')
    
    return redirect(url_for('login'))


# --- Protected Routes (require a logged-in user) ---

@app.route('/')
def index():
    """
    Renders the main dashboard showing all patients, doctors, and appointments.
    This route is now protected by a login check.
    """
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    try:
        patients = Patient.query.all()
        appointments = Appointment.query.all()
        doctors = Doctor.query.all()
        return render_template(
            'index.html',
            patients=patients,
            appointments=appointments,
            doctors=doctors
        )
    except Exception as e:
        print(f"An error occurred while fetching data: {e}")
        return "An internal error occurred.", 500

@app.route('/add_patient_form')
def add_patient_form():
    """Renders the form to add a new patient."""
    # Login check added here
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('add_patient.html')

@app.route('/add_patient', methods=['POST'])
def add_patient():
    """Handles the creation of a new patient."""
    # Login check added here
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        # Changed from 'age' to 'date_of_birth'
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        
        # New: Convert the date string to a datetime object
        date_of_birth_obj = datetime.strptime(date_of_birth, '%Y-%m-%d').date()

        new_patient = Patient(
            first_name=first_name,
            last_name=last_name,
            # Pass the date object to the model
            date_of_birth=date_of_birth_obj,
            gender=gender
        )
        db.session.add(new_patient)
        db.session.commit()
        flash('Patient added successfully!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while adding a patient: {e}", 'danger')
        return redirect(url_for('add_patient_form'))

@app.route('/add_doctor', methods=['POST'])
def add_doctor():
    """Handles the creation of a new doctor."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        specialization = request.form['specialization']

        new_doctor = Doctor(
            first_name=first_name,
            last_name=last_name,
            specialization=specialization
        )
        db.session.add(new_doctor)
        db.session.commit()
        flash('Doctor added successfully!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while adding a doctor: {e}", 'danger')
        return redirect(url_for('add_doctor_form')) 

@app.route('/add_appointment_form')
def add_appointment_form():
    """Renders the form to schedule a new appointment."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    return render_template('add_appointment.html', patients=patients, doctors=doctors)

@app.route('/add_appointment', methods=['POST'])
def add_appointment():
    """Handles the creation of a new appointment."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        # Get patient_id, doctor_id, date, and time from the form
        patient_id = request.form['patient_id']
        doctor_id = request.form['doctor_id']
        datetime_str = request.form['appt-datetime']
        diagnosis_str = request.form['appt-diagnosis']

        # Convert the datetime string to a single datetime object
        appointment_datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
        
        # Check if an appointment already exists for this doctor at this date and time
        existing_appointment = Appointment.query.filter_by(
            doctor_id=doctor_id,
            date=appointment_datetime
        ).first()

        if existing_appointment:
            # If a conflict is found, flash an error message and redirect
            flash('This doctor already has an appointment at this date and time. Please choose another time.', 'danger')
            return redirect(url_for('add_appointment_form'))
            
        new_appointment = Appointment(
            # Pass the full datetime object
            date=appointment_datetime,
            diagnosis=diagnosis_str,
            patient_id=patient_id,
            doctor_id=doctor_id
        )
        db.session.add(new_appointment)
        db.session.commit()
        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while adding an appointment: {e}", 'danger')
        return redirect(url_for('add_appointment_form'))

@app.route('/get_booked_appointments/<int:doctor_id>/<string:selected_date>', methods=['GET'])
def get_booked_appointments(doctor_id, selected_date):
    """
    API endpoint to get booked appointment times for a specific doctor on a given date.
    Returns a JSON list of booked times (e.g., ["09:30", "11:00"]).
    """
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Convert the selected_date string from the URL to a date object
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()

        # Query the database for appointments for the given doctor on the specified date
        booked_appointments = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            db.func.date(Appointment.date) == date_obj
        ).all()
        
        # Extract the time part from each booked appointment and format it as a string
        booked_times = [appt.date.strftime('%H:%M') for appt in booked_appointments]
        
        # Return the list of booked times as a JSON response
        return jsonify(booked_times)
    
    except Exception as e:
        print(f"Error fetching booked appointments: {e}")
        return jsonify({'error': 'An internal server error occurred.'}), 500

@app.route('/delete_patient/<int:id>')
def delete_patient(id):
    """Deletes a patient and their associated records."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        patient_to_delete = Patient.query.get_or_404(id)
        # Because of cascade='all, delete-orphan' in models.py,
        # associated appointments and medical records will be deleted automatically.
        db.session.delete(patient_to_delete)
        db.session.commit()
        flash('Patient deleted successfully!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting a patient: {e}", 'danger')
        return redirect(url_for('index'))

@app.route('/patient_details/<int:id>')
def patient_details(id):
    """Displays the details and medical records for a specific patient."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    patient = Patient.query.get_or_404(id)
    filter_type = request.args.get('filter', 'all')
    records = []
    
    if filter_type == 'current':
        start_date = datetime.utcnow() - timedelta(days=30)
        records = MedicalRecord.query.filter(
            MedicalRecord.patient_id == id,
            MedicalRecord.upload_date >= start_date
        ).order_by(MedicalRecord.upload_date.desc()).all()
    elif filter_type == 'previous':
        start_date = datetime.utcnow() - timedelta(days=30)
        records = MedicalRecord.query.filter(
            MedicalRecord.patient_id == id,
            MedicalRecord.upload_date < start_date
        ).order_by(MedicalRecord.upload_date.desc()).all()
    else: # Default to 'all'
        records = MedicalRecord.query.filter_by(patient_id=id).order_by(MedicalRecord.upload_date.desc()).all()

    return render_template('patient_details.html', patient=patient, records=records, filter_type=filter_type)

@app.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
def edit_patient_form(id):
    """Renders the form to edit patient details and handles the form submission."""
    if not session.get('logged_in'):
        flash("You must be logged in to access this page.", "warning")
        return redirect(url_for('login'))
    
    patient = Patient.query.get_or_404(id)
    
    if request.method == 'POST':
        full_name = request.form['full_name']
        name_parts = full_name.split(' ', 1)
        patient.first_name = name_parts[0]
        if len(name_parts) > 1:
            patient.last_name = name_parts[1]
        else:
            patient.last_name = ''
        
        # Changed from 'age' to 'date_of_birth'
        patient.date_of_birth = request.form['date_of_birth']
        patient.gender = request.form['gender']
        
        try:
            db.session.commit()
            flash("Patient details updated successfully!", "success")
            return redirect(url_for('patient_details', id=patient.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating patient: {e}", "danger")
            return redirect(url_for('edit_patient_form', id=patient.id))
            
    return render_template('edit_patient.html', patient=patient)


@app.route('/update_patient/<int:id>', methods=['POST'])
def update_patient(id):
    """Handles the update logic for a patient."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    try:
        patient = Patient.query.get_or_404(id)
        patient.first_name = request.form['first_name']
        patient.last_name = request.form['last_name']
        # Changed from 'age' to 'date_of_birth'
        patient.date_of_birth = request.form['date_of_birth']
        patient.gender = request.form['gender']
        db.session.commit()
        flash('Patient details updated successfully!', 'success')
        return redirect(url_for('patient_details', id=patient.id))
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')
        return redirect(url_for('edit_patient_form', id=id))

@app.route('/upload_record/<int:patient_id>', methods=['POST'])
def upload_record(patient_id):
    """Handles the upload of a new medical record for a patient."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('patient_details', id=patient_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('patient_details', id=patient_id))
        
    if file:
        file_content = file.read().decode('utf-8')
        file.seek(0)
        
        lines = file_content.splitlines()
        diagnosis = "No-Diagnosis"
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        diagnosis_match = re.search(r'Diagnosis:\s*(.*)', file_content, re.IGNORECASE)
        date_match = re.search(r'Date:\s*(.*)', file_content, re.IGNORECASE)

        if diagnosis_match:
            diagnosis = diagnosis_match.group(1).strip()
        if date_match:
            date_str = date_match.group(1).strip()
            
        truncated_diagnosis = ''.join(e for e in diagnosis[:11] if e.isalnum() or e.isspace()).strip()
        
        try:
            parsed_date = datetime.strptime(date_str, '%B %d, %Y')
            formatted_date = parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            formatted_date = datetime.now().strftime('%Y-%m-%d')
            
        new_filename = f"{truncated_diagnosis}_{formatted_date}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        
        file.save(filepath)
        
        new_record = MedicalRecord(
            filename=new_filename,
            file_path=filepath,
            diagnosis_summary=truncated_diagnosis,
            upload_date=datetime.utcnow(),
            full_content=file_content,
            patient_id=patient_id
        )
        db.session.add(new_record)
        db.session.commit()
        flash('Medical record uploaded and updated successfully!', 'success')
        
    return redirect(url_for('patient_details', id=patient_id))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serves uploaded files from the uploads directory."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/export_all_records/<int:patient_id>')
def export_all_records(patient_id):
    """Exports all medical records for a patient as a single text file."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    patient = Patient.query.get_or_404(patient_id)
    records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.upload_date.asc()).all()
    
    output = f"Medical Records for Patient: {patient.full_name}\n"
    output += "="*50 + "\n\n"
    
    for record in records:
        output += f"--- Record ID: {record.id} ---\n"
        output += record.full_content + "\n\n"
        output += "-"*30 + "\n\n"
        
    response = Response(output, mimetype='text/plain')
    response.headers['Content-Disposition'] = f"attachment; filename=all_records_{patient.id}.txt"
    return response

@app.route('/export_record/<int:record_id>')
def export_record(record_id):
    """Exports a single medical record as a text file."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    record = MedicalRecord.query.get_or_404(record_id)
    
    response = Response(record.full_content, mimetype='text/plain')
    response.headers['Content-Disposition'] = f"attachment; filename={record.filename}"
    return response

@app.route('/get_record_content/<int:record_id>', methods=['GET'])
def get_record_content(record_id):
    """API endpoint to get the full text content of a single medical record."""
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    record = MedicalRecord.query.get_or_404(record_id)
    return jsonify({'content': record.full_content})

# --- Administrator Routes ---

@app.route('/list_users')
def list_users():
    """Admin route to see all registered users."""
    if not session.get('logged_in') or session.get('username') != 'Administrator':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    users = User.query.all()
    return render_template('list_users.html', users=users)

@app.route('/give_access', methods=['GET', 'POST'])
def give_access():
    """Admin route to add a new user to the database."""
    if not session.get('logged_in') or session.get('username') != 'Administrator':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'warning')
            return render_template('give_access.html')

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'User "{username}" created successfully.', 'success')
        return redirect(url_for('list_users'))

    return render_template('give_access.html')

@app.route('/see_access_requests')
def see_access_requests():
    """Admin route to see all pending access requests."""
    if not session.get('logged_in') or session.get('username') != 'Administrator':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    pending_requests = AccessRequest.query.all()
    return render_template('see_access_requests.html', requests=pending_requests)

@app.route('/approve_request/<int:request_id>', methods=['POST'])
def approve_request(request_id):
    """Admin route to approve an access request and create a new user."""
    if not session.get('logged_in') or session.get('username') != 'Administrator':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    access_request = AccessRequest.query.get_or_404(request_id)
    username = f"{access_request.first_name.lower()}_{access_request.last_name.lower()}"
    
    # Check if a user with this username already exists
    if User.query.filter_by(username=username).first():
        flash(f'A user with username "{username}" already exists. Please create a user manually.', 'warning')
        db.session.delete(access_request)
        db.session.commit()
        return redirect(url_for('see_access_requests'))

    # Create a new user with a temporary password (can be changed later)
    new_user = User(username=username)
    new_user.set_password("temp_password")
    db.session.add(new_user)
    
    # Delete the access request from the table
    db.session.delete(access_request)
    db.session.commit()
    
    flash(f'Access for {access_request.full_name} approved. Default username: {username}, Password: temp_password', 'success')
    return redirect(url_for('see_access_requests'))

@app.route('/deny_request/<int:request_id>', methods=['POST'])
def deny_request(request_id):
    """Admin route to deny an access request."""
    if not session.get('logged_in') or session.get('username') != 'Administrator':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    access_request = AccessRequest.query.get_or_404(request_id)
    db.session.delete(access_request)
    db.session.commit()
    
    flash(f'Access request from {access_request.full_name} denied.', 'success')
    return redirect(url_for('see_access_requests'))

# New route to delete a user (Admin only)
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """Admin route to delete a user."""
    if not session.get('logged_in') or session.get('username') != 'Administrator':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    user_to_delete = User.query.get_or_404(user_id)

    # Prevent the admin from deleting their own account
    if user_to_delete.username == 'Administrator':
        flash('Cannot delete the Administrator account.', 'danger')
        return redirect(url_for('list_users'))

    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'User "{user_to_delete.username}" deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')
    
    return redirect(url_for('list_users'))

# New route to reset a user's password (Admin only)
@app.route('/reset_password/<int:user_id>', methods=['POST'])
def reset_password(user_id):
    """Admin route to reset a user's password to a temporary default."""
    if not session.get('logged_in') or session.get('username') != 'Administrator':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    user_to_reset = User.query.get_or_404(user_id)
    new_password = "temp_password"
    
    user_to_reset.set_password(new_password)
    
    try:
        db.session.commit()
        flash(f'Password for user "{user_to_reset.username}" has been reset to "{new_password}".', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {e}', 'danger')
    
    return redirect(url_for('list_users'))

if __name__ == '__main__':
    app.run(debug=True)
