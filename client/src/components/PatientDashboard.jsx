import PatientHealthRecords from "./PatientHealthRecords";
import PatientRequests from "./PatientRequests";

const PatientDashboard = () => {
  

  return (
    <div className="flex justify-between">
      <PatientHealthRecords/>
      <PatientRequests/>
    </div>
  );
};

export default PatientDashboard;
