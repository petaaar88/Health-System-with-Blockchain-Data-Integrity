import CreateUser from "./CreateUser"

const CentralAuthorityDashboard = () => {
  return (
    <div className="flex justify-between">
        <CreateUser title={"Health Authority"} fields={["Name","Type","Password","Address","Phone"]} api={import.meta.env.VITE_API_URL + '/api/health-authority'}/>
        <CreateUser title={"Patient"} fields={["First Name","Last Name", "Password","Personal ID", "Date of Birth", "Gender","Address", "Phone", "Citizenship"]} api={import.meta.env.VITE_API_URL + '/api/patients'}/>
    </div>

  )
}

export default CentralAuthorityDashboard