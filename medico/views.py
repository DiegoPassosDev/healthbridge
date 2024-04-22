from django.shortcuts import redirect, render
from .models import DadosMedico, Especialidades, is_medico, DatasAbertas
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.messages import constants
from datetime import datetime, timedelta
from paciente.models import Consulta, Documento

def cadastro_medico(request):  
  if is_medico(request.user):
    messages.add_message(request, constants.ERROR, 'Você já é um médico cadastrado')
    return redirect('abrir_horario')

  if request.method == 'GET':
    especialidades = Especialidades.objects.all()
    return render(request, 'cadastro_medico.html', {'especialidades': especialidades, 'is_medico': is_medico(request.user)})
  elif request.method == 'POST':
    crm = request.POST.get('crm')
    nome = request.POST.get('nome')
    cep = request.POST.get('cep')
    endereco = request.POST.get('endereco')
    bairro = request.POST.get('bairro')
    numero = request.POST.get('numero')
    cim = request.FILES.get('cim')
    rg = request.FILES.get('rg')
    foto = request.FILES.get('foto')
    especilidade = request.POST.get('especialidade')
    descricao = request.POST.get('descricao')
    valor_consulta = request.POST.get('valor_consulta')

    dados_medico = DadosMedico(
      crm=crm, 
      nome=nome.upper(), 
      cep=cep, 
      endereco=endereco.upper(), 
      bairro=bairro.upper(), 
      numero=numero, 
      cedula_identidade_medica=cim, 
      rg=rg, 
      foto=foto, 
      especialidade=Especialidades.objects.get(pk=especilidade),
      descricao=descricao.upper(), 
      valor_consulta=valor_consulta,
      user=request.user,
    )

    dados_medico.save()
    messages.add_message(request, constants.SUCCESS, 'Médico cadastrado com sucesso')
    return redirect('abrir_horario')

def abrir_horario(request):
  if not is_medico(request.user):
    messages.add_message(request, constants.WARNING, 'Você não é um médico cadastrado')
    return redirect('cadastro_medico')
  
  if request.method == 'GET':
    dados_medico = DadosMedico.objects.get(user=request.user)
    datas_abertas = DatasAbertas.objects.filter(user=request.user)
    return render(request, 'abrir_horario.html', {'dados_medico': dados_medico, 'datas_abertas': datas_abertas, 'is_medico': is_medico(request.user)})
  
  elif request.method == 'POST':
    data = request.POST.get('data')
    data_formatada = datetime.strptime(data, '%Y-%m-%dT%H:%M')

    if data_formatada < datetime.now():
      messages.add_message(request, constants.WARNING, 'Data anterior a data atual.')
      return redirect('abrir_horario')
    
    horario_abrir = DatasAbertas(
      data=data_formatada,
      user=request.user,
    )

    horario_abrir.save()

    messages.add_message(request, constants.SUCCESS, 'Horário cadastrado com sucesso')    

    return redirect('abrir_horario')
  
def consultas_medico(request):
  if not is_medico(request.user):
    messages.add_message(request, constants.WARNING, 'Você não é um médico cadastrado')
    return redirect('/usuarios/logout/')

  hoje = datetime.now().date()

  consultas_hoje = Consulta.objects.filter(data_aberta__user=request.user).filter(data_aberta__data__gte=hoje).filter(data_aberta__data__lt=hoje + timedelta(days=1))

  consultas_restantes = Consulta.objects.exclude(id__in=consultas_hoje.values_list('id')).filter(datas_abertas__user=request.user)

  return render(request, 'consultas_medico.html', {'consultas_hoje': consultas_hoje, 'consultas_restantes': consultas_restantes, 'is_medico': is_medico(request.user)})

def consulta_area_medico(request, id_consulta):
  if not is_medico(request.user):
    messages.add_message(request, constants.WARNING, 'Você não é um médico cadastrado')
    return redirect('/usuarios/logout/')

  if request.method == 'GET':
    consulta = Consulta.objects.get(id=id_consulta)
    documentos = Documento.objects.filter(consulta=consulta)
    return render(request, 'consulta_area_medico.html', {'consulta': consulta, 'is_medico': is_medico(request.user), 'documentos': documentos})
  elif request.method == 'POST':
    consulta = Consulta.objects.get(id=id_consulta)
    link = request.POST.get('link')

    if consulta.status == 'C':
      messages.add_message(request, constants.WARNING, 'Consulta já foi cancelada.')
      return redirect(f'/medicos/consulta_area_medico/{id_consulta}')
    elif consulta.status == 'F':
      messages.add_message(request, constants.WARNING, 'Consulta já foi finalizada.')
      return redirect(f'/medicos/consulta_area_medico/{id_consulta}')
    
    consulta.link = link
    consulta.status = 'I'
    consulta.save()
    messages.add_message(request, constants.SUCCESS, 'A consulta acaba de ser iniciada.')
    return redirect(f'/medicos/consulta_area_medico/{id_consulta}')
  
def finalizar_consulta(request, id_consulta):
  if not is_medico(request.user):
    messages.add_message(request, constants.WARNING, 'Você não é um médico cadastrado')
    return redirect('/usuarios/logout/')

  consulta = Consulta.objects.get(id=id_consulta)

  if consulta.data_aberta.user != request.user:
    messages.add_message(request, constants.ERROR, 'Você não tem permissão para finalizar essa consulta.')
    return redirect(f'/medicos/consulta_area_medico/{id_consulta}')

def add_documento(request, id_consulta):
  if not is_medico(request.user):
    messages.add_message(request, constants.WARNING, 'Você não é um médico cadastrado')
    return redirect('/usuarios/logout/')

  consulta = Consulta.objects.get(id=id_consulta)

  if consulta.data_aberta.user != request.user:
    messages.add_message(request, constants.ERROR, 'Você não tem permissão para adicionar documentos a essa consulta.')
    return redirect(f'/medicos/consulta_area_medico/{id_consulta}')
  
  if request.method == 'GET':
    return render(request, 'consulta_area_medico', {'consulta': consulta, 'is_medico': is_medico(request.user)})
  elif request.method == 'POST':
    titulo = request.POST.get('titulo')
    documento = request.FILES.get('documento')

    if not documento:
      messages.add_message(request, constants.ERROR, 'Insira um documento válido.')
      return redirect(f'/medicos/cosulta_area_medico/{id_consulta}')

    documento = Documento(
      consulta=consulta,
      titulo=titulo,
      documento=documento,
    )

    documento.save()
    messages.add_message(request, constants.SUCCESS, 'Documento adicionado com sucesso.')
    return redirect(f'/medicos/consulta_area_medico/{id_consulta}')