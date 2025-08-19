
const CentralAuthorityDetails = ({data}) => {
  return (
    <>
      <h1 className="text-2xl font-medium mb-5">Central Authority Details</h1>
      <p className="text-lg"><span className="font-bold">Name:</span> {data?.name}</p>
    </>
  )
}

export default CentralAuthorityDetails