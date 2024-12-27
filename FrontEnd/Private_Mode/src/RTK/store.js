import { configureStore } from "@reduxjs/toolkit";
import AuthorizationReducer from "./Slices/AuthorizationSlice";
import CourseSlice from "./Slices/CourseSlice";
import StudentSlice from "./Slices/StudentSlice";
import PrivateCourseSlice from "./Slices/PrivateCourseSlice"
import ResponsiveComponentsReducer from "./Slices/ResponsiveComponents"
import StreamSlice from "./Slices/StreamSlice";

const store = configureStore({
  reducer: {
    Authorization: AuthorizationReducer,
    Course: CourseSlice,
    student: StudentSlice,
    PrivateCourse: PrivateCourseSlice,
    ResponsiveComponents: ResponsiveComponentsReducer,
    Stream: StreamSlice
  },
});

export default store;
