import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")
import uuid
import json
from datetime import datetime
import websockets
import asyncio

from flask import Flask, request, jsonify
from pymongo import MongoClient
from entities.patient import Patient
from entities.health_authority import HealthAuthority
from blockchain.backend.core.transaction import Transaction
from blockchain.backend.core.transaction_body import TransactionBody
from blockchain.backend.util import util
from entities.doctor import Doctor
from util.util import generate_secret_key_b64, convert_secret_key_to_bytes, encrypt, decrypt

async def send_to_blockchain_and_wait_response(message, timeout=60):
    """
    Šalje poruku blockchain peer-u i čeka odgovor
    """
    try:
        # Konektuj se na blockchain peer (pretpostavljam port 8765)
        uri = "ws://localhost:8765"
        
        async with websockets.connect(uri) as websocket:
            # Pošalji poruku
            await websocket.send(json.dumps(message))
            print(f"📤 Sent to blockchain: {message['type']}")
            
            # Čekaj odgovor sa timeout-om
            response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            response_data = json.loads(response)
            
            print(f"📥 Received from blockchain: {response_data}")
            return True, response_data
            
    except asyncio.TimeoutError:
        return False, {"error": "Blockchain response timeout"}
    except Exception as e:
        return False, {"error": f"Blockchain connection error: {str(e)}"}

def send_to_blockchain_per_request(message):
    """
    Wrapper funkcija za korišćenje u Flask route-u
    """
    try:
        # Pokreni async funkciju iz sync konteksta
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success, response = loop.run_until_complete(
                send_to_blockchain_and_wait_response(message)
            )
            return success, response
        finally:
            loop.close()
    except Exception as e:
        return False, {"error": f"Failed to communicate with blockchain: {str(e)}"}

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
            # Slanje na blockchain - nova konekcija za ovaj request
            new_account = {
                "public_key": new_patient.public_key,
                "private_key": new_patient.private_key
            }

            message = {
                "type": "CLIENT_ADD_ACCOUNT",
                "data": new_account
            }

            blockchain_success, blockchain_response = send_to_blockchain_per_request(message)
            
            response_data = {
                "message": "Patient successfully added", 
                "id": str(result.inserted_id)
            }
            
            response =  blockchain_response

            if blockchain_success:
                response_data["blockchain_response"] = response["message"]
            else:
                response_data["blockchain_error"] = response
            
            return jsonify(response_data), 201
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
    
    try:
        # Kreiraj HealthAuthority objekat
        new_health_authority = HealthAuthority(
            name=data.get("name"),
            type=data.get("type"),
            address=data.get("address"),
            phone=data.get("phone")
        )

        # Ubaci u bazu kao dict
        result = collection.insert_one(new_health_authority.to_dict())
        if result.inserted_id:
            # Slanje na blockchain - nova konekcija za ovaj request
            new_account = {
                "public_key": new_health_authority.public_key,
                "private_key": new_health_authority.private_key
            }

            message = {
                "type": "CLIENT_ADD_ACCOUNT",
                "data": new_account
            }

            blockchain_success, blockchain_response = send_to_blockchain_per_request(message)
            
            response_data = {
                "message": "Health Authority successfully added", 
                "id": str(result.inserted_id)
            }
            
            response =  blockchain_response
            if blockchain_success:
                response_data["blockchain_response"] = response["message"]
            else:
                response_data["blockchain_error"] = response
            
            return jsonify(response_data), 201
        else:
            return jsonify({"error": "Failed to insert patient"}), 500

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


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
    patients_collection = db["patients"]
    health_authorities_collection = db["health_authorities"]

    data = request.json

    new_id = uuid.uuid4().hex
    data["_id"] = new_id

    secret_key = generate_secret_key_b64()

    health_record_string_data = json.dumps(data)
    encrypted_data = encrypt(health_record_string_data, convert_secret_key_to_bytes(secret_key))

    health_record = {
        "_id": new_id,
        "health_authority_id": data["health_authority_id"],
        "data": encrypted_data,
        "key": secret_key,
        "patient_id": data["patient_id"]
    }

    
    patient_dict = patients_collection.find_one({"_id": data["patient_id"]})
    if not patient_dict:
        return {"error": "Patient not found"}, 404
    
    health_authority_dict = health_authorities_collection.find_one({"_id": data["health_authority_id"]})
    if not health_authority_dict:
        return {"error": "Health authority not found"}, 404

    patient = Patient.from_dict(patient_dict)
    health_authority = HealthAuthority.from_dict(health_authority_dict)

    # Kreiraj transakciju
    transaction_body = TransactionBody(
        health_authority.public_key, 
        patient.public_key, 
        new_id,
        datetime.now().isoformat(),
        util.hash256(data)
    )
    transaction = Transaction(transaction_body)
    health_authority.sign(transaction)
    
    try:
        # Pošalji na blockchain i čekaj odgovor
        message = {
            "type": "CLIENT_ADD_TRANSACTION",
            "data": {
                "transaction": transaction.to_dict(),
                "data_for_validation": data
            }
        }

        blockchain_success, blockchain_response = send_to_blockchain_per_request(message)
        
        if blockchain_success:
            # Proveri tip odgovora od blockchain-a
            response_type = blockchain_response.get("type")
            
            if response_type == "TRANSACTION_RESULT":
                transaction_success = blockchain_response.get("success", False)
                blockchain_message = blockchain_response.get("message", "")
                transaction_id = blockchain_response.get("transaction_id")
                
                if transaction_success:
                    # Transakcija je uspešno dodana u blockchain
                    result = health_records_collection.insert_one(health_record)
                    
                    return jsonify({
                        "message": "Health record successfully added and confirmed on blockchain",
                        "id": new_id,
                        "transaction_id": transaction_id,
                        "blockchain_status": blockchain_message,
                        "database_id": str(result.inserted_id)
                    }), 201
                    
                else:
                    # Transakcija je odbijena
                    return jsonify({
                        "error": "Transaction rejected by blockchain network",
                        "blockchain_message": blockchain_message,
                        "transaction_id": transaction_id
                    }), 400
            else:
                # Nepoznat tip odgovora
                return jsonify({
                    "error": "Unexpected blockchain response",
                    "response": blockchain_response
                }), 500
        else:
            # Greška u komunikaciji sa blockchain-om
            return jsonify({
                "error": "Failed to communicate with blockchain",
                "blockchain_error": blockchain_response.get("error", "Unknown error")
            }), 500

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route("/api/health-records/<string:hr_id>", methods=["GET"])
def get_health_record(hr_id):
    health_records_collection = db["health_records"]
    health_dict = health_records_collection.find_one({"_id": hr_id})

    print(decrypt(health_dict["data"],convert_secret_key_to_bytes(health_dict["key"])))
    return jsonify(json.loads(decrypt(health_dict["data"],convert_secret_key_to_bytes(health_dict["key"])))), 201


@app.route("/api/health-records/verify/<string:hr_id>", methods=["GET"])
def verify_health_record(hr_id):
    health_records_collection = db["health_records"]
    data = request.json

    health_record_dict = health_records_collection.find_one({"_id": hr_id})

    if not health_record_dict:
        return {"error": "Health record not found"}, 404
      
    if health_record_dict["key"] != data["secret_key"]:
        return {"error": "Key is invalid!"}, 403

    try:

        health_record_for_verification = json.loads(decrypt(health_record_dict["data"],convert_secret_key_to_bytes(health_record_dict["key"])))
        message = {
                "type": "CLIENT_VERIFY_TRANSACTION",
                "data": {
                    "health_record_id":hr_id,
                    "health_record" : health_record_for_verification
                }
        }

        blockchain_success, blockchain_response = send_to_blockchain_per_request(message)
        response_data = {}
        response =  blockchain_response

        if blockchain_success:
            response_data["blockchain_response"] = response["message"]
        else:
            response_data["blockchain_error"] = response
                
        return jsonify(response_data), 200
       

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)