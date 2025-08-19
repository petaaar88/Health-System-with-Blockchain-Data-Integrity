import { Alert, Button, CircularProgress } from "@mui/material";
import DetailRenderer from "./DetailRenderer";
import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import {formatDateToString} from "../utils/utils.js"

const HealthRecord = ({ data, secretKey }) => {
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const { token } = useAuth();

  const handleClick = () => {
    setLoading(true);
    setError("");

    const verifyHealthRecord = async () => {
      try {
        const response = await fetch(
          import.meta.env.VITE_API_URL +
            `/api/health-records/verify/${data._id}`,
          {
            method: "post",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ secret_key: secretKey }),
          }
        );

        const responseData = await response.json();
      

        if (response.ok) {
            if (responseData.blockchain_response.toLowerCase().includes('invalid'))
                setError(responseData.blockchain_response);
            else
                setSuccess(responseData.blockchain_response);
        }
        else {
          if (response.status == "500") setError("Internal Error");
          else setError(responseData.error);
        }
      } catch (err) {
        setError("Error. Try again.");
        console.error("Verifying health record:", err);
      } finally {
        setLoading(false);
      }
    };

    verifyHealthRecord();
  };

  const excludeFromDetails = [
    "_id",
    "doctor_id",
    "health_authority_id",
    "health_authority_name",
    "doctor_first_name",
    "doctor_last_name",
    "patient_id",
    "patient_first_name",
    "patient_last_name",
    "date"
  ];

  const detailsData = Object.keys(data)
    .filter((key) => !excludeFromDetails.includes(key))
    .reduce((obj, key) => {
      obj[key] = data[key];
      return obj;
    }, {});

  return (
    <div className="mb-4 bg-white w-160 p-5 rounded-md shadow-sm">
      <div className="mb-4">
        <p >
          <span className="font-bold">ID:</span> {data._id}
        </p>
        <p >
          <span className="font-bold">Date:</span> {formatDateToString(data.date)}
        </p>
        <p >
          <span className="font-bold">Health Authority Name:</span>{" "}
          {data.health_authority_name}
        </p>
        <p >
          <span className="font-bold">Doctor:</span> Dr.{" "}
          {data.doctor_first_name} {data.doctor_last_name}
        </p>
      </div>

      <hr className="py-2" />

      <div className="mb-4">
        <p className="text-xl font-bold mb-4">Details</p>

        {Object.keys(detailsData).length > 0 ? (
          <DetailRenderer
            data={detailsData}
            excludeFields={excludeFromDetails}
          />
        ) : (
          <p className="text-gray-500 italic">
            No additional details available
          </p>
        )}
      </div>

      <hr className="mb-4" />

      <Button
        variant="contained"
        color="info"
        disabled={loading}
        startIcon={loading && <CircularProgress size={20} color="inherit" />}
        onClick={handleClick}
      >
        {loading ? "Verifying..." : "Verify Health Record"}
      </Button>
      {error && (
        <Alert severity="error" className="mt-4 " onClose={() => setError("")}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert
          severity="success"
          className="mt-4 "
          onClose={() => setSuccess("")}
        >
          {success}
        </Alert>
      )}
    </div>
  );
};

export default HealthRecord;
