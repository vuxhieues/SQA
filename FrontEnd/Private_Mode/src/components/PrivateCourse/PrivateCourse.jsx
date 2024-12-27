import { Link, Route, Routes } from "react-router-dom"
import Announcement from "../Announcement/Announcement"
import "./PrivateCourse.css"
import { useEffect, useRef, useState } from "react"
import Assignment from "../Assignment";
import Quiz from "../Quiz";
import TestImage from "../../assets/3mk.jpg"
import { useDispatch, useSelector } from "react-redux";
import { GetAnnouncements, GetAssignmets, GetChats, GetQuizzes, MakeAnnouncement, MakeThenGetAnnouncement, setCurrentCourse, setRemoveFlag } from "../../RTK/Slices/PrivateCourseSlice";
import ChatPage from "../ChatPage";
import { setChatMode } from "../../RTK/Slices/ResponsiveComponents";
import SmallLoading from "../SmallLoading/SmallLoading";
import LoadingScreen from "../LoadingScreen/LoadingScreen";

function PrivateCourse() {
    const dispatch = useDispatch();
    const announcemnetInp = useRef(null);
    const [currentChatIndex, setCurrentChatIndex] = useState(-1);
    const { chatMode } = useSelector(state => state.ResponsiveComponents);

    const { token, user_id, role } = useSelector(state => state.Authorization);
    const { currentCourseId } = useSelector(state => state.ResponsiveComponents);
    const { quizzes, assignments, announcements, chatRooms, finishedFetching, currentCourse, privateCourses } = useSelector(state => state.PrivateCourse);

    const [shownPartNumber, setShownPartNumber] = useState(0);
    const [localAnnouncements, setLocalAnnouncements] = useState([]);
    
    const { announcementRemoveFlag, announcementToDeleteID, makeAnnouncementState } = useSelector(state => state.PrivateCourse);

    useEffect(() => {  
        privateCourses?.forEach(course => {
            if (course.courseid == currentCourseId) {
                dispatch(setCurrentCourse(course));
        }})
    }, [currentCourseId, privateCourses])

    useEffect(() => {
        setLocalAnnouncements(announcements);
    }, [announcements])
    
    useEffect(() => {
        console.log(announcementRemoveFlag, announcementToDeleteID);
        if(announcementRemoveFlag) {
            const index = localAnnouncements.findIndex(
                announcement => announcement.announcementid === announcementToDeleteID
            );
            if (index !== -1) {
                let x = [...localAnnouncements]
                console.log(localAnnouncements);
                console.log(index);
                x.splice(index, 1); // Remove 1 element at the specified index
                setLocalAnnouncements(x);
            }
            dispatch(setRemoveFlag({
                id: null,
                flag: false
            }));
        }
    }, [announcementRemoveFlag, announcementToDeleteID])

    useEffect(() => {
        if(currentCourseId != null && token != null) {
            dispatch(GetAnnouncements(currentCourseId));
            dispatch(GetAssignmets(currentCourseId));
            dispatch(GetQuizzes(currentCourseId));
            dispatch(GetChats(currentCourseId));
        }
    }, [currentCourseId, token])

    function renderAnnouncementForm() {
        if(shownPartNumber === 0 && user_id != null && user_id == currentCourse?.topinstructorid && role != null && role == "instructor") {
            return (
                <form onSubmit={(e) => {
                    e.preventDefault();
                    dispatch(MakeThenGetAnnouncement({
                        course_id: 9,
                        announcement: announcemnetInp.current.value  
                    }))
                    e.target.reset();
                }}
                    className="sticky z-[500] top-0 bg-white make-announcement justify-evenly items-center flex w-full px-3 py-5">
                    <div className="w-[80%] md:w-[85%] pr-5 flex justify-center">
                        <input required ref={announcemnetInp} type="text" placeholder="Make Announcement"
                        className="w-full placeholder:text-[0.7rem] placeholder:md:text-[1rem] md:p-2 p-1 border-[1px] border-black"/>
                    </div>
                    <div className="w-[15%] flex justify-center">
                        <button className="bg-green-600 flex justify-center items-center lg:gap-3 md:gap-2 gap-3 py-2 w-full text-[1rem] sm:text-[0.8rem] md:text-[0.9rem] lg:text-[1rem] rounded-3xl text-white border-[1px] border-green-600 hover:bg-white hover:text-black duration-300">
                            {
                                makeAnnouncementState &&
                                <SmallLoading />
                            }
                            Announce
                        </button>
                    </div>
                </form>
            )
        }
    }

    return (
        <>
            {
                finishedFetching < 3 &&
                <LoadingScreen />
            }
            <header className="w-full bg-white py-2 rounded-2xl">
                <h1 className="text-black text-[3rem] lg:text-[5rem] text-center">{currentCourse?.title}</h1>
            </header>
            <main className="pt-1 relative flex flex-col flex-grow overflow-auto">
                <div className="pb-1">
                    <div className="inner-container rounded-2xl bg-white">
                        <ul className="menu flex items-center px-2 md:px-4">
                            <li onClick={() => {
                                dispatch(setChatMode(false));
                                setShownPartNumber(0);
                            }} className="w-fit cursor-pointer md:px-2 px-1 select-none py-1 md:py-3 menu-item lg:text-[1rem] md:text-[0.8rem] sm:text-[0.7rem] text-[0.5rem]  mx-1 sm:mx-2 md:mx-4 z-[1] relative before:absolute before:left-0 before:right-0 before:h-[10px] before:content-[''] before:z-[9999] before:text-black">Announcements</li>
                            <li onClick={() => {
                                dispatch(setChatMode(false));
                                setShownPartNumber(1);
                            }} className="w-fit cursor-pointer md:px-2 px-1 select-none py-1 md:py-3 menu-item lg:text-[1rem] md:text-[0.8rem] sm:text-[0.7rem] text-[0.5rem]  mx-1 sm:mx-2 md:mx-4">Assignments</li>
                            <li onClick={() => {
                                dispatch(setChatMode(false));
                                setShownPartNumber(2);
                            }} className="w-fit cursor-pointer md:px-2 px-1 select-none py-1 md:py-3 menu-item lg:text-[1rem] md:text-[0.8rem] sm:text-[0.7rem] text-[0.5rem]  mx-1 sm:mx-2 md:mx-4">Quizzes</li>
                            <li onClick={() => {
                                dispatch(setChatMode(false));
                                setShownPartNumber(3);
                            }} className="w-fit cursor-pointer md:px-2 px-1 select-none py-1 md:py-3 menu-item lg:text-[1rem] md:text-[0.8rem] sm:text-[0.7rem] text-[0.5rem]  mx-1 sm:mx-2 md:mx-4">Chat</li>
                            <Link to={`https://yomac-public-7m6c.vercel.app/course/${currentCourseId}`} onClick={() => {
                                dispatch(setChatMode(false));
                                setShownPartNumber(4);
                            }}
                             className="w-fit cursor-pointer md:px-2 px-1 select-none py-1 md:py-3 menu-item lg:text-[1rem] md:text-[0.8rem] sm:text-[0.7rem] text-[0.5rem]  mx-1 sm:mx-2 md:mx-4">Sections</Link>
                        </ul>
                    </div>
                </div>
                {
                    !chatMode ?
                    <div className="content overflow-auto bg-white rounded-2xl flex-grow h-full">
                        {
                            role &&
                            renderAnnouncementForm()
                        }
                        {
                            shownPartNumber === 0 && localAnnouncements.length === 0 &&
                            <div className="text-center capitalize text-[1rem] md:text-[2rem] lg:text-[3rem] absolute top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%]">No Announcements yet</div>                       }
                        {
                            shownPartNumber === 0 &&
                            localAnnouncements.map(announcement => {
                                return <Announcement permission={user_id != null && user_id == currentCourse?.topinstructorid && role != null && role == "instructor"} key={announcement.announcementid} id={announcement.announcementid} courseid={announcement.courseid} announcement={announcement.announcement}
                                    announcer={announcement.announcer} />
                            })
                        }
                        {
                            shownPartNumber === 1 &&
                            assignments.map(assignment => {
                                return (
                                    <div key={assignment.courseid} className="section-container">
                                        <div className="px-[5px] py-2 md:py-3 md:px-10">
                                            <div className="shadow-lg border-[0.1px] px-2 pt-2 pb-5 bg-white rounded-2xl border-gray-400">
                                                <div className="inner-container flex">
                                                    <div className="pl-2 flex flex-col justify-center">
                                                        <p className="text-[0.6rem] sm:text-[0.8rem] md:text-[1rem] font-bold capitalize">{assignment.title}</p>
                                                    </div>
                                                </div>
                                                <div className="assignments">
                                                    <div className="flex">
                                                        <p className="text-[0.6rem] md:text-[0.8rem] lg:text-[1rem] p-3 ml-1 md:p-5 md:ml-3">Assignments:</p>
                                                        <div className="flex-grow flex items-center w-full">
                                                            {
                                                                assignment.assignment.length === 0 &&
                                                                <p className="text-center ml-4">No Assignments Yet</p>
                                                            }
                                                            {
                                                                assignment.assignment.map(assignmentItem => {
                                                                    return <Assignment key={assignmentItem.assignmentid} id={assignmentItem.assignmentid}
                                                                    description={assignmentItem.description} maxMarks={assignmentItem.maxmarks}
                                                                    passingMarks={assignmentItem.passingmarks} sectionid={assignment.coursesectionid} title={assignmentItem.title} createdat={assignmentItem.createdat}
                                                                    student={assignmentItem.student}/>
                                                                })
                                                            }
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )
                            })
                        }
                        {
                            shownPartNumber === 2 &&
                            quizzes.map(quiz => {
                                return (
                                    <div key={quiz.courseid} className="section-container">
                                        <div className="px-[5px] py-2 md:py-3 md:px-10">
                                            <div className="shadow-lg border-[0.1px] px-2 pt-2 pb-5 bg-white rounded-2xl border-gray-400">
                                                <div className="inner-container flex">
                                                    <div className="pl-2 flex flex-col justify-center">
                                                        <p className="text-[0.6rem] sm:text-[0.8rem] md:text-[1rem] font-bold capitalize">{quiz.title}</p>
                                                    </div>
                                                </div>
                                                <div className="assignments">
                                                    <div className="flex">
                                                        <p className="text-[0.6rem] md:text-[0.8rem] lg:text-[1rem] p-3 ml-1 md:p-5 md:ml-3">Quizzes:</p>
                                                        <div className="flex-grow w-full">
                                                            {
                                                                quiz.quizzes.length === 0 &&
                                                                <p className="text-[0.6rem] md:text-[0.8rem]
                                                                lg:text-[1rem] p-3 ml-1 md:p-5 md:ml-
                                                                3">No quizzes available in this section</p>
                                                            }
                                                            {
                                                                quiz.quizzes.map(quizItem => {                                                                
                                                                    return <Quiz key={quizItem.quizexamid}
                                                                    maxMarks={quizItem.totalmarks} id={quizItem.quizexamid}
                                                                    passingMarks={quizItem.passingmarks} instructor={quizItem.instructor} student={quizItem.student} title={quizItem.title} createdat={quizItem.createdat}/>
                                                                })
                                                            }
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )
                            })
                        }
                        {
                            shownPartNumber == 3 &&
                            <section className="grid grid-flow-row md:grid-cols-2 grid-cols-1">
                                {
                                    chatRooms.length === 0 &&
                                    <p className="text-center text-[1rem] md:text-[2rem] lg:text-[3rem] absolute top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%]">No Students Yet in here</p>
                                }
                                {
                                    chatRooms?.map((room, index) => {
                                        if(role == "instructor")
                                            return (
                                                <div key={room.chatid} id={room.chatid} courseid={room.courseid} className="w-full p-2">
                                                    <div onClick={() => {
                                                        setCurrentChatIndex(index);
                                                        dispatch(setChatMode(true));
                                                    }} className="inner-container p-2 rounded-md shadow-lg flex items-center cursor-pointer">
                                                        <div className="image-container w-[4.5rem] h-[4.5rem]">
                                                            <img className="w-full h-full object-cover rounded-full aspect-square"
                                                                src={room.student.profilepic} alt="" />
                                                        </div>
                                                        <div className="data pl-4">
                                                            <p className="text-[1.3rem] font-semibold capitalize">{room.student.studentname}</p>
                                                            <p className="text-[0.8rem] capitalize">{room.student.username}</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                            else if(role == "student")
                                                return (
                                                    <div key={room.chatid} id={room.chatid} courseid={room.courseid} className="w-full p-2">
                                                        <div onClick={() => {
                                                            setCurrentChatIndex(index);
                                                            dispatch(setChatMode(true));
                                                        }} className="inner-container p-2 rounded-md shadow-lg flex items-center cursor-pointer">
                                                            <div className="image-container w-[4.5rem] h-[4.5rem]">
                                                                <img className="w-full h-full object-cover rounded-full aspect-square"
                                                                    src={room.instructor.profilepic} alt="" />
                                                            </div>
                                                            <div className="data pl-4">
                                                                <p className="text-[1.3rem] font-semibold capitalize">{room.instructor.instructorname}</p>
                                                                <p className="text-[0.8rem] capitalize">{room.instructor.username}</p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                    })
                                }
                            </section>
                        }
                    </div>
                    :
                    <ChatPage role={role} room={chatRooms[currentChatIndex]}/>
                }
            </main>
        </>
    )
}

export default PrivateCourse