import { useState } from "react";
import HealthRecordForm from "./HealthRecordForm";
import { Button } from "@mui/material";
import SearchPatients from "./SearchPatients";

const DoctorDashboard = () => {
  const [page, setPage] = useState("Add Health Record");
  const handleAddHealthRecord = () => {
    setPage("Add Health Record");
  };
  const handleSearchPatinents = () => {
    setPage("Search Patients");
  };
  return (
    <div>
      <div className="flex justify-center gap-x-10 mb-5">
        <Button
          onClick={handleAddHealthRecord}
          variant="contained"
          sx={{
            backgroundColor: "white",
            fontWeight: "600",
            color: "blue",
            "&:hover": { backgroundColor: "#90D5FF" },
          }}
        >
          Add Health Record
        </Button>
        <Button
          onClick={handleSearchPatinents}
          variant="contained"
          sx={{
            backgroundColor: "white",
            fontWeight: "600",
            color: "blue",
            "&:hover": { backgroundColor: "#90D5FF" },
          }}
        >
          Search Patients
        </Button>
      </div>
      {page === "Add Health Record" ? <HealthRecordForm /> : <SearchPatients/>}
    </div>
  );
};

export default DoctorDashboard;
