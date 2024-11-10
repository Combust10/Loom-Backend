import fastapi
from typing import Union
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
import re
import time
import asyncio
from fastapi.middleware.cors import CORSMiddleware

app = fastapi.FastAPI()
access_token = "AIzaSyCp2vorMuZsSfc8aw4id5_ToOvCPGv9bgY"

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



llm = GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=access_token)


onboarding_prompt = '''
You are Loom, a friendly and curious conversationalist. Your goal is to get to know the user in a relaxed and natural way, focusing on understanding their interests, background, and personality. 

Start with a very short introduction. You must learn about the user's name first, and then lead up to their age and gender. You MUST have the user's name, age and gender before asking too much about their hobbies and interests. Avoid sounding too formal or robotic. Instead of asking questions in a systematic way, guide the conversation in a friendly, conversational tone.

Share a bit about yourself as well to make it feel like a balanced exchange. For example, you could mention your interests, ask about things they enjoy, and discuss general topics that might lead to discovering the requested details over time.

After you've gathered the user's information, gather details about their interests and hobbies.
Once you’ve gathered enough information,after around every 10 messages, ask if they’d like to continue chatting, but keep it casual—like you’re just keeping the conversation going out of interest rather than as a requirement.

Finally, at the end of each response, you MUST also include a status code, which is only one word, in curly brackets based on the conversation's flow:
If the conversation is going smoothly, with a natural flow of information, use the code "OK".
If you feel the conversation has stalled and you haven’t been able to gather new details in a while, use "TRAILING".
If the user signals they want to end the conversation or stop the chat, or seems like the chat had ended with goodbyes, use "USER_END".
'''

memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm,memory = memory, verbose = True)
@app.post("/onboarding")
async def root_request(user: str, message: str):
    user_message = str(message)
    print(user_message)
    ai_response_data = ""
    if(user_message == "init"):
        result = conversation.predict(input = onboarding_prompt)
        print(result)
        ai_message = re.sub(pattern="\{[\s\S]*\}", repl="", string=result)
        # ai_message = re.sub(pattern="\&[\s\S]*\&", repl="", string=ai_message)
        ai_response_code = re.sub(pattern="\}",repl="",string= re.sub(pattern="\{",repl="", string=re.findall(pattern="\{[\s\S]*\}", string=result)[0]))
        # ai_response_data = re.sub(pattern="\&",repl="", string=re.findall(pattern="\&[\s\S]*\&", string=result)[0])
        # ai_response_data = re.sub(pattern="\&",repl="", string=re.findall(pattern="\&[\s\S]*\&", string=result)[0])
    else:
        result = ""
        while(result == ""):
            result = conversation.predict(input = message)
        print(result)
        ai_message = re.sub(pattern="\{[\s\S]*\}", repl="", string=result)
        # ai_message = re.sub(pattern="\&[\s\S]*\&", repl="", string=ai_message)
        ai_response_code = re.sub(pattern="\}",repl="",string= re.sub(pattern="\{",repl="", string=re.findall(pattern="\{[\s\S]*\}", string=result)[0]))
        # ai_response_data = re.sub(pattern="\&",repl="", string=re.findall(pattern="\&[\s\S]*\&", string=result)[0])
        if(ai_response_code == "USER_END"):
            result = conversation.predict(input = """Give me a json file with all the collected details. The name, age and gender are must have fields. Put "unspecified" as their values if you could not aqcuire those details.
                                                    Finally, add a 4th field called "biodata" which is an array that contains all other details on the same level like a csv, without the key names.""")
            print(result)
            ai_message = ""
            ai_response_data = result
            ai_response_code = "COMPLETED"

    return {"response_message":ai_message,"response_code":ai_response_code,"response_data":ai_response_data}
