import "./App.css";
import { Routes, Route, useLocation, useSearchParams } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import BasePrivateCourse from "./pages/BasePrivateCourse.jsx";
import { useEffect } from "react";
import LiveStream from "./pages/LiveStream.jsx";

function App() {
  const { token } = useSelector(state => state.Authorization);

  useEffect(() => {
    console.log(token);
  }, [token])
  return (
    <div>
      <Routes>
        <Route path="/private" element={<BasePrivateCourse />} />
        <Route path="/live" element={<LiveStream />} />
      </Routes>
    </div>
  );
}

export default App;
