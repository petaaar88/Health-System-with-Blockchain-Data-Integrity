
const HealthAuthorityDetails = ({data}) => {
  return (
    <>
      <h1 className="text-2xl font-medium mb-5">Health Authority Details</h1>
      <p className="text-lg"><span className="font-bold">Name:</span> {data?.name}</p>
      <p className="text-lg"><span className="font-bold">Type:</span> {data?.type}</p>
      <p className="text-lg"><span className="font-bold">Address:</span> {data?.address}</p>
      <p className="text-lg"><span className="font-bold">Phone:</span> {data?.phone}</p>
    </>
  )
}

export default HealthAuthorityDetails