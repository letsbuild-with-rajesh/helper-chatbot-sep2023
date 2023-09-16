from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import auth
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Chat
import os
import openai

openai.api_key = os.environ.get('OPENAI_API_KEY')

def get_ai_response(query, chatHistory):
    # Default text
    messages = [{ 'role': 'system', 'content': 'You are an helpful assistant.' }]

    # History of chat
    for chat in chatHistory:
        messages.append({ 'role': 'user', 'content': chat.query })
        messages.append({ 'role': 'assistant', 'content': chat.response })

    # New query
    messages.append({ 'role': 'user', 'content': query})

    api_response = openai.ChatCompletion.create(model = "gpt-3.5-turbo",messages=messages)

    response_message = api_response.choices[0].message.content.strip()
    return response_message

def chatbot(request):
    if request.user.is_authenticated:
        chats = Chat.objects.filter(user=request.user)
        if request.method == 'POST':
            query = request.POST.get('query')
            response = get_ai_response(query, chats)

            chat = Chat(user=request.user, query=query, response=response, created_at=timezone.now())
            chat.save()
            return JsonResponse({'query': query, 'response': response})
        return render(request, 'chatbot.html', { 'chats': chats })
    else:
        return redirect('/')

def clear_chat(request):
    if request.user.is_authenticated:
        chats = Chat.objects.filter(user=request.user)
        for chat in chats:
            chat.delete()
        return JsonResponse({'success': True})
    else:
        return redirect('/')

def login(request):
    if request.method == 'POST':
        userid = request.POST['userid']
        password = request.POST['password']
        user = auth.authenticate(request, username=userid, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = 'Invalid credentials'
            return render(request, 'login.html', {'error_message': error_message})
    else:
        if request.user.is_authenticated:
            return redirect('chatbot')
        else:
            return render(request, 'login.html')

def signup(request):
    if request.method == 'POST':
        userid = request.POST['userid']
        name = request.POST['name']
        password = request.POST['password']
        confirm_password = request.POST['confirmpassword']
        if password == confirm_password:
            try:
                user = User.objects.create_user(userid, name, password)
                user.save()
                auth.login(request, user)
                return redirect('chatbot')
            except:
                error_message = 'Error in signing up. Please try later!'
                return render(request, 'signup.html', {'error_message': error_message})
        else:
            error_message = 'Both passwords should match'
            return render(request, 'signup.html', {'error_message': error_message})
    else:
        return render(request, 'signup.html')

def logout(request):
    auth.logout(request)
    return redirect('/')