import "./Announcment.css"
import { useEffect, useRef, useState } from "react"
import TestImage from "../../assets/3mk.jpg"
import { useDispatch, useSelector } from "react-redux";
import { DeleteAnnouncement, EditAnnouncement, setEditFlag, setRemoveFlag } from "../../RTK/Slices/PrivateCourseSlice";
import SmallLoading from "../SmallLoading/SmallLoading";

function Announcement(props) {
    const dispatch = useDispatch();

    const [editMode, setEditMode] = useState(false);
    const [executeEditMode, setExecuteEditMode] = useState(false);
    const [removeMode, setRemoveMode] = useState(false);

    const editButton = useRef(null);
    const AnnouncemnetInp = useRef(null);
    const AnnouncemnetEle = useRef(null);
    
    const [announcementText, setAnnouncementText] = useState(props.announcement);
    const tempAnnouncementText = useRef(null);

    const { announcementRemoveFlag, announcementToDeleteID, announcementEditedFlag, announcementToEditID } = useSelector(state => state.PrivateCourse);

    useEffect(() => {
        if(executeEditMode || removeMode)
            AnnouncemnetEle.current?.classList.add("grayscale");
        else if(!(executeEditMode && removeMode))
            AnnouncemnetEle.current?.classList.remove("grayscale");
    }, [executeEditMode, removeMode])

    useEffect(() => {
        if(announcementRemoveFlag)
            setRemoveMode(false);
    }, [announcementRemoveFlag, announcementToDeleteID])

    useEffect(() => {
        if(announcementEditedFlag === true && announcementToEditID === props.id) {
            setAnnouncementText(tempAnnouncementText.current);
            dispatch(setEditFlag({
                id: null,
                flag: false
            }));
            setExecuteEditMode(false);
        }
        tempAnnouncementText.current = null;
    }, [ announcementEditedFlag, announcementToEditID])
    useEffect(() => {
        console.log(editButton); 
        if(editMode) {            
            editButton.current?.classList.add("edit-active");
        } else {
            editButton.current?.classList.remove("edit-active");
        }
    }, [editMode])

    useEffect(() => {
        console.log("announcementText: ", announcementText);
    }, [announcementText])
    return (
        <div className="announcement-container relative">
            <div className="md:py-3 md:px-10 px-2 py-2">
                <div ref={AnnouncemnetEle} className="relative shadow-lg border-[0.1px] p-4 bg-white rounded-2xl border-gray-400 grayscale">
                    <div className="inner-container flex items-center pb-3">
                        <div className="image-container w-[4.3rem] md:w-[5rem] h-[4.3rem] md:h-[5rem] overflow-hidden flex items-center justify-center">
                            <img className="w-[100%] h-[100%] object-cover aspect-square rounded-full" src={props.announcer.profilepic} alt="Image"/>
                        </div>
                        <div className="pl-4 flex mr-auto flex-col justify-center">
                            <p className="text-[1rem] sm:text-[0.8rem] md:text-[1rem]">{props.announcer.username}</p>
                        </div>
                        {
                            executeEditMode &&
                            <div className="flex justify-center items-center absolute left-[50%] top-[50%] translate-x-[-50%] translate-y-[-50%]">
                                <SmallLoading />
                            </div>
                        }
                        {
                            removeMode &&
                            <div className="flex justify-center items-center absolute left-[50%] top-[50%] translate-x-[-50%] translate-y-[-50%]">
                                <SmallLoading />
                            </div>
                        }
                        <div className="controls pr-5">
                            {
                                props.permission &&
                                <>
                                <button onClick={() => {
                                    setEditMode(!editMode);
                                }} ref={editButton} className="p-0 rounded-3xl mx-1 hover:bg-transparent duration-300 border-[1px] border-yellow-400 bg-yellow-400 text-[0.8rem] md:text-[1rem] px-3 md:px-5 py-1">{editMode ? "Editing" : "Edit"}</button>
                                <button onClick={() => {
                                    dispatch(DeleteAnnouncement({
                                        announcement_id: props.id,
                                        course_id: 9
                                    }))
                                    // dispatch(setRemoveFlag({
                                    //     id: props.id,
                                    //     flag: true
                                    // }))
                                    setRemoveMode(true)
                                }} className="p-0 rounded-3xl mx-1 hover:bg-transparent duration-300 hover:text-black border-[1px] border-red-700 text-white bg-red-700 text-[0.8rem] md:text-[1rem] px-3 md:px-5 py-1">{removeMode ? "Deleting" : "Delete"}</button>
                                </>
                            }
                        </div>
                    </div>
                    <div className="announcement-text">
                        {
                            editMode ?
                            <form onSubmit={(e) => {
                                e.preventDefault();
                                dispatch(EditAnnouncement({
                                    announcement: AnnouncemnetInp.current.value,
                                    course_id: 9,
                                    announcement_id: props.id
                                }))
                                // dispatch(setEditFlag({
                                //     id: props.id,
                                //     flag: true
                                // }));
                                tempAnnouncementText.current = AnnouncemnetInp.current.value;
                                setEditMode(false);
                                setExecuteEditMode(true);
                            }} className="sticky z-[100] top-0 bg-white make-announcement justify-between items-center flex w-full px-3 py-3">
                                <div className="w-[80%] flex justify-center">
                                    <input ref={AnnouncemnetInp} required type="text" defaultValue={announcementText} placeholder="Make Announcement"
                                    className="w-full rounded-3xl p-2 border-[1px] border-black"/>
                                </div>
                                <div className="w-[20%] pl-2 flex justify-center">
                                    <button className="bg-green-600 rounded-3xl w-full py-2 text-white border-[1px] border-green-600 hover:bg-white hover:text-black duration-300">Announce</button>
                                </div>
                            </form>
                            :
                            <p className="text-[0.8 rem] md:text-[1rem] ml-5">{announcementText}</p>
                        }
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Announcement