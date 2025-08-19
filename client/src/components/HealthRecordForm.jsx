import { Alert, Button, CircularProgress } from "@mui/material";
import { useState } from "react";
import { capitalizeWords, formatStringToPascalCase } from "../utils/utils";
import { useAuth } from "../contexts/AuthContext";

const HealthRecordForm = () => {
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const { token } = useAuth();
  const [fields, setFileds] = useState({
    patient_id: "",
    diagnosis: ""
  });
  const [newField, setNewField] = useState("");
  const handleAddNewField = () => {
    if (newField) {
      fields[formatStringToPascalCase(newField)] = "";
      setFileds(fields);
      setNewField("");
    }
  };

  const handleNewFieldOnChange = (e) => setNewField(e.target.value);
  const handleFiledsOnChange = (e) => {
    const { name, value } = e.target;
    setFileds((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleOnSubmit = async (e) => {
    e.preventDefault();

    setLoading(true);
    setError("");
    
    try {
      const response = await fetch(
        import.meta.env.VITE_API_URL + "/api/health-records",
        {
          method: "post",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(fields),
        }
      );

      const data = await response.json();

      if (response.ok) setSuccess(data.message);
      else {
        if (response.status == "500") setError("Internal Error");
        else setError(data.error);
      }
    } catch (err) {
      setError("Error. Try again.");
      console.error("Adding health record:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-130">
      <h2 className="text-white text-2xl mb-8">Add Health Record</h2>
      {error && (
        <Alert
          severity="error"
          className="mb-4 w-120"
          onClose={() => setError("")}
        >
          {error}
        </Alert>
      )}
      {success && (
        <Alert
          severity="success"
          className="mb-4 w-120"
          onClose={() => setSuccess("")}
        >
          {success}
        </Alert>
      )}
      <div className="flex items-center gap-x-8 mb-6">
        <input
          type="text"
          name="new_field"
          placeholder="New Field"
          onChange={handleNewFieldOnChange}
          value={newField}
          className="w-90 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white disabled:bg-blue-800 disabled:cursor-not-allowed disabled:text-gray-400"
        />
        <Button variant="contained" onClick={handleAddNewField}>
          Add Field
        </Button>
      </div>

      <hr style={{ color: "white" }} />
      <form method="post" className="mt-6" onSubmit={handleOnSubmit}>
        {Object.entries(fields).map(([key, value]) => (
          <div className="mb-5" key={key}>
            <input
              type="text"
              name={key}
              placeholder={capitalizeWords(key)}
              onChange={handleFiledsOnChange}
              value={value}
              disabled={loading}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white disabled:bg-blue-800 disabled:cursor-not-allowed disabled:text-gray-400"
              required
            />
          </div>
        ))}

        <div>
          <Button
            type="submit"
            variant="contained"
            size="large"
            className="w-full"
            sx={{
              backgroundColor: "white",
              fontWeight: "600",
              color: "blue",
              "&:hover": { backgroundColor: "#90D5FF" },
            }}
            disabled={loading}
            startIcon={
              loading && <CircularProgress size={20} color="inherit" />
            }
          >
            {loading ? `Adding Health Record...` : `Add Health Record`}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default HealthRecordForm;
