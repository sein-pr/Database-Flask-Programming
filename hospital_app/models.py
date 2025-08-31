# models.py - UPDATED AND CORRECTED
# This file defines the database models for the hospital management system.

import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize the SQLAlchemy object
db = SQLAlchemy()

# Models from Lab 4
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    # UPDATED: Changed from 'age' to 'date_of_birth'
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    appointments = db.relationship('Appointment', backref='patient', lazy=True, cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy=True, cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
        
    @property
    def age(self):
        """Calculates the patient's age from their date of birth."""
        if self.date_of_birth:
            today = datetime.today().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(50))
    appointments = db.relationship('Appointment', backref='doctor', lazy=True, cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Corrected attribute name is 'date'
    date_time = db.Column(db.DateTime, nullable=False) 
    diagnosis = db.Column(db.String(255), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    diagnosis_summary = db.Column(db.String(200), nullable=True)
    upload_date = db.Column(db.DateTime, nullable=False)
    full_content = db.Column(db.Text, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)

# New User model for authentication
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# New model to store access requests
class AccessRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    temporary = db.Column(db.Boolean, default=False)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
