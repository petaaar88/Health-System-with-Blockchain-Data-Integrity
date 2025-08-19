import CreateUser from "./CreateUser"

const HealthAuthorityDashboard = () => {
  return (
    <div >
        <CreateUser title={"Doctor"} fields={["First Name","Last Name","Password"]} api={import.meta.env.VITE_API_URL + '/api/doctors'}/>
    </div>
  )
}

export default HealthAuthorityDashboard