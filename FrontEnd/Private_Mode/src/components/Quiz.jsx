import { Link } from "react-router-dom"
import TestImage from "../assets/3mk.jpg"
import { useSelector } from "react-redux";
import { useRef, useState } from "react";
import { prepareStackTrace } from "postcss/lib/css-syntax-error";

function Quiz(props) {    
    const { currentCourseId } = useSelector(state => state.ResponsiveComponents);
    const { currentCourse } = useSelector(state => state.PrivateCourse);
    const { role, user_id } = useSelector(state => state.Authorization);
    let isStudent = false;
    let isInstructor = false;
    let isTopInstructor = false;
    let roleIndex
    
    if (role === "student") {
        isStudent = true;
        roleIndex = 0;
    } else {
        isInstructor = true;
        roleIndex = 1;
        if (currentCourse.topinstructorid == user_id) {
            isTopInstructor = true;
            roleIndex = 2;
        }
    }
    console.log(props);

    function renderComponent() {
        console.log(props.student);
        
        if (props.student) {
            if (props.student.status == "pending") {
                return (
                    <Link to={`https://yomac-public-7m6c.vercel.app/course/${currentCourseId}/quiz/${props.id}/${roleIndex}`} className="block shadow-lg border-[0.1px] px-2 pt-2 pb-5 bg-white rounded-2xl border-gray-400">
                    <div className="inner-container flex">
                        <div className="image-container w-[4.3rem] md:w-[5rem] h-[4.3rem] md:h-[5rem] overflow-hidden flex items-center justify-center pr-2">
                            <img className="w-[100%] h-[100%] aspect-square rounded-full" src={props.instructor.profilepic} alt="Image"/>
                        </div>
                        <div className="pl-2 flex flex-col justify-center">
                            <p className="text-[0.6rem] sm:text-[0.8rem] md:text-[1rem]">{props.instructor.username}</p>
                            <p className="text-[0.6rem] sm:text-[0.8rem] md:text-[1rem]">21May 21</p>
                        </div>
                    </div>
                    <div className="flex">
                        <div className="quiz-text">
                            <p className="text-[0.6rem] md:text-[1rem] ml-5">Title: {props.title}</p>
                            <p className="text-[0.6rem] md:text-[1rem] ml-5">Max Marks: {props.maxMarks}</p>
                            <p className="text-[0.6rem] md:text-[1rem] ml-5">Passing Marks: {props.passingMarks}</p>
                        </div>
                    {
                        props.student &&
                        <div className="student-data">
                            <p className="text-[0.6rem] md:text-[1rem] ml-5">Status: {props.student.status}</p>
                            <p className="text-[0.6rem] md:text-[1rem] ml-5">Pass: {props.student.pass ? props.student.pass : "Still no data"}</p>
                            <p className="text-[0.6rem] md:text-[1rem] ml-5">grade: {props.student.grade ? props.student.grade : "Still no data"}</p>
                        </div>
                    }
                    </div>
                </Link>
                )
            }
            else {
                return (
                    <div className="block shadow-lg border-[0.1px] px-2 pt-2 pb-5 bg-white rounded-2xl border-gray-400">
                        <div className="inner-container flex">
                            <div className="image-container w-[4.3rem] md:w-[5rem] h-[4.3rem] md:h-[5rem] overflow-hidden flex items-center justify-center pr-2">
                                <img className="w-[100%] h-[100%] aspect-square rounded-full" src={props.instructor.profilepic} alt="Image"/>
                            </div>
                            <div className="pl-2 flex flex-col justify-center">
                                <p className="text-[0.6rem] sm:text-[0.8rem] md:text-[1rem]">{props.instructor.username}</p>
                                <p className="text-[0.6rem] sm:text-[0.8rem] md:text-[1rem]">21May 21</p>
                            </div>
                        </div>
                        <div className="flex">
                            <div className="quiz-text">
                                <p className="text-[0.6rem] md:text-[1rem] ml-5">Title: {props.title}</p>
                                <p className="text-[0.6rem] md:text-[1rem] ml-5">Max Marks: {props.maxMarks}</p>
                                <p className="text-[0.6rem] md:text-[1rem] ml-5">Passing Marks: {props.passingMarks}</p>
                            </div>
                        {
                            props.student &&
                            <div className="student-data">
                                <p className="text-[0.6rem] md:text-[1rem] ml-5">Status: {props.student.status}</p>
                                <p className="text-[0.6rem] md:text-[1rem] ml-5">Pass: {props.student.pass ? props.student.pass : "Still no data"}</p>
                                <p className="text-[0.6rem] md:text-[1rem] ml-5">grade: {props.student.grade ? props.student.grade : "Still no data"}</p>
                            </div>
                        }
                        </div>
                    </div>
                )
            }
        }
        else {
            return (
                <Link to={`https://yomac-public-7m6c.vercel.app/course/${currentCourseId}/quiz/${props.id}/${roleIndex}`} className="block shadow-lg border-[0.1px] px-2 pt-2 pb-5 bg-white rounded-2xl border-gray-400">
                    <div className="inner-container flex">
                        <div className="image-container w-[4.3rem] md:w-[5rem] h-[4.3rem] md:h-[5rem] overflow-hidden flex items-center justify-center pr-2">
                            <img className="w-[100%] h-[100%] aspect-square rounded-full" src={props.instructor.profilepic} alt="Image"/>
                        </div>
                        <div className="pl-2 flex flex-col justify-center">
                            <p className="text-[0.6rem] sm:text-[0.8rem] md:text-[1rem]">{props.instructor.username}</p>
                            <p className="text-[0.6rem] sm:text-[0.8rem] md:text-[1rem]">21May 21</p>
                        </div>
                    </div>
                    <div className="flex">
                        <div className="quiz-text">
                            <p className="text-[0.6rem] md:text-[1rem] ml-5">Title: {props.title}</p>
                            <p className="text-[0.6rem] md:text-[1rem] ml-5">Max Marks: {props.maxMarks}</p>
                            <p className="text-[0.6rem] md:text-[1rem] ml-5">Passing Marks: {props.passingMarks}</p>
                        </div>
                    </div>
                </Link>
            )
        }
    }
    
    return (
        <div className="quiz-container">
            <div className="py-2 px-5 md:py-3 md:px-10">
                {renderComponent()}
            </div>
        </div>
    )
}

export default Quiz