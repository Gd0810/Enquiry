from .models import ChatbotSettings, ChatbotQA

def chatbot_context(request):
    settings = ChatbotSettings.load()
    return {
        'chatbot_is_enabled': settings.is_enabled,
    }
