import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import axios from "axios";
import YomacApi from "../../utils/AxiosInstance";
import toast from "react-hot-toast";
import { setCurrentCourseId } from "./ResponsiveComponents";

const initialstate = {
    privateCourses: [],
    currentCourse: null,
    announcements: [],
    assignments: [],
    quizzes: [],
    chatRooms: [],
    finishedFetching: 0,
    makeAnnouncementState : null,
    announcementEditedFlag: false,
    announcementToEditID: null,
    announcementRemoveFlag: false,
    announcementToDeleteID: null,
}

export const GetAnnouncements = createAsyncThunk("AnnouncementSlice/getAnnouncements", async (course_id, { getState, rejectWithValue }) => {
    const { token } = getState().Authorization;
    try {
        const response = await YomacApi.get("get_announcement/" + course_id, {
            headers: {
                token: token
            }
        })
        return response.data
    }
    catch (error) {
        return rejectWithValue(error.message)
    }
})

export const MakeAnnouncement = createAsyncThunk("AnnouncementSlice/makeAnnouncement", async (data, { getState, rejectWithValue }) => {
    const { token } = getState().Authorization;
    try {
        const response = await YomacApi.post('make_announcement',
            {
              'announcement': data.announcement,
              'course_id': data.course_id
            },
            {
              headers: {
                'token': token,
                'Content-Type': 'application/json',
              }
            }
          );
        return response.data
    }
    catch (error) {
        return rejectWithValue(error.message)
    }
})

export const MakeThenGetAnnouncement = createAsyncThunk("AnnouncementSlice/makeThenGetAnnouncement", async (data, { dispatch, getState, rejectWithValue }) => {
    await dispatch(MakeAnnouncement(data));
    return dispatch(GetAnnouncements(data.course_id));
})

export const EditAnnouncement = createAsyncThunk("AnnouncementSlice/editAnnouncement", async (data, { getState, rejectWithValue }) => {
    const { token } = getState().Authorization;
    console.log(data);
    try {
        const response = await YomacApi.put('edit_announcement',
            {
              'announcement': data.announcement,
              'course_id': data.course_id,
              "announcement_id": data.announcement_id
            },
            {
              headers: {
                'token': token,
                'Content-Type': 'application/json',
              }
            }
          );
        return [response.data, data.announcement_id]
    }
    catch (error) {
        return rejectWithValue(error.message)
    }
})

export const GetChats = createAsyncThunk("AnnouncementSlice/getChats", async (course_id, { getState, rejectWithValue }) => {
    const { token } = getState().Authorization;
    try {
        const response = await axios.get('https://yomac.azurewebsites.net/api/chat/get_chat_rooms/' + course_id, {
            headers: {
              'token': token,
              'Content-Type': 'application/json',
            }
          });
        return response.data
    }
    catch (error) {
        return rejectWithValue(error.message)
    }
})

export const DeleteAnnouncement = createAsyncThunk("AnnouncementSlice/deleteAnnouncement", async (data, { getState, rejectWithValue }) => {
    const { token } = getState().Authorization;
    console.log(data);
    try {
        const response = await YomacApi.delete('delete_announcement', {
            headers: {
              'token': token,
              'Content-Type': 'application/json',
            },
            data: {
              'announcement_id': data.announcement_id,
              'course_id': data.course_id
            }
          });
        return [response.data, data.announcement_id]
    }
    catch (error) {
        return rejectWithValue(error.message)
    }
})

export const GetAssignmets = createAsyncThunk("AnnouncementSlice/getAssignments", async (course_id, { getState, rejectWithValue }) => {
    const { token } = getState().Authorization;
    try {
        const response = await YomacApi.get("get_course_assignments/" + course_id, {
            headers: {
                token: token
            }
        })
        return response.data
    }
    catch (error) {
        return rejectWithValue(error.message)
    }
})

export const GetQuizzes = createAsyncThunk("AnnouncementSlice/getQuizzes", async (course_id, { getState, rejectWithValue }) => {
    const { token } = getState().Authorization;
    try {
        const response = await YomacApi.get("get_course_quizzes/" + course_id, {
            headers: {
                token: token
            }
        })
        return response.data
    }
    catch (error) {
        return rejectWithValue(error.message)
    }
})

export const GetPrivateCourses = createAsyncThunk("AnnouncementSlice/getPrivateCourses", async (_, { getState, rejectWithValue }) => {
    const { token, role } = getState().Authorization
    console.log(token);
    try {
        const response = await YomacApi.get("get_user_private_courses", {
            headers: {
                token: token
            }
        });
        console.log(response.data);
        if (role == "instructor")
            return [...response.data.top_instructor_courses, ...response.data.non_top_instructor_courses];
        return response.data;
    }
    catch(error) {
        return rejectWithValue(error);
    }
})

const PrivateCourseSlice = createSlice({
    name: 'announcements',
    initialState: initialstate,
    reducers: {
        setEditFlag: (state, action) => {
            state.announcementEditedFlag = action.payload.flag;
            state.announcementToEditID = action.payload.id;
        },
        setRemoveFlag: (state, action) => {
            state.announcementRemoveFlag = action.payload.flag;
            state.announcementToDeleteID = action.payload.id;
        },
        setCurrentCourse: (state, action) => {
            console.log(action.payload);
            
            state.currentCourse = action.payload;
        }
    },
    extraReducers: builder => 
        builder
            .addCase(GetAnnouncements.pending, (state, action) => {

            })
            .addCase(GetAnnouncements.fulfilled, (state, action) => {
                state.announcements = action.payload;
                if(state.makeAnnouncementState !== null)
                    toast.success(
                        "Announcement Made Successfully",
                        {
                            duration: 5000,
                        }
                    )
                state.makeAnnouncementState = false;
                state.finishedFetching++;
            })
            .addCase(GetAnnouncements.rejected, (state, action) => {
                console.log(action.payload);
            })

            .addCase(GetAssignmets.pending, (state, action) => {

            })
            .addCase(GetAssignmets.fulfilled, (state, action) => {
                state.assignments = action.payload;
                state.finishedFetching++;
            })
            .addCase(GetAssignmets.rejected, (state, action) => {
                console.log(action.payload);
            })

            .addCase(GetQuizzes.pending, (state, action) => {

            })
            .addCase(GetQuizzes.fulfilled, (state, action) => {
                state.quizzes = action.payload;
                state.finishedFetching++;
            })
            .addCase(GetQuizzes.rejected, (state, action) => {
                console.log(action.payload);
            })

            .addCase(MakeAnnouncement.pending, (state, action) => {
                state.makeAnnouncementState = true;
            })
            .addCase(MakeAnnouncement.fulfilled, (state, action) => {
                state.makeAnnouncementFlag = true;
            })
            .addCase(MakeAnnouncement.rejected, (state, action) => {
                state.makeAnnouncementFlag = false;
                console.log(action.payload);
            })

            .addCase(EditAnnouncement.pending, (state, action) => {

            })
            .addCase(EditAnnouncement.fulfilled, (state, action) => {
                state.announcementEditedFlag = true;
                state.announcementToEditID = action.payload[1];
                toast.success(
                    "Announcement Edited Successfully",
                    {
                        duration: 5000,
                    }
                )
            })
            .addCase(EditAnnouncement.rejected, (state, action) => {
                console.log(action.payload);
            })

            .addCase(DeleteAnnouncement.pending, (state, action) => {
                // state.announcementRemoveFlag = true;
            })
            .addCase(DeleteAnnouncement.fulfilled, (state, action) => {
                console.log(action.payload);
                state.announcementRemoveFlag = true;
                state.announcementToDeleteID = action.payload[1];
                toast.success(
                    "Announcement Deleted Successfully",
                    {
                        duration: 5000,
                    }
                )
            })
            .addCase(DeleteAnnouncement.rejected, (state, action) => {
                state.announcementRemoveFlag = true;
                console.log(action.payload);
            })

            .addCase(GetChats.pending, (state, action) => {

            })
            .addCase(GetChats.fulfilled, (state, action) => {
                console.log(action.payload);
                state.chatRooms = action.payload;
                state.finishedFetching++;
            })
            .addCase(GetChats.rejected, (state, action) => {
                console.log(action.payload);
            })

            .addCase(MakeThenGetAnnouncement.pending, (state, action) => {

            })
            .addCase(MakeThenGetAnnouncement.fulfilled, (state, action) => {

            })
            .addCase(MakeThenGetAnnouncement.rejected, (state, action) => {
                console.log(action.payload);
            })

            .addCase(GetPrivateCourses.pending, (state, action) => {

            })
            .addCase(GetPrivateCourses.fulfilled, (state, action) => {
                console.log(action.payload);
                state.privateCourses = action.payload;
            })
            .addCase(GetPrivateCourses.rejected, (state, action) => {
                console.log(action.payload);
            })
})

export const { setEditFlag, setRemoveFlag, setCurrentCourse } = PrivateCourseSlice.actions;
export default PrivateCourseSlice.reducer