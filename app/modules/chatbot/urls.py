from app.modules.chatbot.routers.chatbot_message_router import router as chatbot_message_router
from app.modules.chatbot.routers.chatbot_session_router import router as chatbot_session_router

chatbot = (chatbot_message_router, chatbot_session_router)