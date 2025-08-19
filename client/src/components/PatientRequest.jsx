import { Button } from "@mui/material";
import { useAuth } from "../contexts/AuthContext";
import { useState } from "react";

const PatientRequest = ({ request }) => {
  const { token } = useAuth();
  const [visible, setVisible] = useState(true);
  const handleDecline = () => {
    const declineDeclineRequest = async () => {
      try {
        const response = await fetch(
          import.meta.env.VITE_API_URL + `/api/requests/${request._id}`,
          {
            method: "DELETE",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          }
        );

        if (response.ok) setVisible(false);
      } catch (err) {
        console.error("Declining request:", err);
      }
    };

    declineDeclineRequest();
  };
  const handleAccept = () => {
    const acceptRequest = async () => {
      try {
        let key = null;
        const key_response = await fetch(
          import.meta.env.VITE_API_URL +
            `/api/health-records/secret_key/${request.health_record_id}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          }
        );

        const key_response_data = await key_response.json();

        key = key_response_data


        const response = await fetch(
          import.meta.env.VITE_API_URL + `/api/requests/${request._id}`,
          {
            method: "PATCH",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify(key),
          }
        );

        const reponse_data = await response.json();
        
        if (response.ok) setVisible(false);
      } catch (err) {
        console.error("Accepting request:", err);
      }
    };

    acceptRequest();
  };
  return (
    visible && (
      <div className="mb-4 bg-white w-160 p-5 rounded-md shadow-sm">
        <p className="text-xl">
          <span className="font-bold">{request.health_authority_name}</span>{" "}
          requesting access to your health record with ID:{" "}
          <span className="font-light italic">{request.health_record_id}</span>
        </p>
        <div className="flex gap-x-5 mt-4">
          <Button variant="contained" color="primary" onClick={handleAccept}>
            Accept
          </Button>
          <Button variant="contained" color="error" onClick={handleDecline}>
            Decline
          </Button>
        </div>
      </div>
    )
  );
};

export default PatientRequest;
