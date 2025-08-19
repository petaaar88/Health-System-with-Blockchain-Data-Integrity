import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import CentralAuthorityDetails from "./CentralAuthorityDetails";
import DoctorDetails from "./DoctorDetails";
import HealthAuthorityDetails from "./HealthAuthorityDetails";
import PatientDetails from "./PatientDetails";
import { Button } from "@mui/material";

const UserDetails = () => {
  const [data, setData] = useState(null);
  const { user, token,logout } = useAuth();
  

  useEffect(() => {
    const loadData = async () => {
      let type = user.role;

      if (user.role == "central_authority") type = "central-authority";
      else if (user.role == "health_authorities") type = "health_authority";

      try {
        const response = await fetch(
          import.meta.env.VITE_API_URL + `/api/${type}/${user.id}`,
          {
            method: "GET",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          }
        );

        if (response.ok) {
          const data = await response.json();

          setData(data);
        }
      } catch (error) {
        console.error("Token validation error:", error);
      }
    };

    loadData();
  }, []);

  const renderContent = () => {
    switch (user.role) {
      case "patients":
        return <PatientDetails data={data} />;
      case "doctors":
        return <DoctorDetails data={data} />;
      case "central_authority":
        return <CentralAuthorityDetails data={data} />;
      case "health_authorities":
        return <HealthAuthorityDetails data={data} />;
      default:
        return null;
    }
  };

  return <div className="flex items-center justify-between p-6 shadow-lg bg-white "><div>{renderContent()}</div><Button onClick={logout} color="error" variant="contained">Logout</Button></div>;
};

export default UserDetails;
