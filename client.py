import asyncio
import websockets
import json
from backend.entities.patient import Patient
from backend.entities.health_authority import HealthAuthority
from blockchain.backend.core.transaction import Transaction
from blockchain.backend.core.transaction_body import TransactionBody
from blockchain.backend.core.chain import Chain
from blockchain.backend.core.block import Block
from datetime import datetime
from blockchain.backend.util import util

patient = Patient("Petar", "Djorjdevic")
hospital = HealthAuthority("Dom Zdravlja","asdfasd","asdasfd",'asdfasd')
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

transaction_dict = transaction.to_dict()

async def ws_client():
    uri = "ws://localhost:8765"  # promeni na svoj WS server

    async with websockets.connect(uri) as websocket:
        print(f"Povezan na {uri}")

        # Primer slanja poruke serveru
        await websocket.send(json.dumps({
                                        "type": "CLIENT_ADD_TRANSACTION",
                                         "data":{
                                             "transaction":transaction_dict,
                                             "data_for_validation":medical_record
                                          }
                                        }))

        # Čekaj odgovor od servera
        response = await websocket.recv()
        print(f"Odgovor servera: {response}")

        # Možeš slati i primati poruke u petlji, evo primera:
        for i in range(3):
            poruka = f"Poruka broj {i+1}"
            print(f"Šaljem: {poruka}")
            await websocket.send(poruka)

            odgovor = await websocket.recv()
            print(f"Primio: {odgovor}")

asyncio.run(ws_client())
