import HealthRecord from "./HealthRecord";
import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";

const PatientHealthRecords = () => {
  const [healthRecords, setHealthRecords] = useState(null);
  const { token } = useAuth();

  useEffect(() => {
    fetch(import.meta.env.VITE_API_URL + "/api/health-records", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        setHealthRecords(data);
      })
      .catch((err) => console.log(err));
  }, []);
  return (
    <div>
      <h2 className="text-white text-2xl mb-8">Health Records</h2>
      {healthRecords?.health_records?.length == 0 ? (
        <p className="text-white">No Health Records</p>
      ) : (
        healthRecords?.health_records?.map((healthRecord) => (
          <HealthRecord
            key={healthRecord.health_record._id}
            data={healthRecord.health_record}
            secretKey={healthRecord.key}
          />
        ))
      )}
    </div>
  );
};

export default PatientHealthRecords;
