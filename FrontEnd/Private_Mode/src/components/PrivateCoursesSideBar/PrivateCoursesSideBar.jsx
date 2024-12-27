import { useEffect, useRef, useState } from "react"
import TestImage from "../../assets/3mk.jpg"
import "./PrivateCoursesSideBar.css"
import gsap from "gsap"
import { useDispatch, useSelector } from "react-redux"
import { setAsideBarStatus, setCurrentCourseId } from "../../RTK/Slices/ResponsiveComponents"
import { useMediaQuery } from "react-responsive"
import { GetPrivateCourses } from "../../RTK/Slices/PrivateCourseSlice"

function PrivateCoursesSideBar() {
    const dispatch = useDispatch();
    const smallScreen = useRef(false);
    const { AsideBarHidden } = useSelector(state => state.ResponsiveComponents);  
    const [isCoursesOpen, setIsCoursesOpen] = useState(false);
    const { currentCourseId } = useSelector(state => state.ResponsiveComponents);
    const { privateCourses } = useSelector(state => state.PrivateCourse);
    const { token } = useSelector(state => state.Authorization);
    function OpenCoursesList() {
        console.log("OpenCoursesList");
        gsap.to("#arrow", {
            rotateZ: 90,
            duration: 0.2
        })
        const tl = gsap.timeline();
        tl.to("#courses-list", {
            gridTemplateRows: "1fr",
            duration: 0.3,
        })  
        tl.to("#courses-list > div > div", {
            translateX: "0",
            stagger: 0.1,
            duration: 0.4,
        })
        setIsCoursesOpen(true);
    }

    useEffect(() => {
        console.log(privateCourses);
    }, [privateCourses])
    useEffect(() => {
        dispatch(GetPrivateCourses());
    }, [token])
    
    function CloseCoursesList() {
        console.log("CloseCoursesList");
        
        gsap.to("#arrow", {
            rotateZ: 0,
            duration: 0.2
        })
        const tl = gsap.timeline();
        tl.to("#courses-list > div > div", {
            translateX: "-150%",
            duration: 0.7,
            stagger: -0.2
        })
        tl.to("#courses-list", {
            gridTemplateRows: "0fr",
            duration: 0.5,
            delay: -0.5
        })
        setIsCoursesOpen(false);
    }
        
    function HandleCoursesList() {
        if (isCoursesOpen) {
            CloseCoursesList();
        } else {
            OpenCoursesList();
        }
    }

    const isSmallScreen = useMediaQuery({ query: '(max-width: 764px)' })

    useEffect(() => {  
        if(isSmallScreen) {
            if(AsideBarHidden) {
                gsap.to("aside", {
                    translateX: "0",
                    duration: 0.5
                })
            }
            else {
                gsap.to("aside", {
                    translateX: "-100%",
                    duration: 0.5
                })
            }
        }
        
    }, [AsideBarHidden])
    
    return (
        <aside className="private-course-sidebar md:relative absolute translate-x-[-100%] z-[9999] md:translate-x-0 w-[19%] md:w-[20%] h-[100vh] bg-white">
            <div className="inner-container overflow-y-scroll w-full h-full">
                <div>
                    <div className="overview sticky z-10 top-0 bg-white">
                        <div className="flex lg:p-4 md:p-3 sm:p-2 pr-1 py-2 w-full items-center">
                            <i class="fa-solid fa-bars scale-75 md:scale-90 lg:scale-100"></i>
                            <h2 onClick={() => {
                                dispatch(setCurrentCourseId(0));
                            }} className="cursor-pointer lg:ml-4 md:ml-3 sm:ml-2 ml-1 lg:text-[1.5rem] md:text-[0.9rem] text-[0.7rem] select-none font-semibold">Overview</h2>
                            <i onClick={() => {
                                dispatch(setAsideBarStatus(false));
                            }} class="fa-solid cursor-pointer fa-x ml-auto md:hidden scale-50"></i>
                        </div>
                        <div className="division-line w-full h-[1.8px] bg-[#E0E0E0]"></div>
                    </div>
                    <div className="courses-view">
                        <div className="courses-view-container">
                            <div onClick={HandleCoursesList} className="flex items-center pl-1 sm:pl-2 md:pl-3 relative py-2 cursor-pointer hover:bg-[#dbdbdd6d] duration-300">
                                <i class="fa-solid fa-chevron-right sm:ml-1 scale-[0.7] sm:scale-75 md:scale-100" id="arrow"></i>
                                <p className="truncate select-none lg:ml-4 md:ml-3 sm:ml-2 ml-1 text-[0.6rem] md:text-[0.8rem] xl:text-[1rem]">Private Courses</p>
                            </div>
                            <ul className="truncate" id="courses-list">
                                <div className="pl-2 md:pl-5 bg-[#e6e4e4c8] overflow-hidden">
                                    {
                                        privateCourses?.map((course, index) => {
                                            return (
                                                <div className="pr-1 md:pr-2 translate-x-[-100%]">
                                                    <li onClick={() => {
                                                        if(currentCourseId != course.courseid)
                                                            dispatch(setCurrentCourseId(course.courseid));
                                                    }} key={index} className="w-full pl-2 flex gap-2 items-center my-[0.2rem] py-[0.38rem] rounded-full cursor-pointer hover:bg-[#f8f8f9da] duration-300">
                                                        <div className="image-container w-[1.5rem] md:w-[2rem] lg:w-[2.5rem] h-[1.5rem] md:h-[2rem] lg:h-[2.5rem]">
                                                            <img className="w-full h-full object-cover sm:mr-0 aspect-square rounded-full" src={course.courseimage} alt="test-image" />
                                                        </div>
                                                        <p className="w-[0.7rem] flex-grow truncate capitalize text-[0.5rem] sm:text-[0.6rem] md:text-[0.7rem] lg:text-[1rem]">{course.title}</p>
                                                    </li>
                                                </div>
                                            )
                                        })
                                    }
                                </div>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </aside>
    )
}

export default PrivateCoursesSideBar