export const formatDateToString = (date) => {
  if (!date) return null;

  let temp = date.split("-");

  let formattedString = `${temp[0]}. ${temp[1]}. ${temp[2]}.`;

  return formattedString;
};

export const formatStringToPascalCase = (input) => {
  input = input.toLowerCase();

  return input.replaceAll(" ", "_");
};

export const capitalize = (word) => {
  if (!word) return "";
  return word.charAt(0).toUpperCase() + word.slice(1);
};

export const capitalizeWords = (sentence) => {
  return sentence
    .split(/[ _]/)
    .map((word) => capitalize(word))
    .join(" ");
};

export const formatDateWithTimeToString = (isoTime) => {
  const cleanIso = isoTime.slice(0, 23) + "Z";

  const date = new Date(cleanIso);

  const formatted =
    date.getDate().toString().padStart(2, "0") +
    "." +
    (date.getMonth() + 1).toString().padStart(2, "0") +
    "." +
    date.getFullYear() +
    ". " +
    date.getHours().toString().padStart(2, "0") +
    ":" +
    date.getMinutes().toString().padStart(2, "0") +
    ":" +
    date.getSeconds().toString().padStart(2, "0");

  return formatted;
};
