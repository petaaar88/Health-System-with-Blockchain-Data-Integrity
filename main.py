from blockchain.backend.util import util

from backend.entities.patient import Patient
from backend.entities.health_authority import HealthAuthority
from blockchain.backend.core.transaction import Transaction
from blockchain.backend.core.transaction_body import TransactionBody
from blockchain.backend.core.chain import Chain
from blockchain.backend.core.block import Block
from datetime import datetime


patient = Patient("Petar", "Djorjdevic")
hospital = HealthAuthority("Dom Zdravlja")
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

transaction_body = TransactionBody(hospital.public_key,patient.public_key, 'https:://nseto',datetime.now().isoformat(),util.hash256(medical_record))
transaction = Transaction(transaction_body)
hospital.sign(transaction)


chain = Chain('asdfas',20,5)

if chain.add_transaction(transaction,medical_record) is True:
  new_block = chain.create_new_block()
  
  if Block.is_valid(new_block,chain) is True:
    chain.add_to_block_to_chain(new_block)
   

Chain.is_valid(chain)
print(chain)




