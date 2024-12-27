import { useSelector } from "react-redux";
import SimpleSFUClient from "../utils/SimpleSFUClient.js"
import { useEffect, useRef } from "react";

function LiveStream() {

    const { streams } = useSelector(state => state.Stream);
    
    const x = document.getElementsByTagName("video");
    useEffect(() => {
        console.log(x);
    }, [x])

    // useEffect(() => {
    //     const uniqueStreams = streams.reduce((acc, stream) => {
    //         if (!acc.some(s => s.id === stream.id)) {
    //             acc.push(stream);
    //         }
    //         return acc;
    //     }, []);
    
    //     console.log(uniqueStreams);
    // }, [streams])

    useEffect(() => {
        const simple = new SimpleSFUClient();
    
        simple.on('onConnected', () => {
            simple.connect();
        });
    }, [])
    return (
        <>
            <header className='container flex justify-between items-center'>
                <div className="logo">
                    <a href='#' className='text-[20px] font-bold'>Live Stream</a>
                </div>
                <div className="button-container p-2">
                    <button className='px-5 py-2 bg-green-600 rounded-full text-white border-green-600 border-2
                        hover:bg-transparent hover:text-black duration-300 cursor-pointer text-[18px]'>Enter Room</button>
                </div>
            </header>
            <section className="container py-10 flex justify-center form-sec">
                <form className='w-[50%] p-2 bg-slate-400 rounded-lg cursor-pointer'>
                <p className='text-[25px] text-center font-semibold'>Login</p>
                <div className="username">
                    <label htmlFor="username">UserName</label>
                    <input type="text" id='username' className='w-full p-2 rounded-lg border-2 border-gray-400 focus:outline-none focus:border-blue-600 duration-300' />
                </div>
                <div className="username my-5">
                    <label htmlFor="password-input">Password</label>
                    <input type="password" id='password-input' className='w-full p-2 rounded-lg border-2 border-gray-400 focus:outline-none focus:border-blue-600 duration-300' />
                </div>
                <button className='bg-green-600 w-full py-2 rounded-full text-white text-center font-extrabold'>
                    <p className='inline-block mr-3'>Login</p>
                    <i className="fa-solid fa-right-to-bracket"></i>
                </button>
                </form>
            </section>
            <section className="stream-sec container py-5 ">
                <div id='remote_videos' className="">
                    <div className="videos-inner gap-5 grid grid-cols-2"></div>
                </div>
                {/* <button className='mt-5 rounded-full py-2 bg-green-500'>Start Streaming</button> */}
            </section>
        </>
    );
}

export default LiveStream;