import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
import uuid
import json

from flask import Flask, request, jsonify
from pymongo import MongoClient
from entities.patient import Patient
from entities.health_authority import HealthAuthority
from entities.doctor import Doctor
from util.util import generate_secret_key_b64, convert_secret_key_to_bytes, encrypt, decrypt

app = Flask(__name__)

# Povezivanje na lokalnu MongoDB bazu
client = MongoClient("mongodb://localhost:27017/")
db = client["cs203_project-health_system"]  # baza


@app.route("/api/patients", methods=["POST"])
def add_patient():

    collection = db["patients"]   

    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ["first_name", "last_name", "personal_id", "date_of_birth", 
                          "gender", "address", "phone", "citizenship"]
        
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        if collection.find_one({"personal_id": data["personal_id"]}):
            return jsonify({"error": "Patient with this personal_id already exists!"}), 400

        new_patient = Patient(
            first_name=data["first_name"],
            last_name=data["last_name"],
            personal_id=data["personal_id"],
            date_of_birth=data["date_of_birth"],
            gender=data["gender"],
            address=data["address"],
            phone=data["phone"],
            citizenship=data["citizenship"]
        )

        result = collection.insert_one(new_patient.to_dict())
        
        if result.inserted_id:
            return jsonify({"message": "Patient successfully added", "id": str(result.inserted_id)}), 201
        else:
            return jsonify({"error": "Failed to insert patient"}), 500

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route("/api/patients/<string:patient_id>", methods=["GET"])
def get_patient(patient_id):
    collection = db["patients"]
    patient_dict = collection.find_one({"_id": patient_id})
    return jsonify(patient_dict), 201

@app.route("/api/health-authority", methods=["POST"])
def add_health_authority():
    collection = db["health_authorities"]
    data = request.json
    

    # Kreiraj HealthAuthority objekat
    ha = HealthAuthority(
        name=data.get("name"),
        type=data.get("type"),
        address=data.get("address"),
        phone=data.get("phone")
    )

    # Ubaci u bazu kao dict
    collection.insert_one(ha.to_dict())

    return jsonify({"message": "HealthAuthority successfully added", "id": ha._id}), 201

@app.route("/api/doctors", methods = ["POST"])
def add_doctor():

    #TODO iz jwt-a uzmi id health authoritija
    collection = db["doctors"]
    data = request.json

    # Kreiraj HealthAuthority objekat
    new_doctor = Doctor(
        first_name=data["first_name"],
        last_name=data["last_name"],
        health_authority_id=data.get("health_authority_id")
    )

    health_authorities_collection = db["health_authorities"]

    result = health_authorities_collection.update_one(
        {"_id": new_doctor.health_authority_id},
        {"$push": {"doctors": new_doctor._id}}
    )

    if result.matched_count == 0:
        return jsonify({"error": "HealthAuthority sa tim ID-jem nije pronađen"}), 404


    # Ubaci u bazu kao dict
    collection.insert_one(new_doctor.to_dict())

    return jsonify({"message": "Doctor successfully added", "id": new_doctor._id}), 201


@app.route("/api/health-records", methods=["POST"])
def add_health_record():
    health_records_collection = db["health_records"]
    data = request.json

    new_id = uuid.uuid4().hex
    data["_id"] = new_id

    secret_key = generate_secret_key_b64()

    json_data = json.dumps(data)  # Pretvori dict u string pre enkripcije
    encrypted_data = encrypt(json_data, convert_secret_key_to_bytes(secret_key))

    health_record = {
        "_id": new_id,
        "health_authority_id": data["health_authority_id"],
        "data": encrypted_data,
        "key":secret_key,
        "patient_id": data["patient_id"]
    }

    health_records_collection.insert_one(health_record)

    return jsonify({"message": "Health record successfully added", "id": new_id}), 201

@app.route("/api/health-records/<string:hr_id>", methods=["GET"])
def get_health_record(hr_id):
    health_records_collection = db["health_records"]
    health_dict = health_records_collection.find_one({"_id": hr_id})

    print(decrypt(health_dict["data"],convert_secret_key_to_bytes(health_dict["key"])))
    return jsonify(json.loads(decrypt(health_dict["data"],convert_secret_key_to_bytes(health_dict["key"])))), 201

if __name__ == "__main__":
    app.run(debug=True)