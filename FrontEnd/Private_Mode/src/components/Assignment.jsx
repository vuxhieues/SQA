import { Link } from "react-router-dom"
import TestImage from "../assets/3mk.jpg"
import { useSelector } from "react-redux";

function Assignment(props) {
    const { currentCourseId } = useSelector(state => state.ResponsiveComponents);
    console.log(props);
    
    function renderComponent() {
        if (props.student) {
            console.log("I am student");
            
            if (props.student.status == "pending") {
                console.log("I will go");
                return (
                    <Link to={`https://yomac-public-7m6c.vercel.app/course/${currentCourseId}/sec/${props.sectionid}/assign/${props.id}`} className="block shadow-lg border-[0.1px] px-1 pt-2 pb-3 bg-white rounded-2xl border-gray-400">
                    <div className="announcement-text px-2">
                        <div className="flex justify-between">
                            <p className="text-[0.45rem] md:text-[1rem] font-semibold capitalize">{props.title}</p>
                            <p className="text-[0.45rem] md:text-[0.8rem] lg:text-[1rem]">{new Date(props.createdat).toLocaleString()}</p>
                        </div>
                        <p className="text-[0.6rem] md:text-[1rem] mt-4">{props.description}</p>
                        <div className="flex items-center">
                            <p className="text-[0.6rem] md:text-[1rem] mt-4 md:pr-5 pr-3">max marks: {props.maxMarks}</p>
                            <p className="text-[0.6rem] md:text-[1rem] mt-4 mr-auto md:pl-5 pl-3">passing marks: {props.passingMarks}</p>
                            {
                                props.student &&
                                <p className="text-[0.6rem] md:text-[1rem] mt-4 pl-5 text-green-600">{props.student.status}</p>
                            }
                        </div>
                    </div>
                </Link>
                )
            }
            else {
                return (
                    <div className="block shadow-lg border-[0.1px] px-1 pt-2 pb-3 bg-white rounded-2xl border-gray-400">
                    <div className="announcement-text px-2">
                        <div className="flex justify-between">
                            <p className="text-[0.45rem] md:text-[1rem] font-semibold capitalize">{props.title}</p>
                            <p className="text-[0.45rem] md:text-[0.8rem] lg:text-[1rem]">{new Date(props.createdat).toLocaleString()}</p>
                        </div>
                        <p className="text-[0.6rem] md:text-[1rem] mt-4">{props.description}</p>
                        <div className="flex items-center">
                            <p className="text-[0.6rem] md:text-[1rem] mt-4 md:pr-5 pr-3">max marks: {props.maxMarks}</p>
                            <p className="text-[0.6rem] md:text-[1rem] mt-4 mr-auto md:pl-5 pl-3">passing marks: {props.passingMarks}</p>
                            {
                                props.student &&
                                <p className="text-[0.6rem] md:text-[1rem] mt-4 pl-5 text-green-600">{props.student.status}</p>
                            }
                        </div>
                    </div>
                </div>
                )
            }
        }
        else {
            return (
                <Link to={`https://yomac-public-7m6c.vercel.app/course/${currentCourseId}/sec/${props.sectionid}/assign/${props.id}`} className="block shadow-lg border-[0.1px] px-1 pt-2 pb-3 bg-white rounded-2xl border-gray-400">
                    <div className="announcement-text px-2">
                        <div className="flex justify-between">
                            <p className="text-[0.45rem] md:text-[1rem] font-semibold capitalize">{props.title}</p>
                            <p className="text-[0.45rem] md:text-[0.8rem] lg:text-[1rem]">{new Date(props.createdat).toLocaleString()}</p>
                        </div>
                        <p className="text-[0.6rem] md:text-[1rem] mt-4">{props.description}</p>
                        <div className="flex items-center">
                            <p className="text-[0.6rem] md:text-[1rem] mt-4 md:pr-5 pr-3">max marks: {props.maxMarks}</p>
                            <p className="text-[0.6rem] md:text-[1rem] mt-4 mr-auto md:pl-5 pl-3">passing marks: {props.passingMarks}</p>
                        </div>
                    </div>
                </Link>
            )
        }
    }  
    return (
        <div className="assignment-container">
            <div className="py-3 px-2">
                {renderComponent()}
            </div>
        </div>
    )
}

export default Assignment