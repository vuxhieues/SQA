import { createSlice } from "@reduxjs/toolkit";

const initialstate = {
    AsideBarHidden: false,
    currentCourseId: 0,
    chatMode: false 
}
const ResponsiveComponents = createSlice({
    name: 'ResponsiveComponents',
    initialState: initialstate,
    reducers: {
        setAsideBarStatus: (state, action) => {
            state.AsideBarHidden = action.payload;
        },
        setCurrentCourseId: (state, action) => {
            state.currentCourseId = action.payload;
        },
        setChatMode: (state, action) => {
            state.chatMode = action.payload;
        }
    }
})

export const { setAsideBarStatus, setCurrentCourseId, setChatMode } = ResponsiveComponents.actions;
export default ResponsiveComponents.reducer