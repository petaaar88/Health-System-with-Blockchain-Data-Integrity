import { useAuth } from "../contexts/AuthContext";
import CentralAuthorityDashboard from "../components/CentralAuthorityDashboard";
import UserDetails from "../components/UserDetails";
import HealthAuthorityDashboard from "../components/HealthAuthorityDashboard";
import PatientDashboard from "../components/PatientDashboard";
import DoctorDashboard from "../components/DoctorDashboard";

const Dashboard = () => {

  const { user } = useAuth();

  const renderContent = () => {
    switch (user.role) {
      case "patients":
        return <PatientDashboard/>;
      case "doctors":
        return <DoctorDashboard/>;
      case "central_authority":
        return <CentralAuthorityDashboard />;
      case "health_authorities":
        return <HealthAuthorityDashboard/>;
      default:
        return null;
    }
  };

  return (
    <div className="bg-blue-700 min-h-screen ">
      <UserDetails />
      <div className="p-6">{renderContent()}</div>
    </div>
  );
};

export default Dashboard;
