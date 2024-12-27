import { useEffect, useRef, useState } from "react";
import TestImage from "../assets/3mk.jpg"
import { useSelector } from "react-redux";
import SmallLoading from "./SmallLoading/SmallLoading";

function ChatPage(props) {
    const { token, user_id, role } = useSelector(state => state.Authorization);
    const { chatMode } = useSelector(state => state.ResponsiveComponents);
    const [ws, setWs] = useState(null);
    const wsRef = useRef(null);
    const MessageInp = useRef(null);
    const [currMessage, setCurrMessage] = useState("");
    const [chatMessages, setChatMessages] = useState([]);
    const messagesEndRef = useRef(null);
    const [fetchingMessagesStatus, setFetchingMessagesStatus] = useState(true);

    useEffect(() => {
      console.log(token);
      
      if(token) {
        const ws = new WebSocket(`wss://yomac.azurewebsites.net/ws/chat/private_chat/${props.room.chatid}?token=${token}`); // Replace with your WebSocket server URL
        
        // Set up WebSocket event listeners
        ws.onopen = () => {
          console.log('WebSocket connection opened');
          setWs(ws)
          wsRef.current = ws;
        };
        
        ws.onmessage = (event) => {
          if(fetchingMessagesStatus)
            setFetchingMessagesStatus(false);
          const SendedData = JSON.parse(event.data);
          console.log('Received message from server: ', SendedData);
          if(SendedData.message != null) {
            const MessageModel = {
              text: SendedData.message,
              sender: SendedData.sender
            }
            setChatMessages(oldVal => [...oldVal, MessageModel])
          }
          // Handle incoming message
        };
    
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };
    
        ws.onclose = () => {
          console.log('WebSocket connection closed');
        };
    
        // Cleanup on component unmount
      }
      // Create a WebSocket instance
      return () => {        
        if (wsRef.current) {
          console.log("Clean");
          wsRef.current.close();
        }
      };
    }, [token]);

    useEffect(() => {
      console.log(chatMessages);
    }, [chatMessages])

    window.addEventListener("beforeunload", () => {
        console.log(chatMode);
        if (ws) {
            ws.close();
        }
    })

    useEffect(() => {
        console.log(chatMode);
        
        if (ws && !chatMode) {
            ws.close();
        }
    }, [chatMode])

  const sendMessage = (message) => {
    console.log(message);
    if (ws) {
      ws.send(JSON.stringify({ message: message }));
    }};
    return (
        <section className="chat-room flex-grow flex flex-col bg-white rounded-2xl overflow-hidden">
            <header className="w-full flex items-center py-4 px-5">
                <div className="image-container w-[3rem] h-[3rem] md:w-[4rem] md:h-[4rem]">
                    <img src={props.role == "instructor" ? props.room.student.profilepic : props.room.instructor.profilepic} className="w-full h-full rounded-full aspect-square" alt="test-image" />
                </div>
                <div className="ml-4">
                    <p className="text-[1rem] md:text-[1.5rem]">{props.role == "instructor" ? props.room.student.studentname: props.room.instructor.studentname}</p>
                    <p className="text-[0.7rem] md:text-[1rem]">{props.role == "instructor" ? props.room.student.username: props.room.instructor.username}</p>
                </div>  
            </header>
            <main className="chat-messages bg-[#dad9d9] flex-grow flex flex-col overflow-auto relative">
              {
                fetchingMessagesStatus &&
                <div className="absolute left-[50%] top-[50%] translate-x-[-50%] translate-y-[-50%]">
                  <SmallLoading />
                </div>
              }
                <div className="messages h-full flex-grow overflow-auto">
                    {
                      chatMessages.map((message, index) => {
                          console.log(message);
                          console.log(user_id);
                          if(message.sender.id == user_id && role == message.sender.role)
                            return (
                              <div key={index} className="message flex flex-col items-end my-2">
                                <div className="bg-white py-2 px-5 rounded-2xl">
                                  <p className="text-[0.8rem] md:text-[1rem]">{message.text}</p>
                                </div>
                              </div>
                            )
                          else 
                            return (
                              <div key={index} className="message flex flex-col items-start my-2">
                                <div className="bg-white py-2 px-5 rounded-2xl">
                                  <p className="text-[0.8rem] md:text-[1rem]">{message.text}</p>
                                </div>
                              </div>
                            )
                      })
                    }
                </div>
                {
                  fetchingMessagesStatus ?
                  <form onSubmit={(e) => {
                      e.preventDefault();
                      sendMessage(MessageInp.current.value);
                      e.target.reset();
                  }} className="w-full h-[3rem] bg-white flex justify-center sticky top-[100%]">
                      <input disabled ref={MessageInp} className="w-full h-full cursor-not-allowed outline-none px-2" placeholder="Enter Your Message" type="text" />
                  </form>
                  :
                  <form onSubmit={(e) => {
                      e.preventDefault();
                      sendMessage(MessageInp.current.value);
                      e.target.reset();
                  }} className="w-full h-[3rem] bg-white flex justify-center sticky top-[100%]">
                      <input ref={MessageInp} className="w-full h-full outline-none px-2" placeholder="Enter Your Message" type="text" />
                  </form>
                }
            </main>
        </section>
    );
}

export default ChatPage;