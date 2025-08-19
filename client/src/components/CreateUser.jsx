import { useState } from "react";
import { Button, Alert, CircularProgress } from "@mui/material";
import { formatStringToPascalCase } from "../utils/utils";
import { useAuth } from "../contexts/AuthContext";

const CreateUser = ({ title, fields, api }) => {
  const [formData, setFormData] = useState(() => {
    const initial = fields.reduce((acc, field) => {
      acc[formatStringToPascalCase(field)] = ""; 
      return acc;
    }, {});

    return { ...initial };
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const { token } = useAuth();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    
    if (error) setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setLoading(true);
    setError("");
    
    try {
      

      const response = await fetch(api, {
        method: "post",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body:JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (response.ok) 
        setSuccess(data.message)
      else{
        if(response.status == "500")
            setError("Internal Error");
        else
            setError(data.error);
      } 
      
    } catch (err) {
      setError("Error. Try again.");
      console.error("Adding user:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
        {error && (
        <Alert severity="error" className="mb-4 w-120" onClose={() => setError("")}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" className="mb-4 w-120" onClose={() => setSuccess("")}>
          {success}
        </Alert>
      )}
      <h2 className="text-white text-2xl mb-8">Add {title}</h2>
      <form onSubmit={handleSubmit} method="post" className="w-120">
        {fields.map((field) => (
          <div className="mb-5" key={formatStringToPascalCase(field)}>
            <input
              type={field.toLowerCase().includes("date") ? "date" : "text"}
              name={formatStringToPascalCase(field)}
              placeholder={field}
              value={formData[formatStringToPascalCase(field)]}
              onChange={handleInputChange}
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
            {loading ? `Adding ${title}...` : `Add ${title}`}
          </Button>
        </div>
      </form>
      
    </div>
  );
};

export default CreateUser;
