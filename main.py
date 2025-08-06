from blockchain.backend.util import util

from backend.patient import Patient
from backend.hospital_entity import HospitalEntity
from blockchain.backend.core.transaction import Transaction
from blockchain.backend.core.transaction_body import TransactionBody
from blockchain.backend.core.chain import Chain
from datetime import datetime


patient = Patient("Petar", "Djorjdevic")
hospital = HospitalEntity("Dom Zdravlja")
medical_record = {
    "id":"asdfadsf00",
    "patient_id": "987654321",
    "patient_name": "Petar Đorđević",
    "lab_test": {
      "date": "2025-08-01",
      "results": {
        "CRP": "12 mg/L",
        "Leukociti": "8.1 x10^9/L"
      }
    },
    "diagnosis": "Blaga bakterijska infekcija",
    "doctor_name": "Dr. Jovana Petrović",
    "doctor_id":"asdfasdf",
    "hospital_name": "Dom zdravlja Novi Beograd",
    "hospital_id":"asdfasdfasfasdf"
  }

transaction_body = TransactionBody(hospital.public_key,patient.public_key, 'https:://nseto',datetime.now().isoformat())
transaction = Transaction(transaction_body)

hospital.sign(transaction)

chain = Chain('asdfas')
chain.add_block(transaction,medical_record)

print(chain)




