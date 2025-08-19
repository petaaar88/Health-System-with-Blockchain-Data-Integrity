import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import PatientRequest from "./PatientRequest";

const PatientRequests = () => {
  const [requests, setRequest] = useState(null);
  const { token } = useAuth();

  useEffect(() => {
    fetch(import.meta.env.VITE_API_URL + "/api/requests/patient", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((response) => {
        return response.json();
      })
      .then((data) => {
        setRequest(data);
      })
      .catch((err) => console.log(err));
  }, []);
  return (
    <div>
      <h2 className="text-white text-2xl mb-8">Requests</h2>
      {requests?.length == 0 ? (
        <p className="text-white">No Requests</p>
      ) : (
        requests?.map((request) => (
          <PatientRequest key={request._id} request={request} />
        ))
      )}
    </div>
  );
};

export default PatientRequests;
