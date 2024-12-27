import { createSlice } from "@reduxjs/toolkit";

const initialstate = {
    streams: []
}

const StreamSlice = createSlice({
    name: 'stream',
    initialState: initialstate,
    reducers: {
        addStream(state, action) {
            state.streams.push(action.payload)
        },
        removeStream(state, action) {

        }
    }
})

export const { addStream, removeStream } = StreamSlice.actions;
export default StreamSlice.reducer;