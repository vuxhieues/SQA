import { Route, Routes, useLocation } from "react-router-dom"
import PrivateCoursesSideBar from "../components/PrivateCoursesSideBar/PrivateCoursesSideBar"
import { useDispatch, useSelector } from "react-redux"
import { setAsideBarStatus, setCurrentCourseId } from "../RTK/Slices/ResponsiveComponents";
import { useEffect } from "react";
import { login } from "../RTK/Slices/AuthorizationSlice";
import PrivateCourse from "../components/PrivateCourse/PrivateCourse";

function BasePrivateCourse() {
    
    const location = useLocation();
    const { token } = useSelector(state => state.Authorization);
    const queryParams = new URLSearchParams(location.search);
    useEffect(() => {
      console.log(queryParams.get('user_id'));
      if(queryParams.get('user_id') != null) {
        console.log("DAMNAMSB");
        
          dispatch(login({
              user_id: queryParams.get('user_id'),
              token: queryParams.get('token'),
              role: queryParams.get('role'),
          }));
          dispatch(setCurrentCourseId(queryParams.get('curr_course_id')));
          window.history.replaceState({}, '', location.pathname);
      }
  }, [location, queryParams])

    const dispatch = useDispatch();
    const { currentCourseId, AsideBarHidden } = useSelector(state => state.ResponsiveComponents);
    useEffect(() => {
        console.log(AsideBarHidden);
    }, [AsideBarHidden])
    return (
        <section className="bg-[#dcdfe3] relative w-full h-[100vh] overflow-y-hidden pr-1 flex">
            <PrivateCoursesSideBar />
            <section className="course-data relative pl-1 lg:w-[80%] md:w-[85%] flex-grow flex flex-col py-1">
                <div onClick={() => {
                    dispatch(setAsideBarStatus(true));
                }} className="aside-menu-icon absolute p-1 top-[1%] left-[2%] cursor-pointer md:hidden">
                    <i class="fa-solid fa-bars scale-125"></i>
                </div>
                {
                    currentCourseId == 0 ?
                    <div className="flex justify-center items-center flex-col flex-grow">
                        <h2 className="md:text-[2rem] lg:text-[3rem] font-bold select-none">YOMAC PRIVATE MODE</h2>
                        <p className="md:text-[1.5rem] lg:text-[2rem] select-none">Select a course to view</p>
                    </div>
                    :
                    <PrivateCourse />
                }
            </section>
        </section>
    )
}

export default BasePrivateCourse