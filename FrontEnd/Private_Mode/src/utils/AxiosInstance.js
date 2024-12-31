import axios from "axios"

const YomacApi = axios.create({
    baseURL: `${process.env.REACT_APP_BASE_URL}/api/auth/`,
})

// function GetNumber() {
//     return 5;
// }

YomacApi.interceptors.request.use(
    (request) => {
      console.log(request);
      return request;
    }
)

export default YomacApi;