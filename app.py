from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = "keksdbkfbekd9238982ssbdnbsy"

# create database object
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
db = SQLAlchemy(app)

# Doctors table
class Doctors(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    max_patients = db.Column(db.Integer, nullable=False)

    # constructor
    def __init__(self, name, specialty, max_patients):
        self.name = name
        self.specialty = specialty
        self.max_patients = max_patients

    # string representation of the object
    def __repr__(self):
        return f'{self.id} {self.name} {self.specialty} {self.max_patients}'
    
# Appointment table
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patientName = db.Column(db.String(100), nullable=False)
    regDate = db.Column(db.DateTime, default=datetime.utcnow)
    appointmentDate = db.Column(db.DateTime, nullable=False)
    doctorId = db.Column(db.Integer, nullable=False)

    # constructor
    def __init__(self, patientName, appointmentDate, doctorId):
        self.patientName = patientName
        self.appointmentDate = appointmentDate
        self.doctorId = doctorId

    # string representation of the object
    def __repr__(self):
        return f'{self.id} {self.patientName} {self.regDate} {self.appointmentDate} {self.doctorId}'
    
# this will create db file if already isn't there
with app.app_context():
    db.create_all()

def serializeDoctor(doctor):
    return dict(id=doctor.id, 
                name=doctor.name, 
                specialty=doctor.specialty, 
                max_patients=doctor.max_patients)

def serializeAppointment(appointment):
    return dict(id=appointment.id, 
                PatientName=appointment.patientName, 
                regDate=appointment.regDate, 
                appointmentDate=appointment.appointmentDate, 
                doctorId=appointment.doctorId)


@app.route('/')
def hello():
    return jsonify({'/api/doctors': 'List the all doctors',
                    '/api/doctors/1': 'A particular doctor\'s detail',
                    '/api/appointment': 'book the appointment'})

@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    doctor_list = []
    doctors = Doctors.query.all()
    for doctor in doctors:
        doctor_list.append(serializeDoctor(doctor))
    return jsonify(doctor_list), 200

@app.route('/api/doctors/<int:id>', methods=['GET'])
def get_doctor(id):
    doctor = Doctors.query.filter_by(id=id).first()
    if not doctor:
        return jsonify({"Message" : "Doctor is not found"}), 404
    doctor = serializeDoctor(doctor)
    return jsonify(doctor), 200

@app.route('/api/appointment', methods=['POST'])
def make_appointment():
    try:
        patientName = request.form['patientName']
    except KeyError:
        return jsonify({"Error": 'Patient name is required'}), 400
    try:
        doctorId = request.form['doctorId'] 
    except KeyError:
        return jsonify({"Error": 'Doctor ID is required'}), 400
    try:
        app_date = request.form['appointmentDate']
    except KeyError:
       return jsonify({"Error": 'Appointment date is required'}), 400

    appointmentDate = datetime.strptime(app_date, "%Y-%m-%d")
    
    doctor = Doctors.query.filter_by(id=doctorId).first()

    # to check the day is working day or not
    if (appointmentDate.strftime("%A") == 'Sunday'):
        return jsonify({'Message': 'Sunday is not working day'}), 400
    
    # to doctor is exists or not
    if not (doctor):
        return jsonify({'Message': 'Doctor is not found'}), 404
  
    # to doctor is free or not
    total_appoinment = Appointment.query.filter_by(appointmentDate=appointmentDate, doctorId=doctorId).count()
    if (total_appoinment >= doctor.max_patients):
        return jsonify({'Message': 'Doctor is fully booked for the evening'}), 400

    # to store appointments on the database
    appointment = Appointment(patientName=patientName, 
                              appointmentDate=appointmentDate, 
                              doctorId=doctorId)
    db.session.add(appointment)
    db.session.commit()
    
    # to retrieve the last stored appointment
    appointment_details = Appointment.query.order_by(Appointment.id.desc()).first()

    return jsonify(serializeAppointment(appointment_details)), 201
    

if __name__ == '__main__':
    app.run(debug=True)