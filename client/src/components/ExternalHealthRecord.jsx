import { Button } from "@mui/material";
import { formatDateWithTimeToString } from "../utils/utils";
import { useAuth } from "../contexts/AuthContext";
import { useEffect, useState } from "react";
import HealthRecord from "./HealthRecord";

const ExternalHealthRecord = ({ data }) => {
  const { token } = useAuth();
  const [isRequestSent, setIsRequestSent] = useState(null);
  const [hideHealthRecord, setHideHealthRecord] = useState(true);
  const [healthRecordData, setHealthRecordData] = useState(null);

  const loadRequests = async () => {
    try {
      const response = await fetch(
        import.meta.env.VITE_API_URL + `/api/requests/doctors`,
        {
          method: "get",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      const reponse_data = await response.json();

      if (response.ok) {
        let request = reponse_data.find(
          (request) => request.health_record_id == data.health_record_id
        );
        if (request) setIsRequestSent(true);
        else setIsRequestSent(false);
      }
    } catch (err) {
      console.error("Adding health record:", err);
    }
  };
  useEffect(() => {
    if (!data.key) loadRequests();
  }, []);

  const handleSendRequest = async () => {
    try {
      const response = await fetch(
        import.meta.env.VITE_API_URL + `/api/requests`,
        {
          method: "post",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            health_record_id: data.health_record_id,
            patient_id: data.patient_id,
          }),
        }
      );

      if (response.ok) setIsRequestSent(true);
    } catch (err) {
      console.error("Adding health record:", err);
    }
  };

  const handleLoadHealthRecord = async () => {
    try {
      const response = await fetch(
        import.meta.env.VITE_API_URL +
          `/api/health-records/decrypt/${data.health_record_id}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ secret_key: data.key }),
        }
      );
      const reponse_data = await response.json();
      console.log(response);
      console.log(reponse_data);

      if (response.ok) {
        setHideHealthRecord(false);
        setHealthRecordData(reponse_data);
      }
    } catch (err) {
      console.error("Adding health record:", err);
    }
  };

  return hideHealthRecord ? (
    <div className="mb-4 bg-white w-160 p-5 rounded-md shadow-sm">
      <p>
        <span className="font-bold">Health Record ID:</span>{" "}
        {data.health_record_id}
      </p>
      <p>
        <span className="font-bold">Health Authority Creator:</span>{" "}
        {data.health_authority_name}
      </p>
      <p>
        <span className="font-bold">Added At Blockchain:</span>{" "}
        {formatDateWithTimeToString(data.added_at_blockchain)}
      </p>
      {data.key ? (
        <div className="mt-3">
          <Button
            variant="contained"
            color="success"
            onClick={handleLoadHealthRecord}
          >
            Load Health Record
          </Button>
        </div>
      ) : isRequestSent ? (
        <div className="mt-3">
          <Button disabled={true} variant="contained" color="success">
            Request Sent
          </Button>
        </div>
      ) : (
        <div className="mt-3">
          <Button variant="contained" color="info" onClick={handleSendRequest}>
            Send Request
          </Button>
        </div>
      )}
    </div>
  ) : (
    <HealthRecord data={healthRecordData.health_record} secretKey={healthRecordData.key}/>
  );
};

export default ExternalHealthRecord;
