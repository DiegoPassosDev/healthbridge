from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.messages import constants
from django.contrib import messages
from django.contrib import auth


def cadastro(request):	
  if request.method == 'GET':
    return render(request, 'cadastro.html')
  elif request.method == 'POST':
    username = request.POST.get('username')
    email = request.POST.get('email')
    senha = request.POST.get('senha')
    confirmar_senha = request.POST.get('confirmar_senha')    
  
    if senha != confirmar_senha:
      messages.add_message(request, constants.ERROR, 'Senhas não conferem')
      return redirect('cadastro')
    
    if len(senha) < 6:
      messages.add_message(request, constants.ERROR, 'Senha deve ter no mínimo 6 caracteres')
      return redirect('cadastro')
    
    users = User.objects.filter(username=username.upper())

    if users.exists():
      messages.add_message(request, constants.ERROR, 'Usuário já cadastrado')
      return redirect('cadastro')
    
    user = User.objects.create_user(
      username=username.upper(), 
      email=email.lower(), 
      password=senha
    )
    return redirect('login')
  
def login_view(request):
  if request.method == 'GET':
    return render(request, 'login.html')
  elif request.method == 'POST':
    username = request.POST.get('username')
    senha = request.POST.get('senha')
    
    user = auth.authenticate(request, username=username.upper(), password=senha)

    if user:
      auth.login(request, user)
      return redirect('/pacientes/home')

    messages.add_message(request, constants.ERROR, 'Usuário ou senha inválidos')    
    
    return redirect('login')


def logout_view(request):
  auth.logout(request)
  return redirect('login')
