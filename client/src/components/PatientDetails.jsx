import {formatDateToString} from "../utils/utils.js"

const PatientDetails = ({data}) => {
  
  return (
    <>
      <h1 className="text-2xl font-medium mb-5">Patient Details</h1>
      <p className="text-lg"><span className="font-bold">First Name:</span> {data?.first_name}</p>
      <p className="text-lg"><span className="font-bold">Last Name:</span> {data?.last_name}</p>
      <p className="text-lg"><span className="font-bold">Personal ID:</span> {data?.personal_id}</p>
      <p className="text-lg"><span className="font-bold">Date of Birth:</span> {formatDateToString(data?.date_of_birth)}</p>
      <p className="text-lg"><span className="font-bold">Gender:</span> {data?.gender}</p>
      <p className="text-lg"><span className="font-bold">Address:</span> {data?.address}</p>
      <p className="text-lg"><span className="font-bold">Phone:</span> {data?.phone}</p>
      <p className="text-lg"><span className="font-bold">Citizenship:</span> {data?.citizenship}</p>
    </>
  );
};

export default PatientDetails;
