
const DoctorDetails = ({data}) => {
  return (
    <>
      <h1 className="text-2xl font-medium mb-5">Doctor Details</h1>
      <p className="text-lg"><span className="font-bold">First Name:</span> {data?.first_name}</p>
      <p className="text-lg"><span className="font-bold">Last Name:</span> {data?.last_name}</p>
      <p className="text-lg"><span className="font-bold">Health Authority Name:</span> {data?.health_authority_name}</p>
      
    </>
  )
}

export default DoctorDetails